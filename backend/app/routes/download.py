from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import shutil

from app.database import get_db
from app import models
from app.auth import get_current_user


def _resolve_run_add_watermark():
    # dynamic import with fallbacks to support different PYTHONPATH/test contexts
    try:
        from deploy.watermark_wrapper import run_add_watermark as _fn
        return _fn
    except Exception:
        pass
    try:
        from backend.deploy.watermark_wrapper import run_add_watermark as _fn
        return _fn
    except Exception:
        pass
    try:
        # last resort: relative import when package context allows
        from ..deploy.watermark_wrapper import run_add_watermark as _fn
        return _fn
    except Exception:
        raise ImportError('Could not import watermark wrapper')

router = APIRouter()


def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


@router.get('/documents/{doc_id}/download')
def download_document(doc_id: int, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 查找文档
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Document not found')

    # 权限校验：检查 DocumentAccess
    access = db.query(models.DocumentAccess).filter(models.DocumentAccess.document_id == doc_id, models.DocumentAccess.user_id == current_user.id).first()
    if not access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

    original_path = doc.file_path
    if not os.path.exists(original_path):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Source file missing')

    # 记录下载日志（先写入，成功/失败都记录）
    log = models.DownloadLog(user_id=current_user.id, document_id=doc.id, client_ip=request.client.host if request.client else None)
    db.add(log)
    db.commit()

    # 如果需要水印，调用 wrapper 生成临时文件
    if doc.watermark_enabled:
        watermark_text = doc.watermark_text or f"{current_user.username}"  # 简单示例
        try:
            run_fn = _resolve_run_add_watermark()
            tmp_path = run_fn(original_path, watermark_text, doc.font_size or 40, float(doc.opacity or 0.3))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Watermark failed: {str(e)}')

        background_tasks.add_task(remove_file, tmp_path)
        return FileResponse(path=tmp_path, filename=doc.filename, media_type='application/pdf')
    else:
        # 直接返回原始文件，但注意该路径应对 nginx 隐藏，不可被外部直接访问
        return FileResponse(path=original_path, filename=doc.filename, media_type='application/pdf')
