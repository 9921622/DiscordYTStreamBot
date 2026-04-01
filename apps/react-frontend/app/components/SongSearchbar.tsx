import { useEffect, useRef, useState } from "react";

import { CrossIcon } from "./utilities/Icons";

import SongSearchbarCard from "./SongSearchbarCard";

import { youtubeAPI } from "~/api/youtube/youtube-wrapper";
import type { YoutubeSearch, YoutubeVideo } from "~/api/youtube/youtube-types";
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";
import SongDropdown from "./SongDropdown";


function SongSearchbarDropdownExtra({ query }: { query: string }) {
  return (
    <div className="border-t border-zinc-800 mt-1 pt-1">

        <button className="w-full text-left px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 rounded-md transition join">
        <span className="mr-2"> Show full results for "{query}" </span>
        <CrossIcon />
        </button>

    </div>
  );
}

export default function SongSearchbar() {
    const { videoPlay } = usePlaybackVideoContext()
    const [search, setSearch] = useState("");
    const [results, setResults] = useState<YoutubeVideo[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    // search handler
    useEffect(() => {
        if (!search) {
            setResults([]);
            return;
        }

        const timer = setTimeout(async () => {
            const res: YoutubeSearch = await youtubeAPI.search.search({
                q: search,
                max_results: 5,
            });
            setResults(res.results || []);
        }, 500);

        return () => clearTimeout(timer);
    }, [search]);

    // open handler
    useEffect(() => {
        function handleClickOutside(e: MouseEvent) {
            if (!containerRef.current?.contains(e.target as Node)) {
                setIsOpen(false);
            }
        }

        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (


        <div
            ref={containerRef}
            className="dropdown relative w-full md:w-[600px]">

        <input
            tabIndex={0}
            type="text"
            placeholder="Search from Youtube"
            onFocus={() => setIsOpen(true)}
            className="input input-md input-bordered rounded-full bg-gray-900 border-gray-700 placeholder-gray-400 text-white w-full"
            onChange={e => setSearch(e.target.value.trim())}
            />


        {isOpen && search && results.length > 0 && (
        <ul
            tabIndex={0}
            className="dropdown-content absolute left-0 mt-2 w-full bg-zinc-900 rounded-lg shadow-lg z-[999] p-2 flex flex-col gap-1"
            >

            {results.map((item, i) => (
            <li key={item.youtube_id}>
                <SongDropdown song={item}>
                <SongSearchbarCard song={item} onClick={() => videoPlay?.(item)}/>
                </SongDropdown>
            </li>
            ))}

            <SongSearchbarDropdownExtra query={search}/>

        </ul>
        )}

        </div>
    );
}
