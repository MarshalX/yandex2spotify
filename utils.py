import requests
from base64 import b64encode
from os import path
from PIL import Image


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def proc_captcha(captcha):
    response = requests.get(captcha, allow_redirects=True)
    open('captcha.gif', 'wb').write(response.content)
    Image.open('captcha.gif').show()
    return input(f'Input number from "captcha.gif" ({path.abspath("captcha.gif")}): ')


def encode_file_base64_jpeg(filename):
    img = Image.open(filename)
    if img.format != 'JPEG':
        img.convert('RGB').save(filename, 'JPEG')

    with open(filename, 'rb') as f:
        return b64encode(f.read())
