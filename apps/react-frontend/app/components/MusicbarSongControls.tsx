
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";
import { PlayIcon, PauseIcon, PrevIcon, NextIcon, VolumeIcon, LoopIcon, ShuffleIcon } from "./utilities/Icons";
import { usePlaybackQueueContext } from "~/contexts/PlaybackQueueContext";
import { useSocketContext } from "~/contexts/SocketContext";


export default function SongControls({ className }: { className : string }) {
    const { send } = useSocketContext();
    const { videoPlaybackStatus, videoPause } = usePlaybackVideoContext()
    const { queue, queueNext } = usePlaybackQueueContext()

    const isPlaying = videoPlaybackStatus?.playing ?? false;
    const isPaused  = videoPlaybackStatus?.paused ?? false;
    const isLoop    = videoPlaybackStatus?.loop   ?? false;
    const hasQueue  = (queue?.length || 0) > 0;

    const handleLoop = () => {
        send({ type: "loop" })
    }

    const onShuffle = () => {}
    const onPrev = () => {}

    return (
        <div className={`${className} flex items-center gap-4`}>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800" onClick={onShuffle}>
                <ShuffleIcon />
            </button>
            <button className="pointer-events-none opacity-40 btn btn-ghost btn-circle hover:bg-gray-800" onClick={onPrev}>
                <PrevIcon />
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800" onClick={videoPause}>
                {isPlaying && !isPaused ? <PauseIcon /> : <PlayIcon />}
            </button>

            <button
                className={`${!hasQueue ? "pointer-events-none opacity-40" : "hover:bg-gray-800"} btn btn-ghost btn-circle hover:bg-gray-800 group relative`}
                onClick={hasQueue ? queueNext : undefined}
                >

                <div className={!hasQueue ? "opacity-40 group-hover:opacity-0 transition-opacity" : ""}>
                    <NextIcon />
                </div>

            </button>

            <button className="btn btn-ghost btn-circle hover:bg-gray-800" onClick={handleLoop}>
                <div className="relative">
                    <LoopIcon />
                    {!isLoop && (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-full h-0.5 bg-current rotate-45" />
                        </div>
                    )}
                </div>
            </button>
        </div>
    );
}
