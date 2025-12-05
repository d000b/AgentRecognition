# main.py
import os
import sys
import time
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import torch
from PIL import Image
import requests
from io import BytesIO

# Наши модули
from config import config
from database import SessionLocal, InferenceRequestDB, FileStorage

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(config.LOG_DIR, 'app', 'app.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI(
    title="Agent Recognition API",
    description="API для работы с моделью Qwen3-VL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    model_loaded: bool
    gpu_available: bool
    paths: Dict[str, Any]

class UploadResponse(BaseModel):
    success: bool
    file_id: str
    filename: str
    file_url: str
    file_type: str
    size_bytes: int

class InferenceRequest(BaseModel):
    text_prompt: str
    file_ids: Optional[List[str]] = []
    image_urls: Optional[List[str]] = []
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    session_id: Optional[str] = None

class InferenceResponse(BaseModel):
    success: bool
    result: str
    request_id: str
    processing_time: float
    tokens_generated: Optional[int] = None

# Глобальные переменные модели
model = None
processor = None
model_loaded = False

# Зависимости
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Вспомогательные функции
def load_model():
    """Загрузка модели из локальной директории"""
    global model, processor, model_loaded
    
    try:
        from transformers import Qwen3VLMoeForConditionalGeneration, AutoProcessor
        
        logger.info(f"Loading model from: {config.MODEL_PATH}")
        
        # Проверка доступности файлов модели
        if not os.path.exists(config.MODEL_PATH):
            raise FileNotFoundError(f"Model directory not found: {config.MODEL_PATH}")
        
        # Проверка наличия safetensors файлов
        safetensors_files = [f for f in os.listdir(config.MODEL_PATH) if f.endswith('.safetensors')]
        if not safetensors_files:
            raise FileNotFoundError(f"No safetensors files found in {config.MODEL_PATH}")
        
        logger.info(f"Found {len(safetensors_files)} model files")
        
        # Загрузка модели
        model = Qwen3VLMoeForConditionalGeneration.from_pretrained(
            config.MODEL_PATH,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )
        
        processor = AutoProcessor.from_pretrained(
            config.MODEL_PATH,
            trust_remote_code=True
        )
        
        model_loaded = True
        logger.info("Model loaded successfully!")
        logger.info(f"Model device: {model.device}")
        logger.info(f"Model dtype: {model.dtype}")
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise

def process_image(image_input):
    """Обработка изображения из разных источников"""
    try:
        if isinstance(image_input, str):
            if image_input.startswith(('http://', 'https://')):
                # Загрузка по URL
                response = requests.get(image_input, timeout=10)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content))
            elif os.path.exists(image_input):
                # Загрузка из файла
                image = Image.open(image_input)
            else:
                # Попытка decode base64
                import base64
                from io import BytesIO
                image_data = base64.b64decode(image_input)
                image = Image.open(BytesIO(image_data))
        elif isinstance(image_input, bytes):
            # Прямые байты
            image = Image.open(BytesIO(image_input))
        elif isinstance(image_input, Image.Image):
            # Уже PIL Image
            image = image_input
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")
        
        # Конвертация в RGB если нужно
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        return image
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise

# Эндпоинты
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("Starting Agent Recognition API...")
    
    # Инициализация директорий
    config.init_directories()
    
    # Валидация конфигурации
    if not config.validate_config():
        logger.error("Configuration validation failed!")
        sys.exit(1)
    
    # Загрузка модели
    try:
        load_model()
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        logger.warning("API будет работать без модели")

