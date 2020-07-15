import spotipy
import configparser

from yandex_music import Client
from spotipy.oauth2 import SpotifyOAuth

config = configparser.RawConfigParser()
config.read('config.ini')
CLIENT_ID = config.get('SPOTIFY', 'CLIENT_ID')
CLIENT_SECRET = config.get('SPOTIFY', 'CLIENT_SECRET')
REDIRECT_URI = config.get('SPOTIFY', 'REDIRECT_URI')
USERNAME = config.get('SPOTIFY', 'USERNAME')
TOKEN = config.get('YANDEX', 'TOKEN')

yandex_client = Client.from_token(TOKEN)

auth_manager = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope='playlist-modify-public', username=USERNAME)
spotify_client = spotipy.Spotify(auth_manager=auth_manager)
yandex_playlists = yandex_client.users_playlists_list()
user = spotify_client.me()['id']


def main():
    print(f'User: {user}')
    for yandex_playlist in [yandex_playlists[2]]:
        playlist_title = yandex_playlist.title
        spotify_playlist = spotify_client.user_playlist_create(user, playlist_title)
        spotify_playlist_id = spotify_playlist['id']
        print(f'Import playlist {playlist_title}')
        yandex_tracks = yandex_playlist.fetch_tracks()
        spotify_tracks = []
        for yandex_track in yandex_tracks:
            track_available = yandex_track['track']['available']
            if track_available:
                track_artist = yandex_track['track']['artists'][0]['name']
                track_title = yandex_track['track']['title']
                print(f'Finding track: {track_artist} - {track_title}...', end='')
                found_tracks = spotify_client.search(f'{track_artist} - {track_title}',
                                                     type='track')['tracks']['items']
                filter_tracks = [track for track in found_tracks if track['name'].lower().startswith(track_title.lower())]
                if len(filter_tracks) > 0:
                    spotify_tracks.append(filter_tracks[0]['id'])
                    print('\tOK')
                else:
                    print('\tNO')
                if len(spotify_tracks) == 100:
                    print(f'Adding {len(spotify_tracks)} in playlist {playlist_title}...', end='')
                    spotify_client.user_playlist_add_tracks(user, spotify_playlist_id, spotify_tracks)
                    spotify_tracks.clear()
                    print('\tOK')
        if len(spotify_tracks) > 0:
            print(f'Adding {len(spotify_tracks)} in playlist {playlist_title}...', end='')
            spotify_client.user_playlist_add_tracks(user, spotify_playlist_id, spotify_tracks)
            print('\tOK')


if __name__ == '__main__':
    main()