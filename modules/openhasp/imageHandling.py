from PIL import Image
import requests
import time
import struct
import logging
import os

from homeassistant.helpers.network import get_url


@pyscript_executor
def getSize(src):
    try:
        if src.startswith("http"):
            im = Image.open(requests.get(src, stream=True).raw)
        else:
            im = Image.open(src)
    except Exception:
        return None

    return im.canvasSize

@pyscript_executor
def prepareImage(src, canvasSize, namePrefix="", resize=False):
    
    _LOGGER = logging.getLogger("custom_components.pyscript.openhasp-pyscript")

    imageID = f"{namePrefix}-{str(time.time()).replace(".","_")}"

    if src.startswith("http"):
        im = Image.open(requests.get(src, stream=True).raw)
    else:
        im = Image.open(src)

    original_width, original_height = im.size
    width, height = canvasSize

    if not resize:
        width = min(w for w in [width, original_width] if w is not None and w > 0)
        height = min(h for h in [height, original_height] if h is not None and h > 0)
        im.thumbnail((width, height), Image.LANCZOS)
    else:
        im = im.resize((width, height), Image.LANCZOS)
    width, height = im.size  # actual canvasSize after resize

    localFileDir = "/config/www/openhasp-pyscript/temp"
    try:
        os.makedirs(localFileDir)
    except FileExistsError:
        pass

    localFilename = f"{localFileDir}/{imageID}"
    publicFileName = f"{get_url(hass, allow_external=False)}/local/openhasp-pyscript/temp/{imageID}"
    with open(localFilename, "wb") as out_image:
        out_image.write(struct.pack("I", height << 21 | width << 10 | 4))    
        img = im.convert("RGB")
        for pix in img.getdata():
            r = (pix[0] >> 3) & 0x1F
            g = (pix[1] >> 2) & 0x3F
            b = (pix[2] >> 3) & 0x1F
            out_image.write(struct.pack("H", (r << 11) | (g << 5) | b))
    
        out_image.flush()

    return localFilename, publicFileName, im.size

@pyscript_executor
def deleteFile(src):
    try:
        os.remove(src)
    except Exception as e:
        return False, e
    else:
        return True, None