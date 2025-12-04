import os
from fastapi import FastAPI, UploadFile, Form, HTTPException, Depends
from fastapi.responses import PlainTextResponse, FileResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from redis import Redis
from rq import Queue
from models import Base, Document
from pipelines import load_into_images
from prometheus_metrics import metrics_response, OCR_JOBS_CREATED
from datetime import datetime
import shutil

STORAGE_PATH = os.getenv('STORAGE_PATH', '/data')
engine = create_engine('sqlite:///db.sqlite3')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

app = FastAPI()

# Redis queue
redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
redis_conn = Redis.from_url(redis_url)
q = Queue('ocr', connection=redis_conn)

# Simple RBAC token-based for demo (replace with proper auth in prod)
def get_current_role(token: str = None):
    # token can be passed as header or query - simplified
    # Map tokens -> roles in env: ADMIN_TOKEN, USER_TOKEN
    admin = os.getenv('ADMIN_TOKEN', 'admintoken')
    user = os.getenv('USER_TOKEN', 'usertoken')
    if token == admin:
        return 'admin'
    if token == user:
        return 'user'
    return 'anonymous'

@app.post('/documents')
async def upload_document(file: UploadFile, token: str = None):
    role = get_current_role(token)
    if role == 'anonymous':
        raise HTTPException(status_code=401, detail='Unauthorized')

    session = Session()
    contents = await file.read()
    raw_dir = os.path.join(STORAGE_PATH, 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    filepath = os.path.join(raw_dir, file.filename)
    with open(filepath, 'wb') as f:
        f.write(contents)

    doc = Document(filename=file.filename, status='uploaded')
    session.add(doc)
    session.commit()

    OCR_JOBS_CREATED.inc()
    return {'id': doc.id, 'filename': doc.filename}

@app.post('/documents/{doc_id}/enqueue')
async def enqueue_processing(doc_id: int, prompt: str = Form('Extract OCR JSON'), token: str = None):
    role = get_current_role(token)
    if role == 'anonymous':
        raise HTTPException(status_code=401, detail='Unauthorized')

    session = Session()
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404)

    raw_path = os.path.join(STORAGE_PATH, 'raw', doc.filename)
    job = q.enqueue('worker.process_document_task', doc_id, raw_path, prompt)

    doc.status = 'queued'
    session.commit()

    return {'job_id': job.get_id(), 'status': 'queued'}

@app.get('/metrics')
async def metrics():
    data = metrics_response()
    return PlainTextResponse(data, media_type='text/plain; version=0.0.4; charset=utf-8')

@app.get('/documents/{doc_id}')
async def get_document(doc_id: int, token: str = None):
    role = get_current_role(token)
    if role == 'anonymous':
        raise HTTPException(status_code=401, detail='Unauthorized')

    session = Session()
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404)

    return {'id': doc.id, 'filename': doc.filename, 'status': doc.status}

@app.get('/result/{doc_id}')
async def download_result(doc_id: int, token: str = None):
    role = get_current_role(token)
    if role == 'anonymous':
        raise HTTPException(status_code=401, detail='Unauthorized')

    session = Session()
    doc = session.get(Document, doc_id)
    if not doc or not doc.result_json:
        raise HTTPException(status_code=404)

    # write temporary file and return
    out_path = os.path.join(STORAGE_PATH, 'ocr', f'{doc.id}.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(doc.result_json)

    return FileResponse(out_path, media_type='application/json', filename=f'{doc.id}.json')
