import { NavLink } from "react-router";
import { Clock, Book, Heart, User, Disc, List, Home } from "lucide-react";

export default function SideBarContent() {
	const sidebarItems = [
        { label: "Home", icon: Home, href: "/" },
		{ label: "History", icon: Clock, href: "/not-implemented" },
		{ label: "Library", icon: Book, href: "/not-implemented" },
		{ label: "Liked Songs", icon: Heart, href: "/not-implemented" },
		{ label: "Artists", icon: User, href: "/not-implemented" },
		{ label: "Albums", icon: Disc, href: "/not-implemented" },
		{ label: "Playlists", icon: List, href: "/not-implemented" },
	];

    return (
        <ul className="menu w-full grow">
            {sidebarItems.map((item) => (
                <li key={item.label}>
                    {item.href ? (
                        <NavLink
                            to={item.href}
                            end
                            className={({ isActive }) => isActive ? "active" : ""}
                        >
                            <item.icon className="w-4 h-4 text-white" />
                            <span>{item.label}</span>
                        </NavLink>
                    ) : (
                        <button>
                            <item.icon className="w-4 h-4 text-white" />
                            <span>{item.label}</span>
                        </button>
                    )}
                </li>
            ))}
        </ul>
    );
}
