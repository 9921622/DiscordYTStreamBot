import { useEffect, useRef, useState } from "react";

import SongSearchbarCard from "./SongSearchbarCard";

import { youtubeAPI } from "~/api/youtube/youtube-wrapper";
import type { YoutubeSearch, YoutubeVideo } from "~/api/youtube/youtube-types";
import { usePlaybackVideoContext } from "~/contexts/PlaybackVideoContext";
import SongDropdown from "./SongDropdown";

function SearchIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.35-4.35" />
    </svg>
  );
}

function ClearIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 6 6 18M6 6l12 12" />
    </svg>
  );
}

function ArrowRightIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-6">
      <div className="w-5 h-5 border-2 border-zinc-600 border-t-zinc-300 rounded-full animate-spin" />
    </div>
  );
}

function EmptyState({ query }: { query: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-6 gap-1">
      <p className="text-sm text-zinc-400">No results for <span className="text-zinc-200">"{query}"</span></p>
      <p className="text-xs text-zinc-600">Try a different search term</p>
    </div>
  );
}

function SongSearchbarDropdownExtra({ query }: { query: string }) {
  return (
    <div className="border-t border-zinc-800 mt-1 pt-1">
      <button className="w-full text-left px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 rounded-md transition flex items-center justify-between gap-2">
        <span className="truncate">Show full results for "{query}"</span>
        <ArrowRightIcon />
      </button>
    </div>
  );
}

export default function SongSearchbar() {
  const { videoPlay } = usePlaybackVideoContext();
  const [search, setSearch] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [results, setResults] = useState<YoutubeVideo[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // search handler with loading state
  useEffect(() => {
    if (!search) {
      setResults([]);
      setHasSearched(false);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setHasSearched(false);

    const timer = setTimeout(async () => {
      try {
        const res: YoutubeSearch = await youtubeAPI.search.search({
          q: search,
          max_results: 5,
        });
        setResults(res.results || []);
      } catch {
        setResults([]);
      } finally {
        setIsLoading(false);
        setHasSearched(true);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [search]);

  // close on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (!containerRef.current?.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleClear() {
    setInputValue("");
    setSearch("");
    setResults([]);
    setHasSearched(false);
    inputRef.current?.focus();
  }

  const showDropdown = isOpen && inputValue.length > 0;
  const showEmpty = hasSearched && !isLoading && results.length === 0;

  return (
    <div ref={containerRef} className="relative w-full md:w-[600px]">
      {/* Input wrapper */}
      <div className="flex items-center gap-2 rounded-full bg-gray-900 border border-gray-700 px-3.5 focus-within:border-gray-500 transition-colors">
        <span className="text-zinc-500 flex-shrink-0">
          <SearchIcon />
        </span>

        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          placeholder="Search from YouTube"
          onFocus={() => setIsOpen(true)}
          onChange={(e) => {
            setInputValue(e.target.value);
            setSearch(e.target.value.trim());
          }}
          onKeyDown={(e) => {
            if (e.key === "Escape") {
              setIsOpen(false);
              inputRef.current?.blur();
            }
          }}
          className="flex-1 bg-transparent outline-none text-white placeholder-gray-400 py-2 text-sm"
        />

        {inputValue && (
          <button
            onMouseDown={(e) => e.preventDefault()}
            onClick={handleClear}
            className="text-zinc-500 hover:text-zinc-200 transition flex-shrink-0"
            aria-label="Clear search"
          >
            <ClearIcon />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {showDropdown && (
        <ul className="absolute left-0 mt-2 w-full bg-zinc-900 rounded-lg shadow-xl border border-zinc-800 z-[999] p-2 flex flex-col gap-1 animate-in fade-in slide-in-from-top-1 duration-150">
          {isLoading && <LoadingSpinner />}

          {!isLoading && showEmpty && <EmptyState query={search} />}

          {!isLoading && results.map((item) => (
            <li key={item.youtube_id}>
              <SongDropdown song={item}>
                <SongSearchbarCard
                  song={item}
                  onClick={() => {
                    videoPlay?.(item);
                    setIsOpen(false);
                  }}
                />
              </SongDropdown>
            </li>
          ))}

          {!isLoading && results.length > 0 && (
            <SongSearchbarDropdownExtra query={search} />
          )}
        </ul>
      )}
    </div>
  );
}
