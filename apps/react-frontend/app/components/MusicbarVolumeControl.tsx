import { useState, useRef, useEffect } from "react";
import { VolumeIcon } from "./utilities/Icons";
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";

export default function VolumeControl() {
    const { videoPlaybackStatus, videoVolume } = usePlaybackVideoContext();
    const volume = videoPlaybackStatus?.volume ?? 0.5;

    const [localVolume, setLocalVolume] = useState(Math.round(volume * 100));
    const [hovered, setHovered] = useState(false);
    const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        if (videoPlaybackStatus?.volume != null) {
            setLocalVolume(Math.round(videoPlaybackStatus.volume * 100));
        }
    }, [videoPlaybackStatus?.volume]);

    const handleMouseEnter = () => {
        if (hideTimer.current) clearTimeout(hideTimer.current);
        setHovered(true);
    };

    const handleMouseLeave = () => {
        hideTimer.current = setTimeout(() => setHovered(false), 250);
    };

    const handleRelease = (value: number) => {
        videoVolume(value / 100);
    };

    return (
        <div
            className="relative flex items-center justify-center"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
        >
            {hovered && (
                <div className="absolute bottom-12 left-1/2 -translate-x-4/5 bg-gray-800 rounded-lg p-3 flex flex-col items-center gap-1 shadow-lg w-36">
                    <span className="text-xs text-gray-400">{localVolume}%</span>
                    <input
                        type="range"
                        min={0}
                        max={100}
                        step={5}
                        value={localVolume}
                        onChange={e => setLocalVolume(Number(e.target.value))}
                        onMouseUp={e => handleRelease(Number(e.currentTarget.value))}
                        onTouchEnd={e => handleRelease(Number(e.currentTarget.value))}
                        className="range range-xs range-primary w-full"
                    />
                    <div className="flex justify-between w-full px-1 text-xs text-gray-400">
                        <span>0</span>
                        <span>100</span>
                    </div>
                </div>
            )}

            <button className="btn btn-ghost btn-circle hover:bg-gray-800">
                <VolumeIcon />
            </button>
        </div>
    );
}
