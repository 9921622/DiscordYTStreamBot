import { useSearchParams } from "react-router";
import { useEffect, useState } from "react";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";
import { youtubeAPI, extractYoutubeId } from "~/api/youtube/youtube-wrapper";
import { discordBotAPI } from "~/api/discord/discord-wrapper";

import ArtistInfo from "./MusicbarArtistInfo";
import SongProgressBar from "./MusicbarSongProgressBar";
import { VolumeIcon } from "./utilities/Icons";
import SongControls from "./MusicbarSongControls";
import MusicbarTags from "./MusicbarTags";



export default function Musicbar({ video, loading }: { video: YoutubeVideo | null, loading: boolean }) {
    const GUILD_ID = `${import.meta.env.VITE_DEBUG_GUILD}`;

    const [currentTime, setCurrentTime] = useState<number>(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isPaused, setIsPaused] = useState(false);

    // Local tick
    useEffect(() => {
        if (!isPlaying || isPaused) return;

        const timer = setInterval(() => {
            setCurrentTime(t => t + 1);
        }, 1000);

        return () => clearInterval(timer);
    }, [isPlaying, isPaused]);

    // Poll the music position from server
    useEffect(() => {
        if (!video) return;

        const poll = async () => {
            try {
                const status = await discordBotAPI.musicControl.status(GUILD_ID);
                setCurrentTime(status.position);
                setIsPlaying(status.playing);
                setIsPaused(status.paused);
            } catch {}
        };

        poll();
        const interval = setInterval(poll, 5000);
        return () => clearInterval(interval);
    }, [video]);

    const handlePause = async () => {
        await discordBotAPI.musicControl.pause(GUILD_ID);
        setIsPaused(p => !p); // optimistic update, poll will correct it
    };

    const handleSeek = async (time: number) => {
        setCurrentTime(time);
        await discordBotAPI.musicControl.seek(GUILD_ID, time);
    };

    const tags = video?.tags ?? [];

    return (
        <div className="bg-gray-900 text-white px-4 py-2 flex items-center justify-between shadow-inner fixed bottom-0 w-full">

            <div className="flex items-center gap-3">
                <ArtistInfo
                    video={video}
                    loading={loading}
                    />
            </div>

            <div className={!video ? "cursor-not-allowed" : ""}>
                <div className={`flex flex-col items-center gap-2 ${!video ? "opacity-40 pointer-events-none" : ""}`}>
                    <SongControls
                        isPlaying={isPlaying}
                        isPaused={isPaused}
                        onPause={handlePause}/>
                    <SongProgressBar
                        currentTime={currentTime}
                        setCurrentTime={handleSeek}
                        duration={video?.duration ?? 0}/>
                </div>
            </div>

            <div className="flex items-center gap-2">
                <MusicbarTags tags={tags} />
            </div>

            <div className="flex items-center gap-3">
                <button className="btn btn-ghost btn-circle hover:bg-gray-800">
                <VolumeIcon />
                </button>
            </div>


        </div>
    );
}
