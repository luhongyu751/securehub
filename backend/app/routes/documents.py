from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import uuid
import shutil

from app.database import get_db
from app import models
from app.auth import get_current_user
from app.utils.audit import record_audit

router = APIRouter()

DOC_DIR = os.getenv('SECUREHUB_DOC_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'documents')))


def ensure_doc_dir():
    os.makedirs(DOC_DIR, exist_ok=True)


def is_admin(user: models.User):
    return getattr(user, 'is_admin', False)


@router.post('/documents/upload')
def upload_document(file: UploadFile = File(...), watermark_enabled: Optional[bool] = True, watermark_text: Optional[str] = None, font_size: Optional[int] = 40, opacity: Optional[float] = 0.3, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin required')

    if file.content_type != 'application/pdf' and not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail='Only PDF uploads allowed')

    ensure_doc_dir()
    # generate safe filename
    ext = os.path.splitext(file.filename)[1] or '.pdf'
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(DOC_DIR, stored_name)

    # save upload to destination
    with open(dest_path, 'wb') as out_f:
        shutil.copyfileobj(file.file, out_f)

    # create DB record
    doc = models.Document(filename=file.filename, file_path=dest_path, watermark_enabled=bool(watermark_enabled), watermark_text=watermark_text, font_size=font_size or 40, opacity=str(opacity or 0.3))
    db.add(doc)
    db.commit()
    db.refresh(doc)
    try:
        record_audit(db, current_user.id if current_user else None, 'upload_document', object_type='document', object_id=doc.id, detail=doc.filename)
    except Exception:
        pass
    return {'id': doc.id, 'filename': doc.filename}


@router.get('/documents')
def list_documents(page: int = 1, size: int = 50, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Document)
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return {'total': total, 'page': page, 'size': size, 'items': [{'id': d.id, 'filename': d.filename, 'watermark_enabled': d.watermark_enabled} for d in items]}


@router.get('/documents/{doc_id}')
def get_document(doc_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    d = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not d:
        raise HTTPException(status_code=404, detail='Document not found')

    # allow if admin or has access
    if not is_admin(current_user):
        access = db.query(models.DocumentAccess).filter(models.DocumentAccess.document_id == doc_id, models.DocumentAccess.user_id == current_user.id).first()
        if not access:
            raise HTTPException(status_code=403, detail='Access denied')

    return {'id': d.id, 'filename': d.filename, 'watermark_enabled': d.watermark_enabled, 'watermark_text': d.watermark_text, 'font_size': d.font_size, 'opacity': d.opacity}


@router.delete('/documents/{doc_id}')
def delete_document(doc_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail='Admin required')
    d = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not d:
        raise HTTPException(status_code=404, detail='Document not found')
    # remove file
    try:
        if os.path.exists(d.file_path):
            os.remove(d.file_path)
    except Exception:
        pass
    # remove DB records
    db.query(models.DocumentAccess).filter(models.DocumentAccess.document_id == doc_id).delete()
    db.delete(d)
    db.commit()
    try:
        record_audit(db, current_user.id if current_user else None, 'delete_document', object_type='document', object_id=doc_id, detail=d.filename)
    except Exception:
        pass
    return {'ok': True}


@router.put('/documents/{doc_id}/metadata')
def set_metadata(doc_id: int, payload: dict, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail='Admin required')
    d = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not d:
        raise HTTPException(status_code=404, detail='Document not found')
    if 'watermark_enabled' in payload:
        d.watermark_enabled = bool(payload.get('watermark_enabled'))
    if 'watermark_text' in payload:
        d.watermark_text = payload.get('watermark_text')
    if 'font_size' in payload:
        d.font_size = int(payload.get('font_size'))
    if 'opacity' in payload:
        d.opacity = str(payload.get('opacity'))
    db.add(d)
    db.commit()
    try:
        record_audit(db, current_user.id if current_user else None, 'set_document_metadata', object_type='document', object_id=d.id, detail=str(payload))
    except Exception:
        pass
    return {'ok': True}


@router.post('/documents/{doc_id}/grant')
def grant_access(doc_id: int, payload: dict, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail='Admin required')
    d = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not d:
        raise HTTPException(status_code=404, detail='Document not found')
    user_id = payload.get('user_id')
    group_id = payload.get('group_id')
    if user_id:
        u = db.query(models.User).filter(models.User.id == user_id).first()
        if not u:
            raise HTTPException(status_code=404, detail='User not found')
        exists = db.query(models.DocumentAccess).filter(models.DocumentAccess.user_id == user_id, models.DocumentAccess.document_id == doc_id).first()
        if not exists:
            access = models.DocumentAccess(user_id=user_id, document_id=doc_id)
            db.add(access)
            db.commit()
            try:
                record_audit(db, current_user.id if current_user else None, 'grant_access_user', object_type='document', object_id=doc_id, detail=str(user_id))
            except Exception:
                pass
    elif group_id:
        g = db.query(models.Group).filter(models.Group.id == group_id).first()
        if not g:
            raise HTTPException(status_code=404, detail='Group not found')
        # grant to all users in group
        for u in g.users:
            exists = db.query(models.DocumentAccess).filter(models.DocumentAccess.user_id == u.id, models.DocumentAccess.document_id == doc_id).first()
            if not exists:
                access = models.DocumentAccess(user_id=u.id, document_id=doc_id)
                db.add(access)
        db.commit()
        try:
            record_audit(db, current_user.id if current_user else None, 'grant_access_group', object_type='document', object_id=doc_id, detail=f'group:{group_id}')
        except Exception:
            pass
    else:
        raise HTTPException(status_code=400, detail='user_id or group_id required')
    return {'ok': True}


@router.post('/documents/{doc_id}/revoke')
def revoke_access(doc_id: int, payload: dict, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail='Admin required')
    user_id = payload.get('user_id')
    group_id = payload.get('group_id')
    if user_id:
        db.query(models.DocumentAccess).filter(models.DocumentAccess.user_id == user_id, models.DocumentAccess.document_id == doc_id).delete()
        db.commit()
        try:
            record_audit(db, current_user.id if current_user else None, 'revoke_access_user', object_type='document', object_id=doc_id, detail=str(user_id))
        except Exception:
            pass
    elif group_id:
        g = db.query(models.Group).filter(models.Group.id == group_id).first()
        if not g:
            raise HTTPException(status_code=404, detail='Group not found')
        for u in g.users:
            db.query(models.DocumentAccess).filter(models.DocumentAccess.user_id == u.id, models.DocumentAccess.document_id == doc_id).delete()
        db.commit()
        try:
            record_audit(db, current_user.id if current_user else None, 'revoke_access_group', object_type='document', object_id=doc_id, detail=f'group:{group_id}')
        except Exception:
            pass
    else:
        raise HTTPException(status_code=400, detail='user_id or group_id required')
    return {'ok': True}
