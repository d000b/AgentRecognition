# main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os
from datetime import datetime
from typing import Optional, List
import uuid
import json

# Модели данных
class InferenceRequest(BaseModel):
    text_prompt: str
    image_urls: Optional[List[str]] = None
    session_id: Optional[str] = None

class InferenceResponse(BaseModel):
    result: str
    request_id: str
    processing_time: float

# Инициализация
app = FastAPI(title="Qwen3-VL API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Папки для хранения
UPLOAD_DIR = "/mnt/nvme/uploads"  # Используем ваше NVMe
PROCESSED_DIR = "/mnt/raid/processed"  # Зеркальный RAID
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Инициализация модели (можно вынести в отдельный сервис)
model = None
processor = None

def init_model():
    """Инициализация модели с поддержкой GPU"""
    global model, processor
    try:
        from transformers import Qwen3VLMoeForConditionalGeneration, AutoProcessor
        import torch
        
        print("Loading Qwen3-VL model...")
        model = Qwen3VLMoeForConditionalGeneration.from_pretrained(
            "Qwen/Qwen3-VL-30B-A3B-Instruct",
            torch_dtype=torch.bfloat16,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        
        processor = AutoProcessor.from_pretrained("Qwen/Qwen3-VL-30B-A3B-Instruct")
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")