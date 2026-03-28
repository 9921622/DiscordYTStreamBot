import type { YoutubeVideo } from "~/api/youtube/youtube-types";

export default function ArtistInfo({ video, loading }: { video: YoutubeVideo | null, loading : boolean }) {
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

    if (!video) return;

    return (
        <>
            <img
            src={video.thumbnail}
            alt="Album Art"
            className="w-12 h-12 object-cover rounded"
            />
            <div>
            <div className="font-semibold">{video.title}</div>
            <div className="text-gray-400 text-sm">{video.creator}</div>
            </div>
        </>
    );
}
