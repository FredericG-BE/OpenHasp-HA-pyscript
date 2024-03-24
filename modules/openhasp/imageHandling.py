from PIL import Image
import requests
import hashlib
import struct
import logging


@pyscript_executor
def getSize(src):
    try:
        if src.startswith("http"):
            im = Image.open(requests.get(src, stream=True).raw)
        else:
            im = Image.open(src)
    except Exception:
        return None

    return im.size

@pyscript_executor
def prepareImage(src, size, fitscreen=False):
    
    _LOGGER = logging.getLogger("custom_components.pyscript.openhasp-pyscript")

    imageID = hashlib.md5(src.encode("utf-8")).hexdigest()

    if src.startswith("http"):
        im = Image.open(requests.get(src, stream=True).raw)
    else:
        im = Image.open(src)

    original_width, original_height = im.size
    width, height = size

    if not fitscreen:
        width = min(w for w in [width, original_width] if w is not None and w > 0)
        height = min(h for h in [height, original_height] if h is not None and h > 0)
        im.thumbnail((height, width), Image.LANCZOS)
    else:
        im = im.resize((height, width), Image.LANCZOS)
    width, height = im.size  # actual size after resize

    localFilename = f"/config/www/openhasp-pyscript/temp/{imageID}"
    publicFileName = f"http://192.168.0.4:8123/local/openhasp-pyscript/temp/{imageID}"
    with open(localFilename, "wb") as out_image:
        out_image.write(struct.pack("I", height << 21 | width << 10 | 4))    
        img = im.convert("RGB")
        for pix in img.getdata():
            r = (pix[0] >> 3) & 0x1F
            g = (pix[1] >> 2) & 0x3F
            b = (pix[2] >> 3) & 0x1F
            out_image.write(struct.pack("H", (r << 11) | (g << 5) | b))
    
        _LOGGER.debug(
            "image_to_rgb565 out_image: %s - %s > %s",
            out_image.name,
            (original_width, original_height),
            im.size,
        )
    
        out_image.flush()

    return publicFileName