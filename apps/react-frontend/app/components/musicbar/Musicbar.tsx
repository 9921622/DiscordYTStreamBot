import { useBotContext } from "~/contexts/BotContext"
import { usePlaylistContext } from "~/contexts/PlaylistContext";

import ArtistInfo from "./MusicbarArtistInfo";
import SongProgressBar from "./MusicbarSongProgressBar";
import SongControls from "./MusicbarSongControls";
import MusicbarTags from "./MusicbarTags";
import VolumeControl from "./MusicbarVolumeControl";
import { useEffect, useRef, useState } from "react";

export default function Musicbar() {
    const { currentVideo, currentVideoLoading } = usePlaylistContext()  // TODO: useCurrentPlayback
    const { botInChannel } = useBotContext()
    const barRef = useRef<HTMLDivElement>(null)
    const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null)
    const [isHovered, setIsHovered] = useState(false)
    const animFrameRef = useRef<number | null>(null)
    const targetPos = useRef<{ x: number; y: number } | null>(null)
    const currentPos = useRef<{ x: number; y: number } | null>(null)

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

    // Smooth lerp animation loop
    useEffect(() => {
        const lerp = (a: number, b: number, t: number) => a + (b - a) * t

        const tick = () => {
            if (targetPos.current) {
                if (!currentPos.current) {
                    currentPos.current = { ...targetPos.current }
                } else {
                    currentPos.current = {
                        x: lerp(currentPos.current.x, targetPos.current.x, 0.1),
                        y: lerp(currentPos.current.y, targetPos.current.y, 0.1),
                    }
                }
                setMousePos({ ...currentPos.current })
            }
            animFrameRef.current = requestAnimationFrame(tick)
        }

        animFrameRef.current = requestAnimationFrame(tick)
        return () => {
            if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
        }
    }, [])

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        const rect = barRef.current?.getBoundingClientRect()
        if (!rect) return
        targetPos.current = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
        }
    }

    const handleMouseEnter = () => setIsHovered(true)
    const handleMouseLeave = () => {
        setIsHovered(false)
        targetPos.current = null
        currentPos.current = null
        setMousePos(null)
    }


    const disabled = !currentVideo || !botInChannel

    return (
        <div
            ref={barRef}
            onMouseMove={handleMouseMove}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            className="fixed bottom-0 w-full bg-[#0f0f0f] text-white px-5 py-3.5 flex items-center justify-between shadow-xl border-t border-white/5"
            style={{ minHeight: 72 }}
        >
            {/* Mouse-following white glow */}
            {mousePos && isHovered && (
                <div
                    className="absolute inset-0 z-0 pointer-events-none overflow-hidden"
                    style={{
                        maskImage: 'none',
                    }}
                >
                    <div
                        style={{
                            position: 'absolute',
                            left: mousePos.x,
                            top: mousePos.y,
                            transform: 'translate(-50%, -50%)',
                            width: 700,
                            height: 700,
                            borderRadius: '50%',
                            background: 'radial-gradient(circle, rgba(255,255,255,0.13) 0%, rgba(255,255,255,0.07) 35%, transparent 70%)',
                            pointerEvents: 'none',
                            transition: 'opacity 0.3s ease',
                            opacity: isHovered ? 1 : 0,
                        }}
                    />
                </div>
            )}

            {/* Animated blurred background */}
            {currentVideo?.thumbnail && (
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
                            backgroundImage: `url(${currentVideo.thumbnail})`,
                            backgroundSize: 'cover',
                            backgroundPosition: 'center',
                            filter: 'blur(28px) brightness(0.5) saturate(2)',
                            animation: 'bgDrift 14s ease-in-out infinite',
                            transform: 'scale(1.15)',
                        }}
                    />
                    <div className="absolute inset-0 bg-black/50" />
                </>
            )}
            {!currentVideo?.thumbnail && <div className="absolute inset-0 bg-[#0f0f0f]" />}

            {/* Left — artist info */}
            <div className="relative z-10 flex items-center gap-3 w-100 min-w-0 flex-shrink-0">
                <ArtistInfo video={currentVideo} loading={currentVideoLoading} />
            </div>

            {/* Center — controls + progress */}
            <div className={`absolute left-1/2 -translate-x-1/2 z-10 ${disabled ? "cursor-not-allowed" : ""}`}>
                <div className={`flex flex-col items-center gap-2 w-[700px] ${disabled ? "opacity-30 pointer-events-none" : ""}`}>
                    {!botInChannel && currentVideo && (
                        <p className="text-[11px] text-amber-400/80 tracking-wide">Bot is not in your voice channel</p>
                    )}
                    <SongControls className="w-full justify-center" />
                    <SongProgressBar className="w-full" />
                </div>
            </div>

            {/* Right — tags + volume */}
            <div className="relative z-10 flex items-center gap-3 ml-auto flex-shrink-0">
                <MusicbarTags tags={currentVideo?.tags ?? []} />
                <VolumeControl />
            </div>
        </div>
    );
}
