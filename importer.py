import argparse
import logging
from base64 import b64encode
from os import path
from time import sleep

import spotipy
from PIL import Image
from requests.exceptions import ReadTimeout
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth
from yandex_music import Client, Artist

REDIRECT_URI = 'https://open.spotify.com'
MAX_REQUEST_RETRIES = 5

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def encode_file_base64_jpeg(filename):
    img = Image.open(filename)
    if img.format != 'JPEG':
        img.convert('RGB').save(filename, 'JPEG')

    with open(filename, 'rb') as f:
        return b64encode(f.read())


def handle_spotify_exception(func):
    def wrapper(*args, **kwargs):
        retry = 1
        while True:
            try:
                return func(*args, **kwargs)
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

    return wrapper


class NotFoundException(SpotifyException):
    def __init__(self, item_name):
        self.item_name = item_name


class Importer:
    def __init__(self, spotify_client, yandex_client, ignore_list, strict_search):
        self.spotify_client = spotify_client
        self.yandex_client = yandex_client

        self._importing_items = {
            'likes': self.import_likes,
            'playlists': self.import_playlists,
            'albums': self.import_albums,
            'artists': self.import_artists
        }

        for item in ignore_list:
            del self._importing_items[item]

        self._strict_search = strict_search

        self.user = handle_spotify_exception(spotify_client.me)()['id']
        logger.info(f'User ID: {self.user}')

        self.not_imported = {}

    def _import_item(self, item):
        type_ = item.__class__.__name__.casefold()
        item_name = item.name if isinstance(item, Artist) else f'{", ".join([artist.name for artist in item.artists])} '\
                                                               f'- {item.title}'
        query = item_name.replace('- ', '')
        found_items = handle_spotify_exception(self.spotify_client.search)(query, type=type_)[f'{type_}s']['items']
        logger.info(f'Importing {type_}: {item_name}...')

        if not self._strict_search and not isinstance(item, Artist) and not len(found_items) and len(item.artists) > 1:
            query = f'{item.artists[0]} {item.title}'
            found_items = handle_spotify_exception(self.spotify_client.search)(query, type=type_)[f'{type_}s']['items']

        logger.info(f'Searching "{query}"...')

        if not len(found_items):
            raise NotFoundException(item_name)

        return found_items[0]['id']

    def _add_items_to_spotify(self, items, not_imported_section, save_items_callback):
        spotify_items = []

        items.reverse()
        for item in items:
            if item.available:
                try:
                    spotify_items.append(self._import_item(item))
                    logger.info('OK')
                except NotFoundException as exception:
                    not_imported_section.append(exception.item_name)
                    logger.warning('NO')

        for chunk in chunks(spotify_items, 50):
            save_items_callback(self, chunk)

    def import_likes(self):
        self.not_imported['Likes'] = []

        likes_tracks = self.yandex_client.users_likes_tracks().tracks
        tracks = self.yandex_client.tracks([f'{track.id}:{track.album_id}' for track in likes_tracks if track.album_id])
        logger.info('Importing liked tracks...')

        def save_tracks_callback(importer, spotify_tracks):
            logger.info(f'Saving {len(spotify_tracks)} tracks...')
            handle_spotify_exception(importer.spotify_client.current_user_saved_tracks_add)(spotify_tracks)
            logger.info('OK')

        self._add_items_to_spotify(tracks, self.not_imported['Likes'], save_tracks_callback)

    def import_playlists(self):
        playlists = self.yandex_client.users_playlists_list()
        for playlist in playlists:
            spotify_playlist = handle_spotify_exception(self.spotify_client.user_playlist_create)(self.user, playlist.title)
            spotify_playlist_id = spotify_playlist['id']

            logger.info(f'Importing playlist {playlist.title}...')

            if playlist.cover.type == 'pic':
                filename = f'{playlist.kind}-cover'
                playlist.cover.download(filename, size='400x400')

                handle_spotify_exception(self.spotify_client.playlist_upload_cover_image)(spotify_playlist_id, encode_file_base64_jpeg(filename))

            self.not_imported[playlist.title] = []

            playlist_tracks = playlist.fetch_tracks()
            tracks = self.yandex_client.tracks([track.track_id for track in playlist_tracks if track.album_id]) \
                if playlist.collective else [track.track for track in playlist_tracks]

            def save_tracks_callback(importer, spotify_tracks):
                logger.info(f'Saving {len(spotify_tracks)} tracks in playlist {playlist.title}...')
                handle_spotify_exception(importer.spotify_client.user_playlist_add_tracks)(importer.user,
                                                                                           spotify_playlist_id,
                                                                                           spotify_tracks)
                logger.info('OK')

            self._add_items_to_spotify(tracks, self.not_imported[playlist.title], save_tracks_callback)

    def import_albums(self):
        self.not_imported['Albums'] = []

        likes_albums = self.yandex_client.users_likes_albums()
        albums = [album.album for album in likes_albums]
        logger.info('Importing albums...')

        def save_albums_callback(importer, spotify_albums):
            logger.info(f'Saving {len(spotify_albums)} albums...')
            handle_spotify_exception(importer.spotify_client.current_user_saved_albums_add)(spotify_albums)
            logger.info('OK')

        self._add_items_to_spotify(albums, self.not_imported['Albums'], save_albums_callback)

    def import_artists(self):
        self.not_imported['Artists'] = []

        likes_artists = self.yandex_client.users_likes_artists()
        artists = [artist.artist for artist in likes_artists]
        logger.info('Importing artists...')

        def save_artists_callback(importer, spotify_artists):
            logger.info(f'Saving {len(spotify_artists)} artists...')
            handle_spotify_exception(importer.spotify_client.user_follow_artists)(spotify_artists)
            logger.info('OK')

        self._add_items_to_spotify(artists, self.not_imported['Artists'], save_artists_callback)

    def import_all(self):
        for item in self._importing_items.values():
            item()

        self.print_not_imported()

    def print_not_imported(self):
        logger.error('Not imported items:')
        for section, items in self.not_imported.items():
            logger.info(f'{section}:')
            for item in items:
                logger.info(item)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates a playlist for user')
    parser.add_argument('-u', '-s', '--spotify', required=True, help='Username at spotify.com')

    spotify_oauth = parser.add_argument_group('spotify_oauth')
    spotify_oauth.add_argument('--id', required=True, help='Client ID of your Spotify app')
    spotify_oauth.add_argument('--secret', required=True, help='Client Secret of your Spotify app')

    parser.add_argument('-t', '--token', required=True, help='Token from music.yandex.com account')

    parser.add_argument('-i', '--ignore', nargs='+', help='Don\'t import some items',
                        choices=['likes', 'playlists', 'albums', 'artists'], default=[])

    parser.add_argument('-T', '--timeout', help='Request timeout for spotify', type=float, default=10)

    parser.add_argument('-S', '--strict-artists-search', help='Search for an exact match of all artists', default=False)

    arguments = parser.parse_args()

    auth_manager = SpotifyOAuth(
        client_id=arguments.id,
        client_secret=arguments.secret,
        redirect_uri=REDIRECT_URI,
        scope='playlist-modify-public, user-library-modify, user-follow-modify, ugc-image-upload',
        username=arguments.spotify
    )
    spotify_client_ = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=arguments.timeout)

    yandex_client_ = Client(arguments.token)
    yandex_client_.init()
    Importer(spotify_client_, yandex_client_, arguments.ignore, arguments.strict_artists_search).import_all()
