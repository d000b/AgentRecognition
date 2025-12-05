import os
from fastapi import FastAPI, UploadFile, HTTPException, Form
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from transformers import AutoProcessor, Qwen3VLMoeForConditionalGeneration
from datetime import datetime
import pathlib

from models import Base, Document
from pipelines import load_into_images
from util import model_generate

STORAGE_PATH = os.getenv("STORAGE_PATH", "/data")
MODEL_ID = os.getenv("MODEL_ID")

# DB
engine = create_engine("sqlite:///db.sqlite3")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Load model
processor = AutoProcessor.from_pretrained(MODEL_ID)
model = Qwen3VLMoeForConditionalGeneration.from_pretrained(
    MODEL_ID, device_map="auto", dtype="auto"
)

app = FastAPI()

# -------------------------------
# Upload Document (CREATE)
# -------------------------------
@app.post("/documents")
async def upload_document(file: UploadFile):
    session = Session()

    contents = await file.read()
    filepath = f"{STORAGE_PATH}/raw/{file.filename}"
    with open(filepath, "wb") as f:
        f.write(contents)

    doc = Document(filename=file.filename)
    session.add(doc)
    session.commit()

    return {"id": doc.id, "filename": file.filename}

# -------------------------------
# Get Document (READ)
# -------------------------------
@app.get("/documents/{doc_id}")
async def get_document(doc_id: int):
    session = Session()
    doc = session.get(Document, doc_id)

    if not doc:
        raise HTTPException(status_code=404)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "status": doc.status,
        "result_json": doc.result_json
    }

# -------------------------------
# Run OCR (UPDATE)
# -------------------------------
@app.post("/documents/{doc_id}/process")
async def process_document(doc_id: int, prompt: str = Form("Extract OCR as JSON")):
    session = Session()
    doc = session.get(Document, doc_id)

    if not doc:
        raise HTTPException(status_code=404)

    doc.status = "processing"
    session.commit()

    file_path = f"{STORAGE_PATH}/raw/{doc.filename}"
    bytes_data = open(file_path, "rb").read()

    images = load_into_images(bytes_data, doc.filename)

    # MODEL CALL
    result = model_generate(model, processor, images, prompt)

    doc.status = "done"
    doc.result_json = result
    doc.updated_at = datetime.utcnow()
    session.commit()

    return {"id": doc_id, "status": "done"}

# -------------------------------
# Delete (DELETE)
# -------------------------------
@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: int):
    session = Session()
    doc = session.get(Document, doc_id)

    if not doc:
        raise HTTPException(status_code=404)

    # Remove file
    os.remove(f"{STORAGE_PATH}/raw/{doc.filename}")

    session.delete(doc)
    session.commit()

    return {"deleted": True}
