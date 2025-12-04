import fitz
from PIL import Image
from io import BytesIO

def load_into_images(file_bytes, filename):
    ext = filename.lower()

    if ext.endswith(".pdf"):
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
        pages = []
        for page in pdf:
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pages.append(img)
        return pages

    elif ext.endswith((".png", ".jpg", ".jpeg", ".tiff")):
        return [Image.open(BytesIO(file_bytes))]

    else:
        raise ValueError("Unsupported file format.")
