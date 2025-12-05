# check_mounts.py
#!/usr/bin/env python3
"""
Скрипт проверки монтирования volumes в Docker контейнере
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

def print_color(text: str, color: str = "white") -> None:
    """Вывод цветного текста"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def check_directory(path: str, description: str, min_files: int = 0) -> Tuple[bool, str, List[str]]:
    """Проверка директории"""
    if not os.path.exists(path):
        return False, f"✗ {description}: {path} (NOT EXISTS)", []
    
    try:
        items = os.listdir(path)
        item_count = len(items)
        
        if min_files > 0 and item_count < min_files:
            return False, f"⚠ {description}: {path} (EXISTS, but has only {item_count} items, expected at least {min_files})", items[:10]
        
        return True, f"✓ {description}: {path} ({item_count} items)", items[:10]
    
    except PermissionError:
        return False, f"✗ {description}: {path} (PERMISSION DENIED)", []
    except Exception as e:
        return False, f"✗ {description}: {path} (ERROR: {str(e)})", []

def check_model_directory(path: str) -> Tuple[bool, str, Dict[str, any]]:
    """Специальная проверка директории модели"""
    if not os.path.exists(path):
        return False, f"✗ Model directory: {path} (NOT EXISTS)", {}
    
    try:
        files = os.listdir(path)
        safetensors = [f for f in files if f.endswith('.safetensors')]
        required_files = [
            'config.json',
            'model.safetensors.index.json',
            'tokenizer.json',
            'tokenizer_config.json'
        ]
        
        missing_required = [f for f in required_files if f not in files]
        
        details = {
            'total_files': len(files),
            'safetensors_files': len(safetensors),
            'missing_required': missing_required,
            'has_config': 'config.json' in files,
            'has_tokenizer': 'tokenizer.json' in files,
            'sample_files': files[:5]
        }
        
        if not safetensors:
            return False, f"✗ Model directory: {path} (NO SAFETENSORS FILES)", details
        
        if missing_required:
            return False, f"⚠ Model directory: {path} (MISSING: {', '.join(missing_required)})", details
        
        return True, f"✓ Model directory: {path} ({len(files)} files, {len(safetensors)} safetensors)", details
    
    except Exception as e:
        return False, f"✗ Model directory: {path} (ERROR: {str(e)})", {}

def check_disk_usage(path: str) -> Tuple[float, float]:
    """Проверка использования диска"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        return used / total * 100, free / (1024**3)  # Процент использования и свободно в GB
    except:
        return 0.0, 0.0

def main() -> None:
    """Основная функция"""
    print_color("\n" + "="*80, "cyan")
    print_color("AGENT RECOGNITION SYSTEM - VOLUME MOUNT CHECK", "cyan")
    print_color("="*80, "cyan")
    
    # Критические пути для проверки
    checks = [
        ("/app/model_weights", "Model Weights Directory", 1),
        ("/app/uploads", "Uploads Directory", 0),
        ("/app/processed", "Processed Results Directory", 0),
        ("/app/temp", "Temp Directory", 0),
        ("/app/logs", "Logs Directory", 0),
        ("/app/database", "Database Directory", 0),
        ("/root/.cache/huggingface", "HuggingFace Cache", 0),
    ]
    
    all_ok = True
    results = {}
    
    print_color("\n1. Checking Docker Volume Mounts:", "yellow")
    print_color("-"*50, "yellow")
    
    for path, description, min_files in checks:
        if path == "/app/model_weights":
            ok, message, details = check_model_directory(path)
            results[description] = {
                "ok": ok,
                "message": message,
                "details": details
            }
        else:
            ok, message, items = check_directory(path, description, min_files)
            results[description] = {
                "ok": ok,
                "message": message,
                "items": items
            }
        
        if not ok:
            all_ok = False
        
        color = "green" if ok else "red" if "✗" in message else "yellow"
        print_color(message, color)
        
        if "details" in results[description] and results[description]["details"]:
            details = results[description]["details"]
            if "safetensors_files" in details:
                print_color(f"    - Safetensors files: {details['safetensors_files']}", "blue")
            if "missing_required" in details and details["missing_required"]:
                print_color(f"    - Missing: {', '.join(details['missing_required'])}", "yellow")
    
    print_color("\n2. Checking Disk Usage:", "yellow")
    print_color("-"*50, "yellow")
    
    # Проверка использования диска для основных путей
    for path, description, _ in checks:
        if os.path.exists(path):
            usage_percent, free_gb = check_disk_usage(path)
            if usage_percent > 0:
                status = "🟢" if usage_percent < 80 else "🟡" if usage_percent < 95 else "🔴"
                print_color(f"{status} {description}: {usage_percent:.1f}% used, {free_gb:.1f} GB free", 
                           "green" if usage_percent < 80 else "yellow" if usage_percent < 95 else "red")
    
    print_color("\n3. System Information:", "yellow")
    print_color("-"*50, "yellow")
    
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown"
            print_color(f"✓ CUDA Available: Yes ({device_count} devices)", "green")
            print_color(f"  Device 0: {device_name}", "blue")
        else:
            print_color("✗ CUDA Available: No", "red")
    except ImportError:
        print_color("⚠ PyTorch not installed", "yellow")
    
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        print_color(f"✓ CPU Usage: {cpu_percent:.1f}%", "blue")
        print_color(f"✓ Memory Usage: {memory.percent:.1f}% ({memory.used/(1024**3):.1f}GB / {memory.total/(1024**3):.1f}GB)", "blue")
    except ImportError:
        print_color("⚠ psutil not installed", "yellow")
    
    print_color("\n4. Python Environment:", "yellow")
    print_color("-"*50, "yellow")
    
    print_color(f"✓ Python Version: {sys.version}", "blue")
    print_color(f"✓ Working Directory: {os.getcwd()}", "blue")
    print_color(f"✓ User: {os.getenv('USER', 'unknown')}", "blue")
    
    # Проверка переменных окружения
    env_vars = [
        "MODEL_PATH",
        "UPLOAD_DIR", 
        "PROCESSED_DIR",
        "TEMP_DIR",
        "LOG_DIR",
        "DB_PATH",
        "CUDA_VISIBLE_DEVICES"
    ]
    
    for var in env_vars:
        value = os.getenv(var, "NOT SET")
        print_color(f"✓ {var}: {value}", "blue")
    
    print_color("\n" + "="*80, "cyan")
    
    if all_ok:
        print_color("✅ ALL CHECKS PASSED - SYSTEM READY", "green")
        sys.exit(0)
    else:
        print_color("❌ SOME CHECKS FAILED - PLEASE REVIEW ERRORS", "red")
        
        # Сохранение отчета
        report_path = "/app/logs/mount_check_report.json"
        try:
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print_color(f"\n📄 Full report saved to: {report_path}", "cyan")
        except Exception as e:
            print_color(f"\n⚠ Could not save report: {e}", "yellow")
        
        sys.exit(1)

if __name__ == "__main__":
    main()