import { useState } from "react";
import { Shield, Music, ChevronDown, ChevronUp, } from "lucide-react";

const MUSIC_PERMISSIONS = [
    { key: "pause",         label: "Pause / Resume",    description: "Can pause and resume playback" },
    { key: "skip",          label: "Skip",              description: "Can skip to the next track" },
    { key: "seek",          label: "Seek",              description: "Can scrub the progress bar" },
    { key: "queue_add",     label: "Add to queue",      description: "Can add songs to the queue" },
    { key: "queue_remove",  label: "Remove from queue", description: "Can remove songs from the queue" },
    { key: "queue_move",    label: "Reorder queue",     description: "Can drag and reorder queue items" },
    { key: "volume",        label: "Volume control",    description: "Can adjust the playback volume" },
    { key: "clear_queue",   label: "Clear queue",       description: "Can clear the entire queue" },
];

const MOCK_SERVERS = [
    { id: "1", name: "My Awesome Server" },
    { id: "2", name: "Gaming Lounge" },
    { id: "3", name: "Music Club" },
];

const MOCK_ROLES = [
    { id: "1", name: "Admin",    color: "#f87171" },
    { id: "2", name: "DJ",       color: "#a78bfa" },
    { id: "3", name: "Member",   color: "#60a5fa" },
    { id: "4", name: "@everyone",color: "#9ca3af" },
];

type Permissions = Record<string, Record<string, boolean>>;

function buildDefaultPermissions(): Permissions {
    const defaults: Permissions = {};
    for (const role of MOCK_ROLES) {
        defaults[role.id] = {};
        for (const perm of MUSIC_PERMISSIONS) {
            defaults[role.id][perm.key] = role.name === "Admin" || role.name === "DJ";
        }
    }
    return defaults;
}

function RoleCard({
            role,
            permissions,
            onChange,
        }: {
            role: typeof MOCK_ROLES[0];
            permissions: Record<string, boolean>;
            onChange: (key: string, value: boolean) => void;
        }) {
    const [open, setOpen] = useState(false);
    const enabledCount = Object.values(permissions).filter(Boolean).length;

    return (
        <div className="bg-base-200 border border-base-content/10 rounded-xl overflow-hidden">
            <button
                className="w-full flex items-center justify-between px-5 py-4 hover:bg-base-300/50 transition-colors"
                onClick={() => setOpen(o => !o)}
            >
                <div className="flex items-center gap-3">
                    <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: role.color }}
                    />
                    <span className="font-medium text-sm">{role.name}</span>
                    <span className="text-xs text-base-content/40 bg-base-300 px-2 py-0.5 rounded-full">
                        {enabledCount} / {MUSIC_PERMISSIONS.length}
                    </span>
                </div>
                {open ? <ChevronUp size={15} className="text-base-content/40" /> : <ChevronDown size={15} className="text-base-content/40" />}
            </button>

            {open && (
                <div className="border-t border-base-content/10 divide-y divide-base-content/5">
                    {MUSIC_PERMISSIONS.map(perm => (
                        <div key={perm.key} className="flex items-center justify-between px-5 py-3 hover:bg-base-300/30 transition-colors">
                            <div>
                                <p className="text-sm font-medium">{perm.label}</p>
                                <p className="text-xs text-base-content/40 mt-0.5">{perm.description}</p>
                            </div>
                            <input
                                type="checkbox"
                                className="toggle toggle-sm toggle-primary"
                                checked={permissions[perm.key] ?? false}
                                onChange={e => onChange(perm.key, e.target.checked)}
                            />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default function Settings() {
    const [selectedServer, setSelectedServer] = useState(MOCK_SERVERS[0].id);
    const [permissions, setPermissions] = useState<Permissions>(buildDefaultPermissions);

    function handlePermissionChange(roleId: string, key: string, value: boolean) {
        setPermissions(prev => ({
            ...prev,
            [roleId]: { ...prev[roleId], [key]: value },
        }));
    }

    return (
        <div className="p-6 max-w-2xl">
            <header className="mb-8">
                <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
                <p className="text-base-content/40 text-sm mt-0.5">Manage your server and permissions</p>
            </header>

            {/* Server select */}
            <section className="mb-8">
                <div className="flex items-center gap-2 mb-3">
                    <Shield size={15} className="text-base-content/50" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-base-content/50">Server</h2>
                </div>
                <div className="bg-base-200 border border-base-content/10 rounded-xl px-5 py-4">
                    <label className="text-sm text-base-content/60 mb-1.5 block">Active server</label>
                    <select
                        className="select select-bordered w-full max-w-sm bg-base-300 border-base-content/10 text-sm"
                        value={selectedServer}
                        onChange={e => setSelectedServer(e.target.value)}
                    >
                        {MOCK_SERVERS.map(s => (
                            <option key={s.id} value={s.id}>{s.name}</option>
                        ))}
                    </select>
                </div>
            </section>

            {/* Role permissions */}
            <section>
                <div className="flex items-center gap-2 mb-3">
                    <Music size={15} className="text-base-content/50" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-base-content/50">Music permissions</h2>
                </div>
                <div className="flex flex-col gap-2">
                    {MOCK_ROLES.map(role => (
                        <RoleCard
                            key={role.id}
                            role={role}
                            permissions={permissions[role.id]}
                            onChange={(key, value) => handlePermissionChange(role.id, key, value)}
                        />
                    ))}
                </div>
            </section>
        </div>
    );
}
