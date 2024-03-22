from PIL import Image
import requests

@pyscript_executor
def getSize(src):
    try:
        if src.startswith("http"):
            im = Image.open(requests.get(src, stream=True).raw)
        else:
            im = Image.open(in_image)
    except Exception:
        return None

    return im.size