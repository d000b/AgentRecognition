FROM pytorch/pytorch:2.7.1-cuda11.8-cudnn9-runtime

# 3. Install PyTorch with CUDA 12.4 support
# Option A: Install from PyPI with CUDA 12.4 (if available)
# RUN pip install --no-cache-dir \
#   torch==2.7.1+cu118 \
#    torchvision==0.22.1 \
#    torchaudio==2.5.0 \
#    --index-url https://download.pytorch.org/whl/cu118

# Option C: For RTX 5060 Ti, you might need nightly build
# RUN pip install --no-cache-dir \
#     --pre torch torchvision torchaudio \
#     --index-url https://download.pytorch.org/whl/nightly/cu124

ENTRYPOINT [ "pip3 freeze" ]
