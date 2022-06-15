# yandex2spotify

A simple Python script that allows to import favorite tracks, playlists, albums, and artists from Yandex.Music to Spotify

## Installation

```bash
pip3 install -r requirements.txt
```

## Usage

0) Register a dummy Spotify OAuth application at <https://developer.spotify.com/dashboard> and copy its client id and secret. Make sure to add `https://open.spotify.com` as the callback URL.

1) Obtain a Yandex.Music OAuth token.[^1]

2) Run the script:
```bash
python3 importer.py --id <spotify_client_id> --secret <spotify_client_secret> -u <spotify_username> -t <yandex_token>
```

3) If you don't want to import some items (likes, playlists, albums, artists) you can exclude them by specifying the `--ignore` argument, for example:
```bash
python3 importer.py --id <spotify_client_id> --secret <spotify_client_secret> -u <spotify_username> -t <yandex_token> -i playlists albums artists
```

[^1]: Since it's impossible to register an OAuth application with Yandex.Music access scope, you have to [reuse the token from music.yandex.ru itself](https://github.com/MarshalX/yandex-music-api/discussions/513).
