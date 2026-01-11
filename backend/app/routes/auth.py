import os
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import pyotp

from app.database import get_db
from app import models
from app.auth import create_access_token, create_refresh_token, REFRESH_TOKEN_EXPIRE_DAYS
from jose import JWTError, jwt
from app.auth import SECRET_KEY, ALGORITHM
from app.security import verify_password, hash_password

router = APIRouter()


@router.post('/token')
def login_for_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db), response: Response = None):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect username or password')

    raw_password = form_data.password
    # If 2FA enabled, expect format 'password:otp' from client
    if user.two_factor_enabled:
        if ':' not in raw_password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='2FA required')
        pwd, otp = raw_password.split(':', 1)
        if not verify_password(pwd, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect username or password')
        totp = pyotp.TOTP(user.otp_secret)
        if not totp.verify(otp):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid 2FA code')
    else:
        if not verify_password(raw_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect username or password')

    access_token = create_access_token({'sub': user.username})
    refresh_token, jti, expiry = create_refresh_token({'sub': user.username})

    # persist refresh token record
    try:
        rt = models.RefreshToken(jti=jti, user_id=user.id, expires_at=expiry)
        db.add(rt)
        db.commit()
    except Exception:
        db.rollback()

    # Set refresh token as HttpOnly cookie
    secure_cookie = bool(int(os.getenv('SECUREHUB_SECURE_COOKIE', '0')))
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=secure_cookie,
        samesite='lax',
        path='/',
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    return {'access_token': access_token, 'token_type': 'bearer'}


@router.post('/2fa/setup')
def setup_2fa(db: Session = Depends(get_db), current_user: models.User = Depends(lambda: None)):
    # This endpoint is intended to be called by an authenticated user; for brevity we won't wire current_user here.
    raise HTTPException(status_code=501, detail='Use admin/user endpoints for 2FA setup')



@router.post('/token/refresh')
def refresh_token(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get('refresh_token')
    if not token:
        raise HTTPException(status_code=400, detail='refresh_token cookie required')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get('type') != 'refresh':
            raise JWTError('Not a refresh token')
        username = payload.get('sub')
        if username is None:
            raise JWTError('Invalid token payload')
        jti = payload.get('jti')
        if not jti:
            raise JWTError('Missing jti')
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid refresh token')

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail='Invalid user')

    # verify refresh token record exists and not revoked
    rt = db.query(models.RefreshToken).filter(models.RefreshToken.jti == jti, models.RefreshToken.user_id == user.id).first()
    if not rt or rt.revoked:
        raise HTTPException(status_code=401, detail='Refresh token revoked')
    # optional: check expiry
    if rt.expires_at and rt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail='Refresh token expired')

    new_access = create_access_token({'sub': user.username})
    return {'access_token': new_access, 'token_type': 'bearer'}



@router.post('/logout')
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get('refresh_token')
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get('jti')
            if jti:
                rt = db.query(models.RefreshToken).filter(models.RefreshToken.jti == jti).first()
                if rt:
                    rt.revoked = True
                    db.add(rt)
                    db.commit()
        except Exception:
            db.rollback()
    # clear cookie
    response.delete_cookie('refresh_token', path='/')
    return {'msg': 'logged out'}
