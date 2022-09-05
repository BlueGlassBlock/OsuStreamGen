import logging
from dataclasses import dataclass, field
from typing import Union


@dataclass
class Difficulty:
    path: str
    name: str
    artist: str
    mapper: str
    difficulty: str
    ar: float
    cs: float
    hp: float
    od: float
    hash: str
    api_beatmap_id: int
    beatmap_id: int
    beatmapset_id: int
    timing: list[tuple[float, float, bool]]


@dataclass
class Song:
    difficulties: list[Difficulty] = field(default_factory=list)


class Songs:
    def __init__(self):
        self.songs: list[Song] = []
        self.bid_mapping: dict[int, Difficulty] = {}
        self.log = logging.getLogger(__name__)

    def add_song(self, song: Song):
        if not song.difficulties:
            self.log.warning("An empty song was added!")
        self.songs.append(song)

    def get_song(self, song_hash: str) -> Union[tuple[Song, Difficulty], None]:
        """
        Returns the song with the given hash
        :param song_hash: Hash of the song to get
        :return: Mapset and song difficulty, or None if nothing was found
        """
        for song in self.songs:
            for diff in song.difficulties:
                if diff.hash == song_hash:
                    return song, diff

        return None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Songs: {self.songs}"
