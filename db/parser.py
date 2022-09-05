import logging
from os import PathLike
from typing import BinaryIO, Literal

from .fmt import read_batch, read_type
from .model import Difficulty, Song, Songs

# osu!.db format
# Data type     Description
# Int           osu! version (e.g. 20150203)
# Int           Folder Count
# Bool          AccountUnlocked (only false when account is locked or banned in any way)
# DateTime      Date the account will be unlocked
# String        Player name
# Int           Number of beatmaps
# Beatmaps*     The beatmaps themselves

# Beatmap Format
# String            Artist name
# String            Artist name, Unicode
# String            Song title
# String            Song title, Unicode
# String            Creator name
# String            Difficulty name
# String            Audio file name
# String            MD5 hash of map
# String            Name of .osu file for map
# Byte              Ranked status (4=ranked, 5=approved, 2=pending/graveyard)
# Short             Number of hitcircles
# Short             Number of sliders
# Short             Number of spinners
# Long              Last modification time in windows ticks
# Byte/Single       Approach rate (Byte if version is less than 20140609, Single otherwise)
# Byte/Single       Circle size (Byte if version is less than 20140609, Single otherwise)
# Byte/Single       HP drain (Byte if version is less than 20140609, Single otherwise)
# Byte/Single       Overall Difficulty (Byte if version is less than 20140609, Single otherwise)
# Double            Slider velocity
# Int-Doublepair*   An int indicating the number of following Int-Double pairs, then the pairs themselves.
#                   Star rating info for osu!standard. The int is the mod combination, the Double is the star rating.
#                   Only present if version greater or equal to 20140609.
# Int-Doublepair*   An int indicating the number of following Int-Double pairs, then the pairs themselves.
#                   Star rating info for Taiko. The int is the mod combination, the Double is the star rating.
#                   Only present if version greater or equal to 20140609.
# Int-Doublepair*   An int indicating the number of following Int-Double pairs, then the pairs themselves.
#                   Star rating info for CTB. The int is the mod combination, the Double is the star rating.
#                   Only present if version greater or equal to 20140609.
# Int-Doublepair*   An int indicating the number of following Int-Double pairs, then the pairs themselves.
#                   Star rating info for osu!mania. The int is the mod combination, the Double is the star rating.
#                   Only present if version greater or equal to 20140609.
# Int               Drain time in seconds
# Int               Total time in milliseconds
# Int               Time when audio preview starts in ms
# Timingpoint+      An int indicating the number of Timingpoints, then the timingpoints.
# Int               Beatmap ID
# Int               Beatmap set ID
# Int               Thread ID
# Byte              Grade achieved in osu!Standard
# Byte              Grade achieved in Taiko
# Byte              Grade achieved in CTB
# Byte              Grade achieved in osu!Mania
# Short             Local beatmap offset
# Single            Stack leniency
# Byte              Osu gameplay mode. 0x00=standard, 0x01=Taiko, 0x02=CTB, 0x03=Mania
# String            Song source
# String            Song tags
# Short             Online offset
# String            Font used for the title of the song
# Boolean           Is the beatmap unplayed
# Long              Last time played
# Boolean           Is beatmap osz2
# String            Folder name of beatmap, relative to Songs folder
# Long              Last time when map was checked with osu! repo
# Boolean           Ignore beatmap sounds
# Boolean           Ignore beatmap skin
# Boolean           Disable storyboard
# Boolean           Disable video
# Boolean           Visual override
# Short?            Unknown. Only present when version less than 20140609
# Int               Unknown. Some last modification time or something
# Byte              Mania scroll speed


