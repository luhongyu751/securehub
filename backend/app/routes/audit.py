from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import datetime
import csv
from io import StringIO

from app.database import get_db
from app import models
from app.auth import get_current_user, get_current_admin_user

router = APIRouter()


def admin_required(user: models.User = Depends(get_current_admin_user)):
    return user


@router.get('/audit')
def list_audit(page: int = 1, size: int = 100, db: Session = Depends(get_db), _: models.User = Depends(admin_required)):
    query = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc())
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    out = []
    for a in items:
        out.append({
            'id': a.id,
            'actor_id': a.actor_id,
            'actor': a.actor.username if a.actor else None,
            'action': a.action,
            'object_type': a.object_type,
            'object_id': a.object_id,
            'detail': a.detail,
            'timestamp': a.timestamp.isoformat(),
        })
    return {'total': total, 'page': page, 'size': size, 'items': out}


@router.get('/audit/export')
def export_audit(db: Session = Depends(get_db), _: models.User = Depends(admin_required)):
    query = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc())
    items = query.all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['id', 'actor_id', 'actor', 'action', 'object_type', 'object_id', 'detail', 'timestamp'])
    for a in items:
        writer.writerow([a.id, a.actor_id, a.actor.username if a.actor else None, a.action, a.object_type, a.object_id, a.detail, a.timestamp.isoformat()])
    content = si.getvalue()
    return Response(content, media_type='text/csv', headers={ 'Content-Disposition': f'attachment; filename="audit_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.csv"' })
