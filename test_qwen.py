import os
from transformers import AutoProcessor, AutoModelForVision2Seq
import torch

model_dir = os.getenv("MODEL_ID", "/app/model")

print(">>> Checking CUDA...")
print("CUDA available:", torch.cuda.is_available())
print("Devices:", torch.cuda.device_count())

print(">>> Listing model directory:", model_dir)
print(os.listdir(model_dir))

while True:
    input()

print(">>> Loading config...")

from transformers import AutoConfig
config = AutoConfig.from_pretrained(model_dir)
print("model_type:", config.model_type)

print(">>> Loading model...")
processor = AutoProcessor.from_pretrained(model_dir, trust_remote_code=True)

model = AutoModelForVision2Seq.from_pretrained(
    model_dir,
    device_map="auto",
    torch_dtype="auto",
    trust_remote_code=True
)

print(">>> Model loaded successfully!")
print(model)