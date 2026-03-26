import SongSearchbar from "./SongSearchbar";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";


function ProfileDropdown() {
  return (
    <div className="dropdown dropdown-end">
          <div
            tabIndex={0}
            role="button"
            className="btn btn-ghost btn-circle avatar"
          >
            <div className="w-10 rounded-full">
              <img
                alt="Profile"
                src="https://img.daisyui.com/images/stock/photo-1534528741775-53994a69daeb.webp"
              />
            </div>
          </div>
          <ul
            tabIndex={-1}
            className="menu menu-sm dropdown-content bg-base-100 rounded-box z-10 mt-3 w-52 p-2 shadow"
          >
            <li>
              <a className="justify-between">
                Profile
                <span className="badge">New</span>
              </a>
            </li>
            <li>
              <a>Settings</a>
            </li>
            <li>
              <a>Logout</a>
            </li>
          </ul>
        </div>
  );
}

export default function Navbar(
  { SongSearchBarOnClick } :
  { SongSearchBarOnClick : ( item : YoutubeVideo) => void; }) {

  function SongOnClick(item : YoutubeVideo) {
    console.log(item);
  }

  return (
    <nav className="text-white px-4 py-2 flex items-center relative shadow-md">

      <div className="flex items-center gap-4">
        <a className="text-2xl font-bold">Boombox</a>
      </div>

      <div className="absolute left-1/2 transform -translate-x-1/2">
        <SongSearchbar onItemClick={SongOnClick}/>
      </div>

      <div className="flex items-center gap-3 ml-auto">
        <ProfileDropdown />
      </div>
    </nav>
  );
}
