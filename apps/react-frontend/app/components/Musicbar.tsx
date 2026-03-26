import type { YoutubeVideo } from "~/api/youtube/youtube-types";
import { youtubeAPI, extractYoutubeId } from "~/api/youtube/youtube-wrapper";
import { useEffect, useState } from "react";

import { PlayIcon, PauseIcon, PrevIcon, NextIcon, VolumeIcon, LoopIcon, ShuffleIcon } from "./utilities/Icons";



function ArtistInfo({ songTitle, artistName, albumArtUrl }: { songTitle: string; artistName: string; albumArtUrl: string }) {
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

function SongProgressBar({ currentTime, duration }: { currentTime: number; duration: number }) {
    const progress = (currentTime / duration) * 100;
    return (
        <div className="flex items-center gap-2 text-xs text-gray-400 w-64">
            <span>0:00</span>
            <input
            type="range"
            min={0}
            max={100}
            defaultValue={progress}
            className="range range-xs range-primary flex-1"
            />
            <span>{Math.floor(duration / 60)}:{String(duration % 60).padStart(2, '0')}</span>
        </div>
    );
}


export default function Musicbar() {
    const [video, setVideo] = useState<YoutubeVideo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        (async () => {
            try {
                const id = extractYoutubeId("https://www.youtube.com/watch?v=e0XBIicJmAE&list=RDO1-Ims-3RJU&index=2") || "";
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

    if (loading) return <div className="bg-gray-900 text-white px-4 py-2 fixed bottom-0 w-full">Loading...</div>;
    if (error || !video) return <div className="bg-gray-900 text-white px-4 py-2 fixed bottom-0 w-full">Error: {error}</div>;

    const songTitle = video.title;
    const songDuration = video.duration;
    const artistName = video.creator;
    const albumArtUrl = video.thumbnail || "";
    const tags = video.tags || [];
    const url = video.source_url;
    const currentTime = 90;

    return (
        <div className="bg-gray-900 text-white px-4 py-2 flex items-center justify-between shadow-inner fixed bottom-0 w-full">


            <div className="flex items-center gap-3">
                <ArtistInfo songTitle={songTitle} artistName={artistName} albumArtUrl={albumArtUrl} />
            </div>


            <div className="flex flex-col items-center gap-2">
                <SongControls />
                <SongProgressBar currentTime={currentTime} duration={songDuration} />
            </div>

            {/* Tags */}
            <div className="flex items-center gap-2 flex-wrap max-w-xs">
                {tags.map((tag) => (
                    <span key={tag.id} className="badge badge-sm badge-primary">
                        {tag.name}
                    </span>
                ))}
            </div>

            {/* Volume Control */}
            <div className="flex items-center gap-3">
                <button className="btn btn-ghost btn-circle hover:bg-gray-800">
                <VolumeIcon />
                </button>
            </div>


        </div>
    );
}
