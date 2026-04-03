import { useEffect, useState } from "react";
import { NumToTime } from "./utilities/misc";
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";
import { useSocketContext } from "~/contexts/SocketContext";

export default function SongProgressBar({ className }: { className?: string }) {
    const { send } = useSocketContext();
    const { video, videoPlaybackStatus } = usePlaybackVideoContext();

    const isPlaying = videoPlaybackStatus?.playing ?? false;
    const isPaused  = videoPlaybackStatus?.paused  ?? false;
    const duration  = video?.duration ?? 0;

    const [currentTime, setCurrentTime] = useState(videoPlaybackStatus?.position ?? 0);
    const [sliderValue, setSliderValue] = useState(0);
    const [dragging, setDragging]       = useState(false);

    const displayTime = dragging ? (sliderValue / 100) * duration : Math.min(duration, currentTime);

    // sync on server push
    useEffect(() => {
        if (videoPlaybackStatus?.position !== undefined)
            setCurrentTime(videoPlaybackStatus.position);
    }, [videoPlaybackStatus?.position]);

    // local tick
    useEffect(() => {
        if (!isPlaying || isPaused || dragging) return;
        const timer = setInterval(() => setCurrentTime(t => Math.min(duration, t + 1)), 1000);
        return () => clearInterval(timer);
    }, [isPlaying, isPaused, dragging, duration]);

    // keep slider in sync when not dragging
    useEffect(() => {
        if (!dragging && duration)
            setSliderValue((currentTime / duration) * 100);
    }, [currentTime, duration, dragging]);

    const handleRelease = () => {
        const time = (sliderValue / 100) * duration;
        setDragging(false);
        setCurrentTime(time);
        send({ type: "seek", position: time });
    };

    return (
        <div className={`${className} flex items-center gap-2 text-xs text-gray-400 w-64`}>
            <span>{NumToTime(displayTime)}</span>
            <input
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
                className="range range-xs range-primary flex-1"
            />
            <span>{NumToTime(duration)}</span>
        </div>
    );
}
