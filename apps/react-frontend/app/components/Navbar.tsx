import SongSearchbar from "./SongSearchbar";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";
import { discordBotAPI } from "~/api/discord/discord-wrapper";
import { backendAPI } from "~/api/backend-wrapper";
import type { DiscordUser } from "~/api/backend-types";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

function ProfileDropdown({ profile } : { profile? : DiscordUser }) {
  const navigate = useNavigate()

  const handleLogout = () => {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    navigate('/login')
  }

  if (!profile) return (
    <button className="btn btn-sm btn-primary" onClick={() => navigate('/login')}>
      Login
    </button>
  )

  return (
    <div className="dropdown dropdown-end">
      <div tabIndex={0} role="button" className="btn btn-ghost btn-circle avatar">
        <div className="w-10 rounded-full">
          {profile && <img alt="Profile" src={profile.avatar} />}
        </div>
      </div>
      <ul tabIndex={-1} className="menu menu-sm dropdown-content bg-base-100 rounded-box z-10 mt-3 w-52 p-2 shadow">
        <li><a className="justify-between">Profile<span className="badge">New</span></a></li>
        <li><a>Settings</a></li>
        <li><a onClick={handleLogout}>Logout</a></li>
      </ul>
    </div>
  )
}


function JoinChannel({ discordUser }: { discordUser?: DiscordUser }) {
  const [loading, setLoading] = useState(false)
  const [inVC, setInVC] = useState<boolean | null>(null)
  const [botInChannel, setBotInChannel] = useState(false)

  useEffect(() => {
    if (!discordUser) return
    discordBotAPI.voice.get_user_vc(discordUser.discord_id).then(data => {
      setInVC(!!data.channel_id)
      setBotInChannel(data.bot_in_channel ?? false)
    })
  }, [discordUser])

  const handleJoin = async () => {
    if (!discordUser) return
    setLoading(true)
    await discordBotAPI.voice.join_user_vc(discordUser.discord_id)
    setBotInChannel(true)
    setLoading(false)
  }

  if (inVC === null) return null

  if (!inVC) return (
    <div className="tooltip tooltip-bottom" data-tip="You're not in a voice channel">
      <button className="btn btn-sm btn-disabled gap-2">
        <span>🔇</span> Not in VC
      </button>
    </div>
  )

  if (botInChannel) return (
    <div className="badge badge-success gap-1 p-3">
      <span>🔊</span> In your channel
    </div>
  )

  return (
    <button className="btn btn-sm btn-primary gap-2" onClick={handleJoin} disabled={loading}>
      {loading ? <span className="loading loading-spinner loading-xs" /> : <span>🎙️</span>}
      Join my VC
    </button>
  )
}

export default function Navbar(
  { SongSearchBarOnClick, discordUser } :
  { SongSearchBarOnClick : ( item : YoutubeVideo) => void;
    discordUser? : DiscordUser;
   }) {


  return (
    <nav className="text-white px-4 py-2 flex items-center relative shadow-md z-50">

      <div className="flex items-center gap-4">
        <a className="text-2xl font-bold">{import.meta.env.VITE_APP_NAME}</a>
      </div>

      <div className="absolute left-1/2 transform -translate-x-1/2">
        <SongSearchbar onItemClick={SongSearchBarOnClick}/>
      </div>

      <div className="flex items-center gap-3 ml-auto">
        <JoinChannel discordUser={discordUser} />
        <ProfileDropdown profile={discordUser}/>
      </div>
    </nav>
  );
}
