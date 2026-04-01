import SongContainerCard from "~/components/SongContainerCard";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";


export default function SongContainer({ songs, className }: { songs: YoutubeVideo[], className?: string }) {

    return (
        <div className={className}>
            {songs && songs.length > 0 ? (
                <div className="grid grid-cols-[repeat(auto-fill,minmax(180px,180px))] gap-12 justify-start">
                    {songs.map((song) => (
                        <SongContainerCard
                            key={song.youtube_id}
                            song={song}
                        />
                    ))}
                </div>
            ) : (
                <p className="text-gray-500 mt-6">No songs available.</p>
            )}
        </div>
    )
}
