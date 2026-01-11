from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
import pyotp

from app.database import get_db
from app import models
from app.auth import get_current_user, get_current_admin_user
from app.utils.audit import record_audit
from app.security import hash_password, verify_password

router = APIRouter()


class CreateUserIn(BaseModel):
    username: str
    password: str
    is_admin: bool = False


class OTPIn(BaseModel):
    code: str


def admin_required(user: models.User = Depends(get_current_admin_user)):
    return user


@router.post('/users', status_code=201)
def create_user(payload: CreateUserIn, db: Session = Depends(get_db), _: models.User = Depends(admin_required)):
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail='User exists')
    u = models.User(username=payload.username, hashed_password=hash_password(payload.password), is_active=True, is_admin=payload.is_admin)
    db.add(u)
    db.commit()
    db.refresh(u)
    # audit
    try:
        record_audit(db, _.id if _ else None, 'create_user', object_type='user', object_id=u.id, detail=u.username)
    except Exception:
        pass
    return {'id': u.id, 'username': u.username}


@router.get('/users')
def list_users(q: Optional[str] = Query(None), page: int = 1, size: int = 50, db: Session = Depends(get_db), _: models.User = Depends(admin_required)):
    query = db.query(models.User)
    if q:
        query = query.filter(models.User.username.ilike(f"%{q}%"))
    total = query.count()
    users = query.offset((page - 1) * size).limit(size).all()
    return {'total': total, 'page': page, 'size': size, 'items': [{'id': u.id, 'username': u.username, 'is_active': u.is_active, 'is_admin': u.is_admin} for u in users]}


@router.get('/users/{user_id}')
def get_user(user_id: int, db: Session = Depends(get_db), _: models.User = Depends(admin_required)):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail='User not found')
    return {'id': u.id, 'username': u.username, 'is_active': u.is_active, 'is_admin': u.is_admin}


@router.put('/users/{user_id}/active')
def set_active(user_id: int, body: dict, db: Session = Depends(get_db), _: models.User = Depends(admin_required)):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail='User not found')
    val = body.get('active')
    if val is None:
        raise HTTPException(status_code=400, detail='active required')
    u.is_active = bool(val)
    db.add(u)
    db.commit()
    try:
        record_audit(db, _.id if _ else None, 'set_active', object_type='user', object_id=u.id, detail=str(u.is_active))
    except Exception:
        pass
    return {'ok': True}


@router.put('/users/{user_id}/admin')
def set_admin(user_id: int, body: dict, db: Session = Depends(get_db), _: models.User = Depends(admin_required)):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail='User not found')
    val = body.get('is_admin')
    if val is None:
        raise HTTPException(status_code=400, detail='is_admin required')
    u.is_admin = bool(val)
    db.add(u)
    db.commit()
    try:
        record_audit(db, _.id if _ else None, 'set_admin', object_type='user', object_id=u.id, detail=str(u.is_admin))
    except Exception:
        pass
    return {'ok': True}


@router.delete('/users/{user_id}', status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), _: models.User = Depends(admin_required)):
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail='User not found')
    db.delete(u)
    db.commit()
    try:
        record_audit(db, _.id if _ else None, 'delete_user', object_type='user', object_id=u.id, detail=u.username)
    except Exception:
        pass
    return {}


@router.get('/users/me')
def me(current_user: models.User = Depends(get_current_user)):
    return {'id': current_user.id, 'username': current_user.username, 'is_active': current_user.is_active, 'two_factor_enabled': current_user.two_factor_enabled}


@router.post('/users/me/2fa/start')
def start_2fa(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # generate secret and store it temporarily
    secret = pyotp.random_base32()
    current_user.otp_secret = secret
    db.add(current_user)
    db.commit()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.username, issuer_name='SecureHub')
    return {'otp_secret': secret, 'provisioning_uri': uri}


@router.post('/users/me/2fa/verify')
def verify_2fa(body: OTPIn, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user.otp_secret:
        raise HTTPException(status_code=400, detail='2FA not initiated')
    totp = pyotp.TOTP(current_user.otp_secret)
    if not totp.verify(body.code):
        raise HTTPException(status_code=400, detail='Invalid 2FA code')
    current_user.two_factor_enabled = True
    db.add(current_user)
    db.commit()
    return {'ok': True}


@router.post('/users/me/2fa/disable')
def disable_2fa(body: OTPIn, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user.two_factor_enabled or not current_user.otp_secret:
        raise HTTPException(status_code=400, detail='2FA not enabled')
    totp = pyotp.TOTP(current_user.otp_secret)
    if not totp.verify(body.code):
        raise HTTPException(status_code=400, detail='Invalid 2FA code')
    current_user.two_factor_enabled = False
    current_user.otp_secret = None
    db.add(current_user)
    db.commit()
    return {'ok': True}


@router.post('/groups', status_code=201)
def create_group(payload: dict, db: Session = Depends(get_db), _: models.User = Depends(admin_required)):
    name = payload.get('name')
    if not name:
        raise HTTPException(status_code=400, detail='name required')
    if db.query(models.Group).filter(models.Group.name == name).first():
        raise HTTPException(status_code=400, detail='group exists')
    g = models.Group(name=name, description=payload.get('description'))
    db.add(g)
    db.commit()
    db.refresh(g)
    return {'id': g.id, 'name': g.name}


@router.get('/groups')
def list_groups(db: Session = Depends(get_db), _: models.User = Depends(admin_required)):
    groups = db.query(models.Group).all()
    items = []
    for g in groups:
        items.append({'id': g.id, 'name': g.name, 'description': g.description, 'members': [{'id': u.id, 'username': u.username} for u in g.users]})
    return {'total': len(items), 'items': items}


@router.post('/groups/{group_id}/add_user')
def add_user_to_group(group_id: int, payload: dict, db: Session = Depends(get_db), _: models.User = Depends(admin_required)):
    user_id = payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=400, detail='user_id required')
    g = db.query(models.Group).filter(models.Group.id == group_id).first()
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not g or not u:
        raise HTTPException(status_code=404, detail='Group or user not found')
    if u in g.users:
        return {'ok': True}
    g.users.append(u)
    db.add(g)
    db.commit()
    try:
        record_audit(db, _.id if _ else None, 'add_user_to_group', object_type='group', object_id=g.id, detail=str(u.id))
    except Exception:
        pass
    return {'ok': True}


@router.post('/groups/{group_id}/remove_user')
def remove_user_from_group(group_id: int, payload: dict, db: Session = Depends(get_db), _: models.User = Depends(admin_required)):
    user_id = payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=400, detail='user_id required')
    g = db.query(models.Group).filter(models.Group.id == group_id).first()
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not g or not u:
        raise HTTPException(status_code=404, detail='Group or user not found')
    if u in g.users:
        g.users.remove(u)
        db.add(g)
        db.commit()
        try:
            record_audit(db, _.id if _ else None, 'remove_user_from_group', object_type='group', object_id=g.id, detail=str(u.id))
        except Exception:
            pass
    return {'ok': True}

