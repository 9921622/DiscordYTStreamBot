import { PlayIcon } from "./utilities/Icons";
import { useBotContext } from "~/contexts/BotContext";


export default function SongCard({ songTitle, artistName, albumArtUrl, onClick }: { songTitle: string; artistName: string; albumArtUrl: string; onClick?: () => void; }) {
    const { botInChannel } = useBotContext()

    return (
        <div className={`card bg-base-100 w-50 h-50 shadow-sm relative overflow-hidden group ${!botInChannel ? "cursor-not-allowed" : ""}`}>
            <figure className="h-full">
                <img src={albumArtUrl} alt={songTitle} className="w-full h-full object-cover" />
            </figure>

            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/70 to-transparent p-4">
                <h2 className="card-title text-white text-lg line-clamp-2">{songTitle}</h2>
                <p className="text-gray-300 text-sm">{artistName}</p>

                <div className="card-actions justify-end mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="tooltip tooltip-top" data-tip={!botInChannel ? "Bot is not in your voice channel" : undefined}>
                        <button
                            className="btn btn-primary btn-sm"
                            onClick={onClick}
                            disabled={!botInChannel}
                        >
                            <PlayIcon />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
