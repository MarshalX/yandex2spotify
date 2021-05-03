# yandex2spotify
Simple Python script, that allow to import favorite tracks, playlists, albums and artists from Yandex.Music to Spotify

## Install requirments
```bash
pip3 install -r requirements.txt
```

## Usage
1) Using credentials:
```bash
python3 yandex2spotify.py -u <spotify_username> -l <yandex_login> -p <yandex_password>
```
2) Using token:
```bash
python3 yandex2spotify.py -u <spotify_username> -t <yandex_token>
```

3) If you don't want to import some items (likes, playlists, albums, artists) you can exclude them by specifying ignore argument, for example:
```bash
python3 yandex2spotify.py -u <spotify_username> -t <yandex_token> -i playlists albums artists
```
