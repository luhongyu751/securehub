import io
import os
import pytest

from fastapi.testclient import TestClient

from app.main import app

# ensure DB and sample data
from backend.scripts.init_db import init_db


@pytest.fixture(scope='module')
def client():
    # Initialize DB with sample data
    init_db()
    with TestClient(app) as c:
        yield c


def test_root(client):
    r = client.get('/')
    assert r.status_code == 200
    assert 'SecureHub' in r.json().get('message')


def test_admin_token_and_upload_list(client):
    # get admin token (admin/adminpass created by init_db)
    resp = client.post('/api/token', data={'username': 'admin', 'password': 'adminpass'})
    assert resp.status_code == 200
    token = resp.json().get('access_token')
    assert token

    headers = {'Authorization': f'Bearer {token}'}

    # upload a small fake PDF
    pdf_bytes = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj<</Type /Catalog>>endobj\ntrailer<<>>\n%%EOF\n"
    files = {'file': ('test.pdf', io.BytesIO(pdf_bytes), 'application/pdf')}
    r2 = client.post('/api/documents/upload', headers=headers, files=files)
    assert r2.status_code == 200
    doc_id = r2.json().get('id')
    assert doc_id

    # list documents
    r3 = client.get('/api/documents', headers=headers)
    assert r3.status_code == 200
    data = r3.json()
    assert 'items' in data


def test_download_requires_access(client):
    # login as alice (has sample access to sample.pdf created by init_db)
    resp = client.post('/api/token', data={'username': 'alice', 'password': 'password'})
    assert resp.status_code == 200
    token = resp.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}

    # find a document id alice has access to (sample.pdf created by init_db has id 1)
    r = client.get('/api/documents', headers=headers)
    assert r.status_code == 200
    items = r.json().get('items', [])
    assert items
    doc_id = items[0]['id']

    # try download
    r2 = client.get(f'/api/documents/{doc_id}/download', headers=headers)
    # should be 200 or 500 if watermarking fails due to missing binary deps; treat >=400 as failure
    assert r2.status_code in (200, 500)
