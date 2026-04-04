export default function MusicbarTags({ tags }: { tags: string[] }) {
    const MAX_TAGS = 3;

    if (!tags.length) return null;

    return (
        <div className="flex items-center gap-1.5">
            {tags.slice(0, MAX_TAGS).map((tag) => (
                <span
                    key={tag}
                    className="text-[10.5px] px-2 py-0.5 rounded-full bg-white/10 text-white/60 border border-white/[0.12] whitespace-nowrap tracking-wide"
                >
                    {tag}
                </span>
            ))}
            {tags.length > MAX_TAGS && (
                <span className="text-[10.5px] text-white/30">
                    +{tags.length - MAX_TAGS}
                </span>
            )}
        </div>
    );
}
