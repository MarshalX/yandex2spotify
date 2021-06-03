from spotipy.exceptions import SpotifyException


class NotFoundException(SpotifyException):
    def __init__(self, section_name, item_name):
        self.section_name = section_name
        self.item_name = item_name
