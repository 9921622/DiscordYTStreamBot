import { useEffect, useRef, useState } from "react";
import { NumToTime } from "../utilities/misc";
import { usePlaybackStatusContext } from "~/contexts/PlaybackStatusContext";
import { useSocketContext } from "~/contexts/SocketContext";
import { useUserContext } from "~/contexts/UserContext";
import { useBotContext } from "~/contexts/BotContext";
import { usePlaylistContext } from "~/contexts/PlaylistContext";

export default function SongProgressBar({ className }: { className?: string }) {
    const { discordUser  }= useUserContext()
    const { send } = useSocketContext();
    const { botInChannel } = useBotContext();
    const { currentVideo } = usePlaylistContext()
    const { playing, paused, position, duration } = usePlaybackStatusContext()

    const isPlaying = playing;
    const isPaused  = paused;

    const startTimeRef = useRef<number>(0);
    const startPositionRef = useRef<number>(0);
    const [currentTime, setCurrentTime] = useState(position ?? 0);
    const [sliderValue, setSliderValue] = useState(0);
    const [dragging, setDragging]       = useState(false);
    const sliderRef = useRef<HTMLInputElement>(null);

    const displayTime = dragging ? (sliderValue / 100) * duration : Math.min(duration, currentTime);

    // sync on server push
    useEffect(() => {
        if (position !== undefined) {
            setCurrentTime(position);
            startTimeRef.current = Date.now();
            startPositionRef.current = position;
        }
    }, [position]);

    // local tick
    useEffect(() => {
        if (!isPlaying || isPaused || dragging) return;
        startTimeRef.current = Date.now();
        startPositionRef.current = currentTime;

        const timer = setInterval(() => {
            const elapsed = (Date.now() - startTimeRef.current) / 1000;
            setCurrentTime(Math.min(duration, startPositionRef.current + elapsed));
        }, 1000);

        return () => clearInterval(timer);
    }, [isPlaying, isPaused, dragging, duration]);

    // keep slider in sync
    useEffect(() => {
        if (!dragging && duration)
            setSliderValue((currentTime / duration) * 100);
    }, [currentTime, duration, dragging]);

    // update CSS custom property for fill
    useEffect(() => {
        sliderRef.current?.style.setProperty('--pct', `${sliderValue}%`);
    }, [sliderValue]);

    const handleRelease = () => {
        if (!botInChannel || !discordUser) return
        const time = (sliderValue / 100) * duration;
        setDragging(false);
        setCurrentTime(time);
        send({ type: "seek", discord_id: discordUser.discord_id, position: time });
    };

    return (
        <>
            <style>{`
                .progress-slider {
                    -webkit-appearance: none;
                    appearance: none;
                    width: 100%;
                    height: 3px;
                    background: rgba(255,255,255,0.12);
                    border-radius: 3px;
                    outline: none;
                    cursor: pointer;
                }
                .progress-slider::-webkit-slider-runnable-track {
                    height: 3px;
                    border-radius: 3px;
                    background: linear-gradient(
                        to right,
                        rgba(255,255,255,0.75) var(--pct, 0%),
                        rgba(255,255,255,0.12) var(--pct, 0%)
                    );
                }
                .progress-slider::-webkit-slider-thumb {
                    -webkit-appearance: none;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    background: #fff;
                    cursor: pointer;
                    opacity: 0;
                    transition: opacity 0.15s;
                    margin-top: -4.5px;
                }
                .progress-row:hover .progress-slider::-webkit-slider-thumb {
                    opacity: 1;
                }
                .progress-slider::-moz-range-track {
                    height: 3px;
                    border-radius: 3px;
                    background: rgba(255,255,255,0.12);
                }
                .progress-slider::-moz-range-progress {
                    height: 3px;
                    border-radius: 3px;
                    background: rgba(255,255,255,0.75);
                }
                .progress-slider::-moz-range-thumb {
                    width: 12px;
                    height: 12px;
                    border: none;
                    border-radius: 50%;
                    background: #fff;
                    cursor: pointer;
                    opacity: 0;
                }
                .progress-row:hover .progress-slider::-moz-range-thumb {
                    opacity: 1;
                }
            `}</style>
            <div className={`${className} progress-row flex items-center gap-2.5`}>
                <span className="text-[11px] text-white/35 tabular-nums w-8 text-right select-none">
                    { currentVideo ? NumToTime(displayTime) : "-:--"}
                </span>
                <input
                    ref={sliderRef}
                    type="range"
                    min={0}
                    max={100}
                    step={0.1}
                    value={sliderValue}
                    onChange={e => setSliderValue(Number(e.target.value))}
                    onMouseDown={() => setDragging(true)}
                    onTouchStart={() => setDragging(true)}
                    onMouseUp={handleRelease}
                    onTouchEnd={handleRelease}
                    className="progress-slider flex-1"
                    style={{ '--pct': `${sliderValue}%` } as React.CSSProperties}
                />
                <span className="text-[11px] text-white/35 tabular-nums w-8 select-none">
                    {NumToTime(duration)}
                </span>
            </div>
        </>
    );
}
