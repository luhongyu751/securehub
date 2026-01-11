from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app import models
from app.auth import get_current_user

router = APIRouter()


def admin_required(user: models.User = Depends(get_current_user)):
    if not getattr(user, 'is_admin', False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin required')
    return user


@router.get('/logs')
def list_logs(
    user_id: Optional[int] = Query(None),
    document_id: Optional[int] = Query(None),
    username: Optional[str] = Query(None),
    start_ts: Optional[str] = Query(None),
    end_ts: Optional[str] = Query(None),
    page: int = 1,
    size: int = 50,
    db: Session = Depends(get_db),
    _: models.User = Depends(admin_required),
):
    # join to get username and filename
    query = db.query(models.DownloadLog, models.User.username, models.Document.filename).join(models.User, models.DownloadLog.user_id == models.User.id).join(models.Document, models.DownloadLog.document_id == models.Document.id)
    if user_id:
        query = query.filter(models.DownloadLog.user_id == user_id)
    if document_id:
        query = query.filter(models.DownloadLog.document_id == document_id)
    if username:
        query = query.filter(models.User.username.ilike(f"%{username}%"))
    if start_ts:
        try:
            from datetime import datetime
            st = datetime.fromisoformat(start_ts)
            query = query.filter(models.DownloadLog.timestamp >= st)
        except Exception:
            raise HTTPException(status_code=400, detail='start_ts must be ISO datetime')
    if end_ts:
        try:
            from datetime import datetime
            et = datetime.fromisoformat(end_ts)
            query = query.filter(models.DownloadLog.timestamp <= et)
        except Exception:
            raise HTTPException(status_code=400, detail='end_ts must be ISO datetime')

    total = query.count()
    items = query.order_by(models.DownloadLog.timestamp.desc()).offset((page - 1) * size).limit(size).all()

    results = []
    for log, username_val, filename in items:
        results.append({
            'id': log.id,
            'user_id': log.user_id,
            'username': username_val,
            'document_id': log.document_id,
            'filename': filename,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None,
            'client_ip': log.client_ip,
        })

    return {'total': total, 'page': page, 'size': size, 'items': results}


@router.get('/logs/export')
def export_logs(
    user_id: Optional[int] = Query(None),
    document_id: Optional[int] = Query(None),
    username: Optional[str] = Query(None),
    start_ts: Optional[str] = Query(None),
    end_ts: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: models.User = Depends(admin_required),
):
    # prepare query (reuse filters from list_logs)
    query = db.query(models.DownloadLog, models.User.username, models.Document.filename).join(models.User, models.DownloadLog.user_id == models.User.id).join(models.Document, models.DownloadLog.document_id == models.Document.id)
    if user_id:
        query = query.filter(models.DownloadLog.user_id == user_id)
    if document_id:
        query = query.filter(models.DownloadLog.document_id == document_id)
    if username:
        query = query.filter(models.User.username.ilike(f"%{username}%"))
    if start_ts:
        from datetime import datetime
        try:
            st = datetime.fromisoformat(start_ts)
            query = query.filter(models.DownloadLog.timestamp >= st)
        except Exception:
            raise HTTPException(status_code=400, detail='start_ts must be ISO datetime')
    if end_ts:
        from datetime import datetime
        try:
            et = datetime.fromisoformat(end_ts)
            query = query.filter(models.DownloadLog.timestamp <= et)
        except Exception:
            raise HTTPException(status_code=400, detail='end_ts must be ISO datetime')

    # streaming generator
    def stream():
        import csv
        import io

        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['id', 'timestamp', 'username', 'user_id', 'filename', 'document_id', 'client_ip'])
        yield si.getvalue()
        si.seek(0); si.truncate(0)

        for log, username_val, filename in query.order_by(models.DownloadLog.timestamp.desc()).yield_per(100):
            writer.writerow([log.id, log.timestamp.isoformat() if log.timestamp else '', username_val, log.user_id, filename, log.document_id, log.client_ip or ''])
            yield si.getvalue()
            si.seek(0); si.truncate(0)

    from fastapi.responses import StreamingResponse
    return StreamingResponse(stream(), media_type='text/csv', headers={"Content-Disposition": "attachment; filename=download_logs.csv"})
