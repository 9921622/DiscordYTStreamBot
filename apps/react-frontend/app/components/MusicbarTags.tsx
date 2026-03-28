

export default function MusicbarTags({ tags } : { tags : string[]}) {
    const MAX_TAGS = 3;

    return (
        <div>
            {tags.slice(0, MAX_TAGS).map((tag) => (
                <span key={tag} className="badge badge-sm badge-primary">
                    {tag}
                </span>
            ))}
            {tags.length > MAX_TAGS && (
                <span className="text-xs text-gray-400">+{tags.length - MAX_TAGS}</span>
            )}
        </div>
    );
}
