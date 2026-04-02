import { HomeIcon, GearIcon, MenuIcon } from "~/components/utilities/Icons";

function SideBarContent() {
	const sidebarItems = [
		{ label: "Home", icon: MenuIcon },
		{ label: "History", icon: GearIcon },
		{ label: "Library", icon: GearIcon },
		{ label: "Liked Songs", icon: GearIcon },
		{ label: "Artists", icon: GearIcon },
		{ label: "Albums", icon: GearIcon },
		{ label: "Playlists", icon: GearIcon },
	]

	return (
		<ul className="menu w-full grow">
			{sidebarItems.map((item) => (
				<li key={item.label}>
					<button className="is-drawer-close:tooltip is-drawer-close:tooltip-right" data-tip={item.label}>
						<item.icon />
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
			<div className="drawer-content">
				<nav className="sticky top-0 z-50 navbar w-full bg-base-300">
					<label htmlFor="my-drawer-4" aria-label="open sidebar" className="btn btn-square btn-ghost">
						<MenuIcon />
					</label>
					<div className="flex-1">{navbar}</div>
				</nav>
				<div className="p-4">{content}</div>
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
