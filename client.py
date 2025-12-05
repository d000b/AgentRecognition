# client.py
import requests
import json

class QwenVLClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
    
    def upload_image(self, image_path):
        """Загрузка изображения на сервер"""
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/upload/image",
                files=files
            )
        return response.json()
    
    def inference(self, text_prompt, image_urls=None):
        """Отправка запроса на inference"""
        data = {
            "text_prompt": text_prompt,
            "image_urls": image_urls or []
        }
        
        response = requests.post(
            f"{self.base_url}/infer",
            json=data
        )
        return response.json()

# Использование
if __name__ == "__main__":
    client = QwenVLClient()
    
    # 1. Загружаем изображение
    upload_result = client.upload_image("path/to/your/image.jpg")
    print(f"Uploaded: {upload_result['image_url']}")
    
    # 2. Делаем запрос
    result = client.inference(
        text_prompt="Опиши это изображение",
        image_urls=[upload_result['image_url']]
    )
    print(f"Result: {result['result']}")