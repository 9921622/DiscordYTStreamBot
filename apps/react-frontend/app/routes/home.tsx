import type { Route } from "./+types/home";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router";

import { youtubeAPI } from "~/api/youtube/youtube-wrapper";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";
import { discordBotAPI } from "~/api/discord/discord-wrapper";
import type { DiscordUser } from "~/api/backend-types";
import { backendAPI } from "~/api/backend-wrapper";

import Navbar from "~/components/Navbar";
import Musicbar from "~/components/Musicbar";
import SongContainer from "~/components/SongContainer";
import SideBar from "~/components/SideBar";
import { BotProvider, useBotContext } from "~/contexts/BotContext"
import { UserProvider, useUser } from "~/contexts/UserContext";


export function meta({}: Route.MetaArgs) {
	return [
		{ title: `${import.meta.env.VITE_APP_NAME}` },
		{ name: "description", content: `Welcome to ${import.meta.env.VITE_APP_NAME}!` },
	];
}


// Hooks ================================================================================

function useSongs() {
	const [songs, setSongs] = useState<YoutubeVideo[]>([])

	useEffect(() => {
		youtubeAPI.video.list().then(setSongs).catch(() => {})
	}, [])

	return songs
}

function usePlayback(guildID: string | null, videoId: string | null, volume: number) {
	const { botInChannel } = useBotContext()
	const [video, setVideo] = useState<YoutubeVideo | null>(null)
	const [videoLoading, setVideoLoading] = useState(false)
	const [playError, setPlayError] = useState<string | null>(null)

	useEffect(() => {
		if (!guildID || !videoId || !botInChannel) return

		setPlayError(null)
		setVideo(null)
		setVideoLoading(true)

		discordBotAPI.musicControl.play(guildID, videoId, 0, volume).catch((err: any) => {
			const message = err?.response?.data?.detail?.error
				|| (typeof err?.response?.data?.detail === 'string' ? err?.response?.data?.detail : null)
				|| "Failed to play track"
			setPlayError(message)
			setVideo(null)
			setVideoLoading(false)
		})

		youtubeAPI.video.retrieve(videoId).then(setVideo).catch(() => setVideo(null)).finally(() => setVideoLoading(false))

	}, [videoId, guildID, botInChannel])

	return { video, setVideo, videoLoading, setVideoLoading, playError }
}



// Page ================================================

function HomePage() {

	const [searchParams, setSearchParams] = useSearchParams()
	const videoId = searchParams.get("v")
	const volume = Number(searchParams.get("vol") ?? 1.0)
	const { guildID } = useBotContext()
	const { video, videoLoading, playError } = usePlayback(guildID, videoId, volume)

	function SongOnClick(item: YoutubeVideo) {
		setSearchParams(prev => { prev.set("v", item.youtube_id); return prev })
	}

	const songs = useSongs()
	return (
		<>
			<SideBar
				navbar={<Navbar SongSearchBarOnClick={SongOnClick} />}
				content={
					<div className="bg-zinc-900 p-5 rounded-md">
						<p className="text-xl font-bold mb-3">All Songs</p>
						<SongContainer songs={songs} onItemClick={SongOnClick} />
					</div>
				}
			/>
			<div className="fixed bottom-0 left-0 w-full z-50">
				<Musicbar video={video} loading={videoLoading} error={playError} />
			</div>
		</>
	)
}

function HomeContextWrapper() {
    const discordUser = useUser()
    return (
        <BotProvider discordUser={discordUser}>
            <HomePage />
        </BotProvider>
    )
}

export default function Home() {
    return (
        <UserProvider>
            <HomeContextWrapper />
        </UserProvider>
    )
}
