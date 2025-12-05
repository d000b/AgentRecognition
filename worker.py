# worker.py
import os
import sys
import time
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from celery import Celery, Task
from celery.utils.log import get_task_logger

from config import config
from database import SessionLocal, InferenceRequestDB

# Настройка логирования
logger = get_task_logger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Инициализация Celery
celery_app = Celery(
    'agent_recognition',
    broker=config.REDIS_URL,
    backend=config.REDIS_URL
)

# Настройки Celery
celery_app.conf.update(
    task