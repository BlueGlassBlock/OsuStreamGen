import logging
import math
from pathlib import Path

import rich.logging
import rich.traceback
from rich.console import Console

from db.model import Difficulty

FORMAT = "%(message)s"
con = Console()
logging.basicConfig(
    level="ERROR",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[rich.logging.RichHandler(console=con, rich_tracebacks=True)],
)
from db.parser import load_db

if __name__ == "__main__":
    songs = load_db(Path("F:/osu!/osu!.db"))
    con.log(f"你有 {len(songs.songs)} 张谱!")
    while True:
        bid = con.input("请输入数字形式的[bold red] BID[/]> [green]")
        if not bid.isdigit():
            con.print(f"[red]错误: {bid} 不是数字")
            continue
        bid = int(bid)
        if bid not in songs.bid_mapping:
            con.print(f"[red]错误：BID {bid} 不存在于你的本地数据库.")
            continue
        diff: Difficulty = songs.bid_mapping[bid]
        valid_timings: list[tuple[float, float]] = [
            timing[:2] for timing in diff.timing if timing[2]
        ]
        if not valid_timings:
            con.print(f"[red]错误：BID {bid}: {diff.name} 没有有效时间点.")
            continue
        base_bpm = 1 / valid_timings[0][0] * 1000 * 60
        consistent_bpm: bool = any(
            math.isclose(base_bpm, 1 / t[0] * 1000 * 60) for t in valid_timings
        )
        if consistent_bpm:
            con.print(
                f"[magenta]错误：BID [cyan]{bid}[/]: [cyan]{diff.name}[/] 为变 BPM 曲目."
            )
            continue
        con.print(f"[green]选定曲目: [cyan]{diff.name}[/], BPM: [cyan]{base_bpm}[/]")
        osu_file_path: Path = Path(diff.path)
