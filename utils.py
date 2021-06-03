from exceptions import NotFoundException
from spotipy.exceptions import SpotifyException
from requests.exceptions import ReadTimeout


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def proc_captcha(captcha):
    response = requests.get(captcha, allow_redirects=True)
    open('captcha.gif', 'wb').write(response.content)
    Image.open('captcha.gif').show()
    return input(f'Input number from "captcha.gif" ({path.abspath("captcha.gif")}):')


def encode_file_base64_jpeg(filename):
    img = Image.open(filename)
    if img.format != 'JPEG':
        img.convert('RGB').save(filename, 'JPEG')

    with open(filename, 'rb') as f:
        return b64encode(f.read())


def spotify_except(func):
    def func_wrapper(*args, **kwargs):
        retry = 1
        while True:
            try:
                return func(*args, **kwargs)
                break
            except NotFoundException  as exception:
                args[0].not_imported[exception.section_name].append(exception.item_name)
                logger.warning('NO')
                break
            except SpotifyException as exception:
                if exception.http_status != 429:
                    raise exception

                if 'retry-after' in exception.headers:
                    sleep(int(exception.headers['retry-after']) + 1)
            except ReadTimeout as exception:
                logger.info(f'Read timed out. Retrying #{retry}...')

                if retry > MAX_REQUEST_RETRIES:
                    logger.info('Max retries reached.')
                    raise exception

                logger.info('Trying again...')
                retry += 1

    return func_wrapper
