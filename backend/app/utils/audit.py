from datetime import datetime
from app import models


def record_audit(db, actor_id, action, object_type=None, object_id=None, detail=None):
    try:
        a = models.AuditLog(actor_id=actor_id, action=action, object_type=object_type, object_id=str(object_id) if object_id is not None else None, detail=detail)
        db.add(a)
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
