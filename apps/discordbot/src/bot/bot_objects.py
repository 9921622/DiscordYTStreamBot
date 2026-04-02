import time
from dataclasses import dataclass, field
from pydantic import BaseModel, RootModel


@dataclass
class Playback:
    """stores guild specific playback state for a voice channel session"""

    video_id: str
    source_url: str
    started_at: float
    offset: float = 0.0
    paused_at: float | None = None
    volume: float = 0.5
    ended: bool = False
    manually_stopped: bool = False
    loop: bool = False

    def get_position(self) -> float:
        if self.paused_at is not None:
            return self.offset
        return self.offset + (time.monotonic() - self.started_at)


class PlaybackStatus(BaseModel):
    """serializable snapshot of a guilds current playback state"""

    playing: bool
    paused: bool
    position: float
    volume: float
    video_id: str | None
    ended: bool
    loop: bool


class Member(BaseModel):
    """ """

    discord_id: str
    username: str
    global_name: str
    avatar: str


class MemberList(RootModel[list[Member]]):
    pass
