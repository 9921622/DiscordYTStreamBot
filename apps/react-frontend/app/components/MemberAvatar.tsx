interface AvatarProps {
    src: string
    alt: string
    tooltip?: string
    size?: number
    className?: string
    ring?: boolean
}

export default function MemberAvatar({ src, alt, tooltip, size = 28, className = "", ring = false }: AvatarProps) {
    return (
        <div
            className={tooltip ? "tooltip" : undefined}
            data-tip={tooltip}
        >
            <img
                src={src}
                alt={alt}
                style={{ width: size, height: size }}
                className={`
                    rounded-full flex-shrink-0
                    transition-transform duration-150
                    hover:scale-110 hover:z-50
                    ${ring ? "ring-[2px] ring-base-200 shadow-sm" : ""}
                    ${className}
                `.trim()}
            />
        </div>
    )
}
