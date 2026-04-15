import { Loader2, Pause, Play, Volume, Volume1, Volume2, VolumeX } from "lucide-react";

export function LoadingSpinner() {
	return (
		<div className="flex items-center justify-center py-6">
			<Loader2 className="w-5 h-5 text-zinc-300 animate-spin" />
		</div>
	);
}

export function PlayPauseIcon({ isPlaying, className = "w-5 h-5" }: { isPlaying: boolean, className?: string }) {
	const Icon = isPlaying ? Pause : Play;
	if (!Icon) return null;
	return (
		<Icon className={`${className}`} />
	);
}

export function ScalingVolumeIcon({ className, level }: {  className?: string, level: number }) {
	let Icon;
	const safeLevel = Math.max(0, Math.min(1, level));
	switch (true) {
		case safeLevel <= 0:
		Icon = VolumeX;
		break;
		case safeLevel < 0.33:
		Icon = Volume;
		break;
		case safeLevel < 0.66:
		Icon = Volume1;
		break;
		default:
		Icon = Volume2;
	}

	return <Icon className={className} />;
}

export function DragHandle() {
    return (
        <svg className="w-5 h-6 text-zinc-500 flex-shrink-0" fill="currentColor" viewBox="0 0 8 16">
            <circle cx="2" cy="3"  r="1.2" /><circle cx="6" cy="3"  r="1.2" />
            <circle cx="2" cy="8"  r="1.2" /><circle cx="6" cy="8"  r="1.2" />
            <circle cx="2" cy="13" r="1.2" /><circle cx="6" cy="13" r="1.2" />
        </svg>
    )
}

export function EqualizerBars({ className = "" }: { className?: string }) {
    return (
        <div className={`flex gap-[2px] items-end h-4 ${className}`}>
            <span className="w-[2px] bg-green-400 animate-eq-fast" />
            <span className="w-[2px] bg-green-400 animate-eq [animation-delay:-0.2s]" />
            <span className="w-[2px] bg-green-400 animate-eq-slow [animation-delay:-0.4s]" />
        </div>
    )
}
