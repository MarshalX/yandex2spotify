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
                            scope='playlist-modify-public, user-library-modify', username=USERNAME)
spotify_client = spotipy.Spotify(auth_manager=auth_manager)
yandex_playlists = yandex_client.users_playlists_list()
user = spotify_client.me()['id']


def main():
    print(f'User: {user}')
    likes_tracks = yandex_client.users_likes_tracks().tracks
    spotify_tracks = []
    unimport_tracks = {}
    unimport_tracks['Likes'] = []
    yandex_tracks = yandex_client.tracks([f'{track.id}:{track.album_id}' for track in likes_tracks])
    print('{:<50}'.format('Importing liked tracks...'))
    for yandex_track in yandex_tracks:
        track_available = yandex_track['available']
        if track_available:
            track_artist = ', '.join([artist['name'] for artist in yandex_track['artists']])
            track_title = yandex_track['title']
            print('{:<48}'.format(f'Importing track: {track_artist} - {track_title}...'), end='')
            found_tracks = spotify_client.search(f'{track_artist} - {track_title}',
                                                 type='track')['tracks']['items']
            if len(found_tracks) > 0:
                spotify_tracks.append(found_tracks[0]['id'])
                print('OK')
            else:
                unimport_tracks['Likes'].append(f'{track_artist} - {track_title}')
                print('NO')
            if len(spotify_tracks) == 50:
                print('{:<48}'.format(f'Saving {len(spotify_tracks)} tracks...'), end='')
                spotify_client.current_user_saved_tracks_add(spotify_tracks)
                spotify_tracks.clear()
                print('OK')
    if len(spotify_tracks) > 0:
        print('{:<48}'.format(f'Saving {len(spotify_tracks)} tracks...'), end='')
        spotify_client.current_user_saved_tracks_add(spotify_tracks)
        print('OK')
    for yandex_playlist in yandex_playlists:
        playlist_title = yandex_playlist.title
        spotify_playlist = spotify_client.user_playlist_create(user, playlist_title)
        spotify_playlist_id = spotify_playlist['id']
        unimport_tracks[playlist_title] = []
        print('{:<50}'.format(f'Importing playlist {playlist_title}...'))
        yandex_tracks = yandex_playlist.fetch_tracks()
        spotify_tracks = []
        for yandex_track in yandex_tracks:
            track_available = yandex_track['track']['available']
            if track_available:
                track_artist = ', '.join([artist['name'] for artist in yandex_track['track']['artists']])
                track_title = yandex_track['track']['title']
                print('{:<48}'.format(f'Importing track: {track_artist} - {track_title}...'), end='')
                found_tracks = spotify_client.search(f'{track_artist} - {track_title}',
                                                     type='track')['tracks']['items']
                if len(found_tracks) > 0:
                    spotify_tracks.append(found_tracks[0]['id'])
                    print('OK')
                else:
                    unimport_tracks[playlist_title].append(f'{track_artist} - {track_title}')
                    print('NO')
                if len(spotify_tracks) == 50:
                    print('{:<50}'.format(f'Adding {len(spotify_tracks)} tracks in playlist {playlist_title}...'),
                          end='')
                    spotify_client.user_playlist_add_tracks(user, spotify_playlist_id, spotify_tracks)
                    spotify_tracks.clear()
                    print('OK')
        if len(spotify_tracks) > 0:
            print('{:<48}'.format(f'Saving {len(spotify_tracks)} tracks in playlist {playlist_title}...'), end='')
            spotify_client.user_playlist_add_tracks(user, spotify_playlist_id, spotify_tracks)
            print('OK')
        print('{:<50}'.format('Error importing tracks:'))
        for playlist in unimport_tracks.keys():
            print(f'{playlist}:')
            for track in unimport_tracks[playlist]:
                print('{:<50}'.format(f'{track}'))


if __name__ == '__main__':
    main()