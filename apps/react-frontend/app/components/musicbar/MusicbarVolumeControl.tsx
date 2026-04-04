import { useState, useRef, useEffect } from "react";
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";
import { ScalingVolumeIcon } from "../utilities/Icons";

export default function VolumeControl() {
    const { videoPlaybackStatus, videoVolume } = usePlaybackVideoContext();
    const volume = videoPlaybackStatus?.volume ?? 0.5;

    const [localVolume, setLocalVolume] = useState(Math.round(volume * 100));
    const [hovered, setHovered] = useState(false);
    const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const sliderRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (videoPlaybackStatus?.volume != null) {
            setLocalVolume(Math.round(videoPlaybackStatus.volume * 100));
        }
    }, [videoPlaybackStatus?.volume]);

    useEffect(() => {
        sliderRef.current?.style.setProperty('--vpct', `${localVolume}%`);
    }, [localVolume]);

    const handleMouseEnter = () => {
        if (hideTimer.current) clearTimeout(hideTimer.current);
        setHovered(true);
    };
    const handleMouseLeave = () => {
        hideTimer.current = setTimeout(() => setHovered(false), 200);
    };
    const handleRelease = (value: number) => videoVolume(value / 100);

    return (
        <>
            <style>{`
                .vol-slider {
                    -webkit-appearance: none;
                    appearance: none;
                    width: 100%;
                    height: 3px;
                    background: rgba(255,255,255,0.12);
                    border-radius: 3px;
                    outline: none;
                    cursor: pointer;
                }
                .vol-slider::-webkit-slider-runnable-track {
                    height: 3px;
                    border-radius: 3px;
                    background: linear-gradient(
                        to right,
                        rgba(255,255,255,0.75) var(--vpct, 50%),
                        rgba(255,255,255,0.12) var(--vpct, 50%)
                    );
                }
                .vol-slider::-webkit-slider-thumb {
                    -webkit-appearance: none;
                    width: 11px;
                    height: 11px;
                    border-radius: 50%;
                    background: #fff;
                    cursor: pointer;
                    margin-top: -4px;
                }
                .vol-slider::-moz-range-track {
                    height: 3px;
                    border-radius: 3px;
                    background: rgba(255,255,255,0.12);
                }
                .vol-slider::-moz-range-progress {
                    height: 3px;
                    border-radius: 3px;
                    background: rgba(255,255,255,0.75);
                }
                .vol-slider::-moz-range-thumb {
                    width: 11px;
                    height: 11px;
                    border: none;
                    border-radius: 50%;
                    background: #fff;
                    cursor: pointer;
                }
            `}</style>

            <div
                className="relative flex items-center justify-center"
                onMouseEnter={handleMouseEnter}
                onMouseLeave={handleMouseLeave}
            >
                {hovered && (
                    <div
                        className="absolute bottom-[calc(100%+10px)] right-0 z-50 flex flex-col items-center gap-2 p-3 w-32 rounded-xl"
                        style={{
                            background: 'rgba(22,22,22,0.97)',
                            border: '0.5px solid rgba(255,255,255,0.12)',
                            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                        }}
                    >
                        <span className="text-[11px] text-white/40 tabular-nums">
                            {localVolume}%
                        </span>
                        <input
                            ref={sliderRef}
                            type="range"
                            min={0}
                            max={100}
                            step={5}
                            value={localVolume}
                            onChange={e => setLocalVolume(Number(e.target.value))}
                            onMouseUp={e => handleRelease(Number(e.currentTarget.value))}
                            onTouchEnd={e => handleRelease(Number(e.currentTarget.value))}
                            className="vol-slider"
                            style={{ '--vpct': `${localVolume}%` } as React.CSSProperties}
                        />
                        <div className="flex justify-between w-full px-0.5">
                            <span className="text-[10px] text-white/25">0</span>
                            <span className="text-[10px] text-white/25">100</span>
                        </div>
                    </div>
                )}

                <button
                    className="flex items-center justify-center w-8 h-8 rounded-full text-white/40 hover:text-white hover:bg-white/10 transition-all duration-150 bg-transparent border-none outline-none cursor-pointer"
                    title="Volume"
                >
                    <ScalingVolumeIcon className="w-4 h-4" level={volume} />
                </button>
            </div>
        </>
    );
}
