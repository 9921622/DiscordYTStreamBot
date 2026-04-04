import type { YoutubeVideo } from "~/api/youtube/youtube-types";

export default function ArtistInfo({ video, loading }: { video: YoutubeVideo | null, loading: boolean }) {
    if (loading) {
        return (
            <>
                <div className="w-[75px] h-[75px] rounded-[10px] bg-white/10 animate-pulse flex-shrink-0" />
                <div className="flex flex-col gap-2 min-w-0">
                    <div className="h-3.5 w-32 rounded-md bg-white/10 animate-pulse" />
                    <div className="h-3 w-20 rounded-md bg-white/10 animate-pulse" />
                </div>
            </>
        );
    }

    if (!video) return null;

    return (
        <>
            <div className="relative flex-shrink-0">
                <img
                    src={video.thumbnail}
                    alt="Album Art"
                    className="w-[75px] h-[75px] object-cover rounded-[10px]"
                    style={{ outline: '2px solid rgba(255,255,255,0.10)', outlineOffset: 2 }}
                />
            </div>
            <div className="min-w-0">
                <div
                    className="text-[13.5px] font-medium text-white leading-snug truncate tracking-[-0.01em]"
                    title={video.title}
                >
                    {video.title}
                </div>
                <div className="text-[12px] text-white/40 mt-0.5 truncate">
                    {video.creator}
                </div>
            </div>
        </>
    );
}
