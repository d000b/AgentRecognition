# Эндпоинт для загрузки изображений
@app.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """Загрузка изображения на сервер"""
    try:
        # Генерация уникального имени файла
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{file_ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # Сохранение файла на быстрый NVMe
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Генерируем URL для доступа к файлу
        image_url = f"/files/{filename}"
        
        return {
            "success": True,
            "image_url": image_url,
            "filename": filename,
            "session_id": session_id or str(uuid.uuid4())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Эндпоинт для обработки текста и изображений
@app.post("/infer")
async def inference(request: InferenceRequest):
    """Основной эндпоинт для inference"""
    import time
    from PIL import Image
    import requests
    
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        if model is None or processor is None:
            init_model()
        
        # Подготовка сообщений
        messages = [{
            "role": "user",
            "content": []
        }]
        
        # Добавляем изображения если есть
        if request.image_urls:
            for img_url in request.image_urls:
                # Загружаем изображение
                if img_url.startswith(('http://', 'https://')):
                    response = requests.get(img_url, stream=True)
                    image = Image.open(response.raw)
                elif img_url.startswith('/files/'):
                    filepath = os.path.join(UPLOAD_DIR, img_url.split('/')[-1])
                    image = Image.open(filepath)
                else:
                    # Прямая загрузка base64 или путь
                    image = Image.open(img_url)
                
                messages[0]["content"].append({
                    "type": "image",
                    "image": image
                })
        
        # Добавляем текстовый промпт
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
        
        # Перенос на GPU если нужно
        if hasattr(model, 'device'):
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        # Генерация ответа
        generated_ids = model.generate(**inputs, max_new_tokens=512)
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
        
        # Логирование запроса (опционально на RAID)
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "processing_time": processing_time,
            "prompt": request.text_prompt,
            "response": output_text
        }
        
        log_path = os.path.join(PROCESSED_DIR, f"{request_id}.json")
        with open(log_path, 'w') as f:
            json.dump(log_entry, f, ensure_ascii=False, indent=2)
        
        return InferenceResponse(
            result=output_text,
            request_id=request_id,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Эндпоинт для потоковой загрузки файлов
@app.get("/files/{filename}")
async def get_file(filename: str):
    """Получение загруженных файлов"""
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath)