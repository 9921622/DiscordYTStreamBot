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
import VolumeControl from "./MusicbarVolumeControl";



export default function Musicbar({ video, loading, error }: { video: YoutubeVideo | null, loading: boolean, error: string | null }) {
    const GUILD_ID = `${import.meta.env.VITE_DEBUG_GUILD}`;
    const [searchParams, setSearchParams] = useSearchParams();

    const [volume, setVolume] = useState<number>(Number(searchParams.get("vol") ?? 1.0));
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

    const poll = async () => {
        try {
            const status = await discordBotAPI.musicControl.status(GUILD_ID);
            setCurrentTime(status.position);
            setIsPlaying(status.playing);
            setIsPaused(status.paused);
            setVolume(status.volume);
        } catch {}
    };

    // update poll when search params changes
    useEffect(() => {
        (async ()=>{
            await poll();
        })();
    }, [searchParams])

    useEffect(() => {
        if (!video) return;
        poll();
        const interval = setInterval(poll, 5000);
        return () => clearInterval(interval);
    }, [video]);

    const handlePause = async () => {
        await discordBotAPI.musicControl.pause(GUILD_ID);
        setIsPaused(p => !p);
        await poll();
    };

    const handleSeek = async (time: number) => {
        setCurrentTime(time);
        await discordBotAPI.musicControl.seek(GUILD_ID, time);
        await poll();
    };

    const handleVolume = async (level: number) => {
        await discordBotAPI.musicControl.setVolume(GUILD_ID, level);
        setVolume(level);
        setSearchParams(prev => {
            prev.set("vol", String(level));
            return prev;
        }, { replace: true });
    };

    const tags = video?.tags ?? [];

    if (error)
        return <p>ERROR {error}</p>

    return (
        <div className="bg-gray-900 text-white px-4 py-5 flex items-center justify-between shadow-inner fixed bottom-0 w-full">

            <div className="flex items-center gap-3 w-1/4 min-w-0">
                <ArtistInfo
                    video={video}
                    loading={loading}
                    />
            </div>

            <div className={`absolute left-1/2 -translate-x-1/2 ${!video ? "cursor-not-allowed" : ""}`}>
                <div className={`flex flex-col items-center gap-2 w-150 ${!video ? "opacity-40 pointer-events-none" : ""}`}>
                    <SongControls
                        className="w-1/2"
                        isPlaying={isPlaying}
                        isPaused={isPaused}
                        onPause={handlePause}/>
                    <SongProgressBar
                        className="w-full"
                        currentTime={currentTime}
                        setCurrentTime={handleSeek}
                        duration={video?.duration ?? 0}/>
                </div>
            </div>

            <div className="flex items-center gap-2 w-1/6 justify-end ml-auto">
                <MusicbarTags tags={tags} />
            </div>

            <div className="flex items-center gap-3">
                <VolumeControl volume={volume} onVolumeChange={handleVolume} />
            </div>


        </div>
    );
}
