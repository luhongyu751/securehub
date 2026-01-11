import os
from pathlib import Path
from passlib.context import CryptContext
from sqlalchemy import inspect

from app.database import engine
from app.database import Base
from app import models
from app.database import DATABASE_URL

from app.auth import create_access_token


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def init_db():
    # If using a local sqlite file for development/tests, remove stale DB to ensure schema matches models
    if DATABASE_URL.startswith('sqlite:///'):
        # path after sqlite:/// is relative to cwd when running; remove if exists
        db_path = DATABASE_URL.replace('sqlite:///', '')
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except Exception:
            pass
    Base.metadata.create_all(bind=engine)
    # simple seed: create user and sample document record if not exists
    from sqlalchemy.orm import Session
    session = Session(bind=engine)

    user = session.query(models.User).filter(models.User.username == 'alice').first()
    if not user:
        u = models.User(username='alice', hashed_password=pwd_context.hash('password'), is_active=True)
        session.add(u)
        session.commit()
        user = u
        print('Created sample user: alice / password')

    admin = session.query(models.User).filter(models.User.username == 'admin').first()
    if not admin:
        a = models.User(username='admin', hashed_password=pwd_context.hash('adminpass'), is_active=True, is_admin=True)
        session.add(a)
        session.commit()
        print('Created admin user: admin / adminpass')

    # Ensure sample document directory
    sample_dir = Path(os.getenv('SECUREHUB_DOC_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'sample_docs'))))
    sample_dir.mkdir(parents=True, exist_ok=True)
    sample_pdf = sample_dir / 'sample.pdf'
    if not sample_pdf.exists():
        # create an empty placeholder PDF to allow testing; real deployments should upload real PDFs
        sample_pdf.write_bytes(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')

    doc = session.query(models.Document).filter(models.Document.filename == 'sample.pdf').first()
    if not doc:
        d = models.Document(filename='sample.pdf', file_path=str(sample_pdf), watermark_enabled=True, watermark_text='CONFIDENTIAL', font_size=40, opacity='0.3')
        session.add(d)
        session.commit()
        # grant access to alice
        access = models.DocumentAccess(user_id=user.id, document_id=d.id)
        session.add(access)
        session.commit()
        print('Created sample document and granted access to alice')

    # print JWT for alice
    token = create_access_token({'sub': user.username})
    print('\nSample JWT for alice:')
    print(token)


if __name__ == '__main__':
    init_db()
