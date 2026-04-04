import { Clock, Book, Heart, User, Disc, List } from "lucide-react";


export default function SideBarContent() {
	const sidebarItems = [
		{ label: "History", icon: Clock },
		{ label: "Library", icon: Book },
		{ label: "Liked Songs", icon: Heart },
		{ label: "Artists", icon: User },
		{ label: "Albums", icon: Disc },
		{ label: "Playlists", icon: List },
	];

    return (
        <ul className="menu w-full grow">
            {sidebarItems.map((item) => (
                <li key={item.label}>
                    <button>
                        <item.icon className="w-4 h-4 text-white" />
                        <span>{item.label}</span>
                    </button>
                </li>
            ))}
        </ul>
    );
}
