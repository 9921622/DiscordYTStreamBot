import { useState } from "react";
import { createPortal } from "react-dom";

interface AvatarProps {
    src: string
    alt: string
    tooltip?: string
    size?: number
    className?: string
    ring?: boolean
}

export default function MemberAvatar({ src, alt, tooltip, size = 28, className = "", ring = false }: AvatarProps) {
    const [pos, setPos] = useState<{ x: number; y: number } | null>(null);

    return (
        <div
            className="inline-flex items-center relative"
            onMouseEnter={e => {
                const r = e.currentTarget.getBoundingClientRect();
                setPos({ x: r.left + r.width / 2, y: r.top - 6 });
            }}
            onMouseLeave={() => setPos(null)}>
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
            {pos && tooltip && createPortal(
                <div
                    className="fixed z-[9999] pointer-events-none -translate-x-1/2 -translate-y-full"
                    style={{ left: pos.x, top: pos.y }}
                >
                    <div className="bg-base-300 text-base-content text-xs rounded px-2 py-1 shadow-lg whitespace-nowrap">
                        {tooltip}
                    </div>
                </div>,
                document.body
            )}
        </div>
    );
}
