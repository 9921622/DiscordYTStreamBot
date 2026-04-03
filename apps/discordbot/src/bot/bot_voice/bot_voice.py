from .audio_mixin import AudioMixin
from .connection_mixin import ConnectionMixin
from .playback_handler import PlaybackHandler
from .voice_control_mixin import VoiceControlMixin
from .voice_events_mixin import VoiceEventsMixin


class DiscordBotVoice(
    VoiceControlMixin,
    AudioMixin,
    ConnectionMixin,
    VoiceEventsMixin,
    PlaybackHandler,
):
    """
    Composition root. Inherits all voice functionality from focused mixins.
    MRO (left to right): VoiceControlMixin → AudioMixin → ConnectionMixin
                       → VoiceEventsMixin → PlaybackHandler
    """
