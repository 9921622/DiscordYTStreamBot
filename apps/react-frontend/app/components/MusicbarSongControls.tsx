
import { PlayIcon, PauseIcon, PrevIcon, NextIcon, VolumeIcon, LoopIcon, ShuffleIcon } from "./utilities/Icons";

interface SongControlsProps {
    className? : string;
    isPlaying: boolean;
    isPaused: boolean;
    isLoop: boolean;
    onPause: () => void;
    onPrev?: () => void;
    onNext?: () => void;
    onShuffle?: () => void;
    onLoop?: () => void;
}
export default function SongControls({ className, isPlaying, isPaused, isLoop, onPause, onPrev, onNext, onShuffle, onLoop }: SongControlsProps) {
    return (
        <div className={`${className} flex items-center gap-4`}>
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
