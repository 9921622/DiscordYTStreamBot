
import { PlayIcon, PauseIcon, PrevIcon, NextIcon, VolumeIcon, LoopIcon, ShuffleIcon } from "./utilities/Icons";

interface SongControlsProps {
    isPlaying: boolean;
    isPaused: boolean;
    onPause: () => void;
    onPrev?: () => void;
    onNext?: () => void;
    onShuffle?: () => void;
    onLoop?: () => void;
}
export default function SongControls({ isPlaying, isPaused, onPause, onPrev, onNext, onShuffle, onLoop }: SongControlsProps) {
    return (
        <div className="flex items-center gap-4">
            <button className="btn btn-ghost btn-circle hover:bg-gray-800" onClick={onShuffle}>
                <ShuffleIcon />
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800" onClick={onPrev}>
                <PrevIcon />
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800" onClick={onPause}>
                {isPlaying && !isPaused ? <PauseIcon /> : <PlayIcon />}
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800" onClick={onNext}>
                <NextIcon />
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800" onClick={onLoop}>
                <LoopIcon />
            </button>
        </div>
    );
}
