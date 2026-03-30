import { useEffect, useState } from "react";
import { NumToTime } from "./utilities/misc";


export default  function SongProgressBar({ className, currentTime, setCurrentTime, duration }: { className? : string, currentTime: number; duration: number; setCurrentTime: (value: number) => void; }) {
    const [localValue, setLocalValue] = useState(0);
    const [dragging, setDragging] = useState(false);
    const displayTime = dragging ? (localValue / 100) * duration : Math.min(duration, currentTime);

    useEffect(() => {
        if (!dragging && duration) setLocalValue((currentTime / duration) * 100);
    }, [currentTime, duration]);

    function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
        setLocalValue(Number(e.target.value));
    }

    function handleRelease() {
        setDragging(false);
        setCurrentTime((localValue / 100) * duration);
    }

    return (
        <div className={`${className} flex items-center gap-2 text-xs text-gray-400 w-64`}>
            <span>{NumToTime(displayTime)}</span>
            <input
                type="range"
                min={0}
                max={100}
                value={localValue}
                onChange={handleChange}
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
