# yandex2spotify

A simple Python script that allows to import favorite tracks, playlists, albums, and artists from Yandex.Music to Spotify

## Installation

```bash
pip3 install -r requirements.txt
```

## Usage

0) [Register a dummy Spotify OAuth application](https://developer.spotify.com/dashboard) and **add `https://open.spotify.com` as a callback URI** in its settings.

1) Obtain a Yandex.Music OAuth token.[^1]

2) Run the script using Client ID and Client Secret copied from your app's Spotify dashboard:
```bash
python3 importer.py --id <spotify_client_id> --secret <spotify_client_secret> -u <spotify_username> -t <yandex_token>
```

3) If you don't want to import some items (likes, playlists, albums, artists) you can exclude them by specifying the `-i/--ignore` argument, for example:
```bash
python3 importer.py --id <spotify_client_id> --secret <spotify_client_secret> -u <spotify_username> -t <yandex_token> -i playlists albums artists
```

4) After launch, script will open the web browser with authorization dialog. After finishing authorization, you need to copy resulting URL, close browser tab and paste that URL after `Enter the URL you were redirected to:`

5) If authorization succeed - you will see log of import process.

[^1]: Since it's impossible to register an OAuth application with Yandex.Music access scope, you have to [reuse the token from music.yandex.ru itself](https://github.com/MarshalX/yandex-music-api/discussions/513).
