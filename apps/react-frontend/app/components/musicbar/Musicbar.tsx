import { useBotContext } from "~/contexts/BotContext"
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";

import ArtistInfo from "./MusicbarArtistInfo";
import SongProgressBar from "./MusicbarSongProgressBar";
import SongControls from "./MusicbarSongControls";
import MusicbarTags from "./MusicbarTags";
import VolumeControl from "./MusicbarVolumeControl";
import { useEffect, useRef } from "react";

export default function Musicbar() {
    const { video, videoLoading, videoError } = usePlaybackVideoContext()
    const { botInChannel } = useBotContext()
    const barRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        const el = barRef.current
        if (!el) return
        const observer = new ResizeObserver(([entry]) => {
            document.documentElement.style.setProperty(
                "--musicbar-height",
                `${entry.contentRect.height}px`
            )
        })
        observer.observe(el)
        return () => observer.disconnect()
    }, [])

    if (videoError) return (
        <div className="fixed bottom-0 w-full flex items-center justify-center px-4 py-5 bg-[#0f0f0f]">
            <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2">
                <span>⚠️</span>
                <span>{videoError}</span>
            </div>
        </div>
    )

    const disabled = !video || !botInChannel

    return (
        <div
            ref={barRef}
            className="fixed bottom-0 w-full bg-[#0f0f0f] text-white px-5 py-3.5 flex items-center justify-between shadow-xl border-t border-white/5"
            style={{ minHeight: 72 }}
        >
            {/* Animated blurred background */}
            {video?.thumbnail && (
                <>
                    <style>{`
                        @keyframes bgDrift {
                            0%   { transform: scale(1.1) translate(0%, 0%); }
                            33%  { transform: scale(1.18) translate(-1.5%, 1%); }
                            66%  { transform: scale(1.14) translate(1.5%, -1%); }
                            100% { transform: scale(1.1) translate(0%, 0%); }
                        }
                    `}</style>
                    <div
                        className="absolute inset-0 transition-all duration-1000"
                        style={{
                            backgroundImage: `url(${video.thumbnail})`,
                            backgroundSize: 'cover',
                            backgroundPosition: 'center',
                            filter: 'blur(28px) brightness(0.3) saturate(1.4)',
                            animation: 'bgDrift 14s ease-in-out infinite',
                            transform: 'scale(1.15)',
                        }}
                    />
                    <div className="absolute inset-0 bg-black/50" />
                </>
            )}
            {!video?.thumbnail && <div className="absolute inset-0 bg-[#0f0f0f]" />}

            {/* Left — artist info */}
            <div className="relative z-10 flex items-center gap-3 w-100 min-w-0 flex-shrink-0">
                <ArtistInfo video={video} loading={videoLoading} />
            </div>

            {/* Center — controls + progress */}
            <div className={`absolute left-1/2 -translate-x-1/2 z-10 ${disabled ? "cursor-not-allowed" : ""}`}>
                <div className={`flex flex-col items-center gap-2 w-[700px] ${disabled ? "opacity-30 pointer-events-none" : ""}`}>
                    {!botInChannel && video && (
                        <p className="text-[11px] text-amber-400/80 tracking-wide">Bot is not in your voice channel</p>
                    )}
                    <SongControls className="w-full justify-center" />
                    <SongProgressBar className="w-full" />
                </div>
            </div>

            {/* Right — tags + volume */}
            <div className="relative z-10 flex items-center gap-3 ml-auto flex-shrink-0">
                <MusicbarTags tags={video?.tags ?? []} />
                <VolumeControl />
            </div>
        </div>
    );
}
