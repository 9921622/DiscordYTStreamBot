import { useState, useRef } from "react";
import { VolumeIcon } from "./utilities/Icons";

export default function VolumeControl({ volume, onVolumeChange }: { volume : number, onVolumeChange?: (volume: number) => void }) {
    const [localVolume, setLocalVolume] = useState(Math.round(volume * 100));
    const [hovered, setHovered] = useState(false);
    const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

    function handleMouseEnter() {
        if (hideTimer.current) clearTimeout(hideTimer.current);
        setHovered(true);
    }

    function handleMouseLeave() {
        hideTimer.current = setTimeout(() => setHovered(false), 250);
    }

    function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
        setLocalVolume(Number(e.target.value));
    }

    function handleRelease(e: React.MouseEvent<HTMLInputElement>) {
        onVolumeChange?.(Number(e.currentTarget.value) / 100);
    }

    return (
        <div
            className="relative flex items-center justify-center"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}>

            {hovered && (
                <div className="absolute bottom-12 left-1/2 -translate-x-4/5 bg-gray-800 rounded-lg p-3 flex flex-col items-center gap-1 shadow-lg w-36">
                    <span className="text-xs text-gray-400">{localVolume}%</span>
                    <input
                        type="range"
                        min={0}
                        max={100}
                        value={localVolume}
                        onChange={handleChange}
                        onMouseUp={handleRelease}
                        onTouchEnd={(e) => onVolumeChange?.(Number(e.currentTarget.value) / 100)}
                        className="range range-xs range-primary w-full"
                        step="5"
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
