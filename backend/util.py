def model_generate(model, processor, images, prompt):
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ] + [
                {"type": "image", "image": img} for img in images
            ]
        }
    ]

    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    output = model.generate(
        **inputs,
        max_new_tokens=4096,
        temperature=0,
        do_sample=False
    )

    # Cut input ids
    generated = output[:, inputs['input_ids'].shape[1]:]

    text = processor.batch_decode(
        generated,
        skip_special_tokens=True
    )[0]

    return text
