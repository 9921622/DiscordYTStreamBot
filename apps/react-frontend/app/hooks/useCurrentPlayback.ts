import { usePlaybackStatusContext } from "~/contexts/PlaybackStatusContext"
import { usePlaylistContext } from "~/contexts/PlaylistContext"

/*
    for displaying playback state (player UI, now playing bar, sync checks)
*/

export function useCurrentPlayback() {
    const { playlist, currentVideoLoading } = usePlaylistContext()
    const { playing, paused, position, duration, volume, loop, video_id } = usePlaybackStatusContext()

    const currentItem = playlist?.current_item ?? null

    // Bot confirms it's actually on this video
    const botConfirmed = !!video_id && video_id === currentItem?.video?.youtube_id

    const statusReceived = video_id !== undefined
    const waitingForStatus = !!currentItem && video_id === undefined

    return {
        currentItem,
        currentVideo: currentItem?.video ?? null,
        currentAddedBy: currentItem?.added_by ?? null,
        isLoading: currentVideoLoading || (!!currentItem && !statusReceived),
        isPlaying: (playing || paused) && botConfirmed,
        isPaused: paused && botConfirmed,
        isBotOutOfSync: !!currentItem && !botConfirmed && !currentVideoLoading && statusReceived,
        position,
        duration,
        volume,
        loop,
    }
}
