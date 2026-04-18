import { useEffect, useState} from "react";

import { youtubeAPI } from "~/api/youtube/youtube-wrapper";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";
import SongContainer from "~/components/SongContainer";

function useSongs() {
    const [songs, setSongs] = useState<YoutubeVideo[]>([]);

    useEffect(() => {
        youtubeAPI.video.list().then(setSongs).catch(() => {});
    }, []);

    return songs;
}

export default function HomePage() {
    const songs = useSongs();
    return (
        <div className="p-6">
            <header className="mb-5">
                <h1 className="text-2xl font-semibold tracking-tight">All Songs</h1>
                <p className="text-base-content/40 text-sm mt-0.5">
                    {songs.length > 0 ? `${songs.length} tracks` : "Loading…"}
                </p>
            </header>
            <SongContainer songs={songs} />
            <div className="h-4" />
        </div>
    );
}
