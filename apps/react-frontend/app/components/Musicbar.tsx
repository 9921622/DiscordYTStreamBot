import type { YoutubeVideo } from "~/api/youtube/youtube-types";
import { youtubeAPI, extractYoutubeId } from "~/api/youtube/youtube-wrapper";
import { useEffect, useState } from "react";

import { PlayIcon, PauseIcon, PrevIcon, NextIcon, VolumeIcon, LoopIcon, ShuffleIcon } from "./utilities/Icons";
import { NumToTime } from "./utilities/misc";


function ArtistInfo({ songTitle, artistName, albumArtUrl, loading }: { songTitle: string; artistName: string; albumArtUrl: string, loading : boolean }) {
    if (loading) {
        return (
            <>
                <div className="skeleton w-12 h-12 rounded" />
                <div className="flex flex-col gap-2">
                    <div className="skeleton h-4 w-32" />
                    <div className="skeleton h-3 w-24" />
                </div>
            </>
        );
    }

    return (
        <>
            <img
            src={albumArtUrl}
            alt="Album Art"
            className="w-12 h-12 object-cover rounded"
            />
            <div>
            <div className="font-semibold">{songTitle}</div>
            <div className="text-gray-400 text-sm">{artistName}</div>
            </div>
        </>
    );
}


function SongControls() {
    return (
        <div className="flex items-center gap-4">
            <button className="btn btn-ghost btn-circle hover:bg-gray-800">
            <ShuffleIcon />
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800">
            <PrevIcon />
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800">
            <PlayIcon />
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800">
            <NextIcon />
            </button>
            <button className="btn btn-ghost btn-circle hover:bg-gray-800">
            <LoopIcon />
            </button>
        </div>
    );
}

function SongProgressBar({ currentTime, setCurrentTime, duration }: { currentTime: number; duration: number; setCurrentTime: (value: number) => void; }) {
    const [localValue, setLocalValue] = useState((currentTime / duration) * 100);
    const [dragging, setDragging] = useState(false);

    useEffect(() => {
        if (!dragging) setLocalValue((currentTime / duration) * 100);
    }, [currentTime, duration]);

    function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
        setLocalValue(Number(e.target.value));
    }

    function handleRelease() {
        setDragging(false);
        setCurrentTime((localValue / 100) * duration);
    }

    return (
        <div className="flex items-center gap-2 text-xs text-gray-400 w-64">
            <span>0:00</span>
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


export default function Musicbar() {
    const [video, setVideo] = useState<YoutubeVideo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [currentTime, setCurrentTime] = useState<number>(90);


    useEffect(() => {
        (async () => {
            try {
                const id = extractYoutubeId("https://www.youtube.com/watch?v=iNxCLMKGZ0o&list=RDiNxCLMKGZ0o&start_radio=1") || "";
                // const id = extractYoutubeId("https://www.youtube.com/watch?v=dei1SgfaQ-E&list=RDdei1SgfaQ-E&start_radio=1") || "";
                const fetchedVideo = await youtubeAPI.video.retrieve(id);
                setVideo(fetchedVideo);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to fetch video");
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    if (!loading && (error || !video))
        return <div className="bg-gray-900 text-white px-4 py-2 fixed bottom-0 w-full">Error: {error}</div>;

    const songTitle = video?.title ?? "";
    const songDuration = video?.duration ?? 0;
    const artistName = video?.creator ?? "";
    const albumArtUrl = video?.thumbnail ?? "";
    const tags = video?.tags ?? [];

    return (
        <div className="bg-gray-900 text-white px-4 py-2 flex items-center justify-between shadow-inner fixed bottom-0 w-full">


            <div className="flex items-center gap-3">
                <ArtistInfo
                    songTitle={songTitle} artistName={artistName} albumArtUrl={albumArtUrl}
                    loading={loading}
                    />
            </div>


            <div className="flex flex-col items-center gap-2">
                <SongControls />
                <SongProgressBar
                    currentTime={currentTime} setCurrentTime={setCurrentTime} duration={songDuration}/>
            </div>

            <div className="flex items-center gap-2 flex-wrap max-w-xs">
                {tags.map((tag) => (
                    <span key={tag.id} className="badge badge-sm badge-primary">
                        {tag.name}
                    </span>
                ))}
            </div>

            <div className="flex items-center gap-3">
                <button className="btn btn-ghost btn-circle hover:bg-gray-800">
                <VolumeIcon />
                </button>
            </div>


        </div>
    );
}