@app.get("/", tags=["Root"])
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Agent Recognition API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Проверка здоровья системы"""
    gpu_available = torch.cuda.is_available() if torch.cuda.is_available() else False
    
    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        timestamp=datetime.now().isoformat(),
        model_loaded=model_loaded,
        gpu_available=gpu_available,
        paths=config.get_paths_info()
    )

@app.post("/upload", response_model=UploadResponse, tags=["Files"])
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """Загрузка файла на сервер"""
    try:
        # Проверка расширения файла
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in config.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(config.ALLOWED_EXTENSIONS)}"
            )
        
        # Генерация уникального имени файла
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        
        # Определение типа файла
        if file_ext in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}:
            file_type = "image"
            save_dir = os.path.join(config.UPLOAD_DIR, "images")
        elif file_ext in {".mp4", ".avi", ".mov"}:
            file_type = "video"
            save_dir = os.path.join(config.UPLOAD_DIR, "videos")
        else:
            file_type = "document"
            save_dir = os.path.join(config.UPLOAD_DIR, "documents")
        
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
        
        # Сохранение файла
        file_size = 0
        with open(filepath, "wb") as buffer:
            while chunk := await file.read(8192):
                file_size += len(chunk)
                buffer.write(chunk)
        
        # Проверка размера файла
        max_size_bytes = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            os.remove(filepath)
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {config.MAX_UPLOAD_SIZE_MB}MB"
            )
        
        # Сохранение в БД
        db = SessionLocal()
        try:
            db_file = FileStorage(
                file_hash=file_id,
                original_filename=file.filename,
                storage_path=filepath,
                file_type=file_type,
                size_bytes=file_size
            )
            db.add(db_file)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving file to database: {e}")
        finally:
            db.close()
        
        logger.info(f"File uploaded: {filename} ({file_size} bytes)")
        
        return UploadResponse(
            success=True,
            file_id=file_id,
            filename=filename,
            file_url=f"/files/{file_type}/{filename}",
            file_type=file_type,
            size_bytes=file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/infer", response_model=InferenceResponse, tags=["Inference"])
async def inference(
    request: InferenceRequest,
    background_tasks: BackgroundTasks
):
    """Основной эндпоинт для inference"""
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        # Подготовка сообщений
        messages = [{
            "role": "user",
            "content": []
        }]
        
        # Обработка загруженных файлов
        images = []
        if request.file_ids:
            db = SessionLocal()
            try:
                for file_id in request.file_ids:
                    db_file = db.query(FileStorage).filter(FileStorage.file_hash == file_id).first()
                    if db_file and db_file.file_type == "image":
                        image = process_image(db_file.storage_path)
                        images.append(image)
            finally:
                db.close()
        
        # Обработка URL изображений
        if request.image_urls:
            for url in request.image_urls:
                try:
                    image = process_image(url)
                    images.append(image)
                except Exception as e:
                    logger.warning(f"Failed to load image from URL {url}: {e}")
        
        # Добавление изображений в сообщение
        for image in images:
            messages[0]["content"].append({
                "type": "image",
                "image": image
            })
        
        # Добавление текстового промпта
        messages[0]["content"].append({
            "type": "text",
            "text": request.text_prompt
        })
        
        # Подготовка входных данных
        inputs = processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        )
        
        # Перенос на GPU
        device = model.device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Генерация ответа
        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=min(request.max_tokens, config.MODEL_MAX_TOKENS),
                temperature=request.temperature,
                do_sample=True,
                top_p=config.MODEL_TOP_P,
                pad_token_id=processor.tokenizer.pad_token_id,
                eos_token_id=processor.tokenizer.eos_token_id
            )
        
        # Декодирование результата
        generated_ids_trimmed = [
            out_ids[len(in_ids):] 
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        
        output_text = processor.batch_decode(
            generated_ids_trimmed, 
            skip_special_tokens=True, 
            clean_up_tokenization_spaces=False
        )[0]
        
        processing_time = time.time() - start_time
        tokens_generated = len(generated_ids_trimmed[0])
        
        # Логирование запроса в фоне
        background_tasks.add_task(
            log_inference_request,
            request_id=request_id,
            request_data=request.dict(),
            result=output_text,
            processing_time=processing_time,
            tokens_generated=tokens_generated
        )
        
        return InferenceResponse(
            success=True,
            result=output_text,
            request_id=request_id,
            processing_time=processing_time,
            tokens_generated=tokens_generated
        )
        
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{file_type}/{filename}", tags=["Files"])
async def get_file(file_type: str, filename: str):
    """Получение загруженного файла"""
    valid_types = ["images", "videos", "documents"]
    if file_type not in valid_types:
        raise HTTPException(status_code=404, detail="Invalid file type")
    
    filepath = os.path.join(config.UPLOAD_DIR, file_type, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/octet-stream"
    )

@app.get("/requests/{request_id}", tags=["Requests"])
async def get_request_status(request_id: str, db: SessionLocal = Depends(get_db)):
    """Получение статуса запроса"""
    request = db.query(InferenceRequestDB).filter(InferenceRequestDB.request_id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return {
        "request_id": request.request_id,
        "status": request.status,
        "created_at": request.created_at.isoformat() if request.created_at else None,
        "completed_at": request.completed_at.isoformat() if request.completed_at else None,
        "processing_time": request.processing_time,
        "result": request.result
    }

# Фоновые задачи
async def log_inference_request(
    request_id: str,
    request_data: Dict[str, Any],
    result: str,
    processing_time: float,
    tokens_generated: int
):
    """Логирование запроса в базу данных"""
    db = SessionLocal()
    try:
        db_request = InferenceRequestDB(
            request_id=request_id,
            session_id=request_data.get("session_id"),
            text_prompt=request_data.get("text_prompt", ""),
            image_paths=request_data.get("file_ids", []) + request_data.get("image_urls", []),
            status="completed",
            result=result,
            processing_time=processing_time,
            completed_at=datetime.utcnow()
        )
        db.add(db_request)
        db.commit()
        logger.info(f"Request logged: {request_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error logging request: {e}")
    finally:
        db.close()

# Монтирование статических файлов
os.makedirs("web", exist_ok=True)
app.mount("/web", StaticFiles(directory="web"), name="web")

# Запуск приложения
if __name__ == "__main__":
    logger.info("Starting uvicorn server...")
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        workers=config.API_WORKERS,
        reload=config.DEBUG,
        log_config=None
    )
