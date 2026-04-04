import { Clock, Book, Heart, User, Disc, List, Menu } from "lucide-react";

function SideBarContent() {
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
					<button className="is-drawer-close:tooltip is-drawer-close:tooltip-right" data-tip={item.label}>
						<item.icon className="w-4 h-4 text-white"/>
						<span className="is-drawer-close:hidden">{item.label}</span>
					</button>
				</li>
			))}
		</ul>
	)
}

export default function SideBar({ navbar, content }: { navbar: React.ReactNode; content: React.ReactNode }) {
	return (
		<div className="drawer lg:drawer-open">
			<input id="my-drawer-4" type="checkbox" className="drawer-toggle" />
			<div className="drawer-content flex flex-col h-screen">
				<nav className="sticky top-0 z-50 navbar w-full bg-base-300 flex-shrink-0">
					<label htmlFor="my-drawer-4" aria-label="open sidebar" className="btn btn-square btn-ghost">
						<Menu className="w-4 h-4 text-white" />
					</label>
					<div className="flex-1">{navbar}</div>
				</nav>
				<div className="flex-1 overflow-hidden p-4 pb-[calc(var(--musicbar-height,80px)+50px)]">
					{content}
				</div>
			</div>

			<div className="drawer-side is-drawer-close:overflow-visible">
				<label htmlFor="my-drawer-4" aria-label="close sidebar" className="drawer-overlay" />
				<div className="flex min-h-full flex-col items-start bg-base-200 is-drawer-close:w-14 is-drawer-open:w-64">
					<div>&nbsp;</div>
					<div>&nbsp;</div>
					<div>&nbsp;</div>
					<SideBarContent />
				</div>
			</div>

		</div>
	)
}
