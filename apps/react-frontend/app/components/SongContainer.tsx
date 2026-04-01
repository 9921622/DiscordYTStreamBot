import SongContainerCard from "~/components/SongContainerCard";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";
import SongDropdown from "./SongDropdown";


export default function SongContainer({ songs, className }: { songs: YoutubeVideo[], className?: string }) {

    return (
        <div className={className}>
            {songs && songs.length > 0 ? (
                <div className="grid grid-cols-[repeat(auto-fill,minmax(180px,180px))] gap-12 justify-start">
                    {songs.map((song) => (
                        <SongDropdown key={song.youtube_id} song={song}>
                        <SongContainerCard
                            song={song}
                            />
                        </SongDropdown>
                    ))}
                </div>
            ) : (
                <p className="text-gray-500 mt-6">No songs available.</p>
            )}
        </div>
    )
}
