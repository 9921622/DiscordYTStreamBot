import SongCard from "~/components/SongContainerCard";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";
import SongDropdown from "./SongDropdown";

export default function SongContainer({ songs, className }: { songs: YoutubeVideo[]; className?: string }) {
    if (!songs?.length) {
        return <p className="text-gray-500 mt-6 text-sm">No songs available.</p>;
    }

    return (
        <div className={className}>
            <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3">
                {songs.map((song) => (
                    <SongDropdown key={song.youtube_id} song={song}>
                        <SongCard song={song} />
                    </SongDropdown>
                ))}
            </div>
        </div>
    );
}