def parse_beatmap(f: BinaryIO) -> Difficulty:
    log = logging.getLogger(__name__)

    # If the database is of a newer version than 20150422, we need to read an int here
    # _ = read_type("Int", f)

    # First, the trivial data of the beatmap
    artist: str = read_type("String", f)
    artist_u: str = read_type("String", f)
    song: str = read_type("String", f)
    song_u: str = read_type("String", f)
    creator: str = read_type("String", f)
    difficulty: str = read_type("String", f)
    audio_file: str = read_type("String", f)
    md5: str = read_type("String", f)
    osu_file: str = read_type("String", f)
    ranked_status: bytes = read_type("Byte", f)
    last_modified: int = read_type("Long", f)
    num_hitcircles: int = read_type("Short", f)
    num_sliders: int = read_type("Short", f)
    num_spinners: int = read_type("Short", f)

    log.log(
        5,
        "artist:{}, artist_u:{}, song:{}, song_u:{}, creator:{}, difficulty:{}, audio_file:{}, "
        "md5:{}, osu_file:{}, ranked_status:{}, num_hitcircles:{}, num_sliders:{}, num_spinners:{}, "
        "last_modified:{}".format(
            artist,
            artist_u,
            song,
            song_u,
            creator,
            difficulty,
            audio_file,
            md5,
            osu_file,
            ranked_status,
            num_hitcircles,
            num_sliders,
            num_spinners,
            last_modified,
        ),
    )

    # Then, the ar, cs, hp and od. If the version is less than 20140609, we need to read 4 bytes, else, 4 singles.

    bm_diff_types: list[Literal["Single"]] = ["Single"] * 4

    ar, cs, hp, od = [read_type(type, f) for type in bm_diff_types]

    # Then, the slider velocity
    slider_velocity: float = read_type("Double", f)

    log.log(
        5,
        "ar:{}, cs:{}, hp:{}, od:{}, slider_velocity:{}".format(
            ar, cs, hp, od, slider_velocity
        ),
    )

    # Then the star ratings. These are an int, followed by that many Int-Double pairs.
    def read_SR() -> list[tuple[int, float]]:
        num_idp = read_type("Int", f)
        idps = [read_type("IntDoublepair", f) for _ in range(num_idp)]
        return idps

    stars_standard, stars_taiko, stars_ctb, stars_mania = [read_SR() for _ in range(4)]

    log.log(
        5,
        "stars_standard:{}, stars_taiko:{}, stars_ctb:{}, stars_mania:{}".format(
            stars_standard, stars_taiko, stars_ctb, stars_mania
        ),
    )

    # Then, the drain time, total time and preview times
    drain_time = read_type("Int", f)
    total_time = read_type("Int", f)
    preview_time = read_type("Int", f)

    log.log(
        5,
        "draintime:{}, totaltime:{}, previewtime:{}".format(
            drain_time, total_time, preview_time
        ),
    )

    # Then, the timing points. These are an int followed by that many Timingpoints.
    num_timingpoints = read_type("Int", f)
    log.debug("There are {} timingpoints.".format(num_timingpoints))
    timingpoints: list[tuple[float, float, bool]] = [
        read_type("Timingpoint", f) for _ in range(num_timingpoints)
    ]

    log.log(5, "timing_points: {}".format(timingpoints))

    # Then some more trivial data
    beatmap_id, beatmap_set_id, thread_id = read_batch(3, "Int", f)
    (
        grade_standard,
        grade_taiko,
        grade_ctb,
        grade_mania,
    ) = read_batch(4, "Byte", f)
    local_offset = read_type("Short", f)
    stack_leniency = read_type("Single", f)
    gameplay_mode = read_type("Byte", f)
    source = read_type("String", f)
    tags = read_type("String", f)
    online_offset = read_type("Short", f)
    font = read_type("String", f)
    unplayed = read_type("Boolean", f)
    last_played = read_type("Long", f)
    is_osz2 = read_type("Boolean", f)
    beatmap_folder = read_type("String", f)
    last_checked = read_type("Long", f)
    (
        ignore_sounds,
        ignore_skin,
        disable_storyboard,
        disable_video,
        visual_override,
    ) = read_batch(5, "Boolean", f)

    log.log(
        5,
        "beatmap_id:{}, beatmap_set_id:{}, thread_id:{}, grade_standard:{}, grade_taiko:{}, grade_ctb:{}, "
        "grade_mania:{}, local_offset:{}, stack_leniency:{}, gameplay_mode:{}, source:{}, tags:{}, "
        "online_offset:{}, font:{}, unplayed:{}, last_played:{}, is_osz2:{}, beatmap_folder:{}, "
        "last_checked:{}, ignore_sounds:{}, ignore_skin:{}, disable_storyboard:{}, disable_video:{}, "
        "visual_override:{}".format(
            beatmap_id,
            beatmap_set_id,
            thread_id,
            grade_standard,
            grade_taiko,
            grade_ctb,
            grade_mania,
            local_offset,
            stack_leniency,
            gameplay_mode,
            source,
            tags,
            online_offset,
            font,
            unplayed,
            last_played,
            is_osz2,
            beatmap_folder,
            last_checked,
            ignore_sounds,
            ignore_skin,
            disable_storyboard,
            disable_video,
            visual_override,
        ),
    )

    # Then a short which is only there if the version is less than 20140609

    # Then, lastly, some last modification time and the mania scroll speed
    unknown_int_modified: int = read_type("Int", f)
    mania_scroll_speed: bytes = read_type("Byte", f)

    log.log(
        5,
        "unknown_int_modified:{}, mania_scroll_speed:{}".format(
            unknown_int_modified, mania_scroll_speed
        ),
    )

    beatmap = Difficulty(
        osu_file,
        song,
        artist,
        creator,
        difficulty,
        ar,
        cs,
        hp,
        od,
        md5,
        beatmap_id,
        beatmap_id,
        beatmap_set_id,
        timingpoints,
    )

    log.debug(
        "Loaded {}: {} - {} [{}] by {}".format(
            beatmap.beatmap_id,
            beatmap.artist,
            beatmap.name,
            beatmap.difficulty,
            beatmap.mapper,
        )
    )

    return beatmap


def load_db(path: PathLike) -> Songs:
    log = logging.getLogger(__name__)
    log.debug(f"Opening file {path}")
    fobj: BinaryIO = open(path, "rb")

    songs = Songs()

    # Try to parse the file as an osu db.
    # First we have some primitive simple types we can just read in one bunch
    version = read_type("Int", fobj)
    num_folders = read_type("Int", fobj)
    unlocked = read_type("Boolean", fobj)
    unlock_time = read_type("DateTime", fobj)
    player_name = read_type("String", fobj)
    num_maps = read_type("Int", fobj)

    log.debug(f"osu!DB version {version}. {num_maps} maps")
    log.log(
        5,
        f"num_folders: {num_folders}, unlocked: {unlocked}, unlock_time: {unlock_time}, player_name: {player_name}",
    )

    # Then, for each beatmap, we need to read the beatmap
    beatmaps: list[Difficulty] = [parse_beatmap(fobj) for _ in range(num_maps)]

    # Now, group the beatmaps by their mapset id, to group them into Songs for the songs list.
    mapsets: dict[int, list[Difficulty]] = {}
    for map in beatmaps:
        songs.bid_mapping[map.beatmap_id] = map
        mapsets.setdefault(map.beatmapset_id, []).append(map)

    # Create Songs from the mapsets.
    for mapset in mapsets.values():
        s = Song()
        s.difficulties = mapset
        songs.add_song(s)

    return songs
