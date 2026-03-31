import SongContainerCard from "~/components/SongContainerCard";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";



export default function SongContainer({ songs, className } : { songs : YoutubeVideo[], className? : string; }) {
    const { videoPlay } = usePlaybackVideoContext()

    return (
        <div className={className}>
            {
            songs && songs.length > 0 ? (
                <div className="grid grid-cols-[repeat(auto-fill,minmax(180px,180px))] gap-12 justify-start">
                {songs.map((song) => (
                    <SongContainerCard
                    key={song.youtube_id}
                    songTitle={song.title}
                    artistName={song.creator}
                    albumArtUrl={song.thumbnail || ""}
                    onClick={() => videoPlay?.(song)}
                    />
                ))}
                </div>
            ) : (
                <p className="text-gray-500 mt-6">No songs available.</p>
            )
            }

        </div>
    );
}
