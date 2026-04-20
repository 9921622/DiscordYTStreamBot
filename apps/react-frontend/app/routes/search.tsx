import { useSearchParams } from "react-router";
import { useEffect, useState } from "react";
import { youtubeAPI } from "~/api/youtube/youtube-wrapper";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";
import type { YoutubeSearch } from "~/api/youtube/youtube-types";
import SongContainer from "~/components/SongContainer";
import { LoadingSpinner } from "~/components/utilities/Icons";

function useSearchResults(query: string) {
    const [results, setResults] = useState<YoutubeVideo[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (!query) { setResults([]); return; }
        setIsLoading(true);
        youtubeAPI.search.search({ q: query, max_results: 25 })
            .then((res: YoutubeSearch) => setResults(res.results || []))
            .catch(() => setResults([]))
            .finally(() => setIsLoading(false));
    }, [query]);

    return { results, isLoading };
}

export default function SearchPage() {
    const [searchParams] = useSearchParams();
    const query = searchParams.get("q") ?? "";
    const { results, isLoading } = useSearchResults(query);

    return (
        <div className="p-6">
            <header className="mb-5">
                <h1 className="text-2xl font-semibold tracking-tight">
                    {query ? `Results for "${query}"` : "Search"}
                </h1>
                <p className="text-base-content/40 text-sm mt-0.5">
                    {isLoading ? "Searching…" : results.length > 0 ? `${results.length} tracks` : query ? "No results" : ""}
                </p>
            </header>

            {isLoading && <LoadingSpinner />}
            {!isLoading && <SongContainer songs={results} />}
            <div className="h-4" />
        </div>
    );
}
