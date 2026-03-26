import type { Route } from "./+types/home";
import { useEffect, useState } from "react";

import { youtubeAPI } from "~/api/youtube/youtube-wrapper";
import type { YoutubeVideo } from "~/api/youtube/youtube-types";

import Navbar from "~/components/Navbar";
import Musicbar from "~/components/Musicbar";
import SongContainer from "~/components/SongContainer";

import { HomeIcon, GearIcon, MenuIcon } from "~/components/utilities/Icons";


export function meta({}: Route.MetaArgs) {
  return [
    { title: "Boombox" },
    { name: "description", content: "Welcome to Boombox!" },
  ];
}




function SideBarContent() {
  const sidebarItems = [
    { label: "Home", icon: MenuIcon },
    { label: "History", icon: GearIcon },
    { label: "Library", icon: GearIcon },
    { label: "Liked Songs", icon: GearIcon },
    { label: "Artists", icon: GearIcon },
    { label: "Albums", icon: GearIcon },
    { label: "Playlists", icon: GearIcon },
  ];
  return (
    <ul className="menu w-full grow">
      {sidebarItems.map((item) => (
        <li key={item.label}>
          <button
            className="is-drawer-close:tooltip is-drawer-close:tooltip-right"
            data-tip={item.label}
          >
            <item.icon />
            <span className="is-drawer-close:hidden">{item.label}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}

function SideBar({navbar, content, sidebar}: {navbar: React.ReactNode, content: React.ReactNode, sidebar: React.ReactNode}) {
  return (
    <div className="drawer lg:drawer-open">
        <input id="my-drawer-4" type="checkbox" className="drawer-toggle" />




        <div className="drawer-content">
          <nav className="navbar w-full bg-base-300">
            <label
              htmlFor="my-drawer-4"
              aria-label="open sidebar"
              className="btn btn-square btn-ghost"
            >
              <MenuIcon />
            </label>
            <div className="flex-1">
              {navbar}
            </div>
          </nav>



          {/* Page content */}
          <div className="p-4">


            {content}


          </div>
        </div>

        {/* Sidebar */}
        <div className="drawer-side is-drawer-close:overflow-visible">
          <label
            htmlFor="my-drawer-4"
            aria-label="close sidebar"
            className="drawer-overlay"
          ></label>

          <div className="flex min-h-full flex-col items-start bg-base-200 is-drawer-close:w-14 is-drawer-open:w-64">
            <div>&nbsp;</div>
            <div>&nbsp;</div>
            <div>&nbsp;</div>
            {sidebar}

          </div>
        </div>
      </div>
  );
}





function Main() {


  const [songs, setSongs] = useState<YoutubeVideo[]>([]);

  useEffect(() => {
      (async () => {
        let songs : YoutubeVideo[] = await youtubeAPI.video.list();
        setSongs(songs);
      })();
  }, []);


  return (
    <div>

        <div className="bg-zinc-900 p-5 rounded-md">
          <p className="text-xl font-bold mb-3">All Songs</p>
          <SongContainer songs={songs} />
        </div>

    </div>
  );
}




export default function Home() {


  return (
    <>
      <SideBar
        navbar={<Navbar />}
        content={<Main />}
        sidebar={<SideBarContent />}
      />

      <div className="fixed bottom-0 left-0 w-full z-50">
        <Musicbar />
      </div>
    </>
  );
}
