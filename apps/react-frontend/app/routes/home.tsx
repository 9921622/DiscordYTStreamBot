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



export function meta({}: Route.MetaArgs) {
	return [
		{ title: `${import.meta.env.VITE_APP_NAME}` },
		{ name: "description", content: `Welcome to ${import.meta.env.VITE_APP_NAME}!` },
	];
}


// Hooks ================================================================================

function useDiscordUser() {
	const [discordUser, setDiscordUser] = useState<DiscordUser>()

	useEffect(() => {
		backendAPI.discord.get_user().then(setDiscordUser).catch(() => {})
	}, [])

	return discordUser
}

function useGuildID(discordUser?: DiscordUser) {
	const [guildID, setGuildID] = useState<string | null>(null)

	useEffect(() => {
		if (!discordUser) return
		discordBotAPI.voice.get_user_vc(discordUser.discord_id).then(data => {
			if (data.guild_id) setGuildID(data.guild_id)
		})
	}, [discordUser])

	return guildID
}

function useSongs() {
	const [songs, setSongs] = useState<YoutubeVideo[]>([])

	useEffect(() => {
		youtubeAPI.video.list().then(setSongs).catch(() => {})
	}, [])

	return songs
}

function usePlayback(guildID: string | null, videoId: string | null, searchParams: URLSearchParams) {
	const [video, setVideo] = useState<YoutubeVideo | null>(null)
	const [videoLoading, setVideoLoading] = useState(false)
	const [playError, setPlayError] = useState<string | null>(null)

	useEffect(() => {
		if (!guildID || !videoId) return

		setPlayError(null)

		const volume_level = Number(searchParams.get("vol") ?? 1.0);

		(async () => {
			try {
				await discordBotAPI.musicControl.play(guildID, videoId, 0, volume_level)
			} catch (err: any) {
				setPlayError(err?.response?.data?.detail || "Failed to play track")
				setVideo(null)
				setVideoLoading(false)
			}
		})();

		(async () => {
			setVideoLoading(true)
			try {
				setVideo(await youtubeAPI.video.retrieve(videoId))
			} catch {
				setVideo(null)
			} finally {
				setVideoLoading(false)
			}
		})()
	}, [videoId, guildID])

	return { video, setVideo, videoLoading, setVideoLoading, playError }
}



// Page ================================================

export default function Home() {
	const [searchParams, setSearchParams] = useSearchParams()
	const videoId = searchParams.get("v")

	const discordUser = useDiscordUser()
	const guildID = useGuildID(discordUser)
	const songs = useSongs()
	const { video, videoLoading, playError } = usePlayback(guildID, videoId, searchParams)

	function SongOnClick(item: YoutubeVideo) {
		setSearchParams(prev => { prev.set("v", item.youtube_id); return prev })
	}

	return (
		<>
			<SideBar
				navbar={<Navbar SongSearchBarOnClick={SongOnClick} discordUser={discordUser} />}
				content={
					<div className="bg-zinc-900 p-5 rounded-md">
						<p className="text-xl font-bold mb-3">All Songs</p>
						<SongContainer songs={songs} onItemClick={SongOnClick} />
					</div>
				}
			/>
			<div className="fixed bottom-0 left-0 w-full z-50">
				<Musicbar guildID={guildID} video={video} loading={videoLoading} error={playError} />
			</div>
		</>
	)
}
