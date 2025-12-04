import os
from transformers import AutoProcessor, Qwen3VLMoeForConditionalGeneration

MODEL_ID = os.getenv('MODEL_ID', 'Qwen/Qwen3-VL-30B-A3B-Instruct')

# Lazy load global singletons
_processor = None
_model = None

def get_processor_and_model():
    global _processor, _model
    if _processor is None:
        _processor = AutoProcessor.from_pretrained(MODEL_ID)
    if _model is None:
        _model = Qwen3VLMoeForConditionalGeneration.from_pretrained(MODEL_ID, device_map='auto', dtype='auto')
    return _processor, _model


def model_generate(images, prompt):
    processor, model = get_processor_and_model()

    messages = [
        {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': prompt}
            ] + [{'type': 'image', 'image': img} for img in images]
        }
    ]

    inputs = processor.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors='pt')
    inputs = inputs.to(model.device)

    generated = model.generate(**inputs, max_new_tokens=4096, temperature=0, do_sample=False)
    generated_trimmed = generated[:, inputs['input_ids'].shape[1]:]

    decoded = processor.batch_decode(generated_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

    return decoded