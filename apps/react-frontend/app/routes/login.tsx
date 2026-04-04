// routes/login.tsx
import { backendAPI } from '~/api/backend-wrapper'

export default function Login() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-[#1e1f22] relative overflow-hidden font-['Nunito',sans-serif]">
            {/* Atmospheric blobs */}
            <div className="absolute w-80 h-80 rounded-full bg-[#5865f2] opacity-15 blur-[60px] -top-20 -left-16 pointer-events-none" />
            <div className="absolute w-60 h-60 rounded-full bg-[#5865f2] opacity-15 blur-[60px] -bottom-10 -right-10 pointer-events-none" />

            <div className="relative w-full max-w-sm mx-4 bg-[#313338] rounded-2xl border border-white/[0.06] shadow-[0_8px_48px_rgba(0,0,0,0.5),0_0_0_1px_rgba(88,101,242,0.12)] px-9 py-10 animate-[cardIn_0.45s_cubic-bezier(0.22,1,0.36,1)_both]">

                {/* Secure badge */}
                <div className="flex justify-center mb-1">
                    <span className="inline-flex items-center gap-1.5 bg-[rgba(88,101,242,0.15)] text-[#949ba4] text-[11.5px] font-semibold rounded-full px-3 py-0.5 tracking-wide">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#5865f2] inline-block" />
                        Secure login
                    </span>
                </div>

                {/* Logo */}
                <div className="flex items-center justify-center w-16 h-16 bg-[#5865f2] rounded-full mx-auto my-5 animate-[logoIn_0.5s_0.1s_cubic-bezier(0.22,1,0.36,1)_both]">
                    <img
                        src="/discord_logo.png"
                        alt="Discord"
                        className="w-10 h-10"
                    />
                </div>

                <h1 className="text-white text-[22px] font-extrabold text-center tracking-tight mb-1.5">Welcome back</h1>
                <p className="text-[#949ba4] text-[13.5px] text-center leading-relaxed mb-8">
                    Continue to your account via Discord OAuth2.<br />
                    Fast, secure, no password needed.
                </p>

                <div className="h-px bg-white/[0.07] mb-6" />

                <a
                    href={backendAPI.discord.oauth2URI()}
                    className="flex items-center justify-center gap-2.5 w-full py-3.5 bg-[#5865f2] hover:bg-[#4752c4] active:scale-[0.98] text-white font-bold text-[15px] rounded-xl transition-all duration-150 hover:-translate-y-px tracking-wide"
                >
                    <svg width="20" height="20" viewBox="0 0 71 55" fill="none">
                        <path d="M60.1 4.9A58.5 58.5 0 0 0 45.5.5a40.7 40.7 0 0 0-1.8 3.7 54.1 54.1 0 0 0-16.3 0A40.7 40.7 0 0 0 25.6.5a58.4 58.4 0 0 0-14.7 4.4C1.6 18 -1 30.8.3 43.4a58.9 58.9 0 0 0 18 9.1 43.3 43.3 0 0 0 3.7-6 38.3 38.3 0 0 1-5.9-2.8l1.4-1.1a42 42 0 0 0 35.8 0l1.4 1.1a38.4 38.4 0 0 1-5.9 2.8 43.1 43.1 0 0 0 3.7 6 58.7 58.7 0 0 0 17.9-9.1C72.3 28.9 69 16.2 60.1 4.9ZM23.8 36c-3.5 0-6.4-3.2-6.4-7.2s2.8-7.2 6.4-7.2 6.5 3.2 6.4 7.2c0 4-2.9 7.2-6.4 7.2Zm23.4 0c-3.5 0-6.4-3.2-6.4-7.2s2.8-7.2 6.4-7.2 6.5 3.2 6.4 7.2c0 4-2.8 7.2-6.4 7.2Z" fill="white"/>
                    </svg>
                    Continue with Discord
                </a>

                <p className="mt-5 text-center text-[12px] text-[#5c6069] leading-relaxed">
                    By continuing, you agree to our{' '}
                    <a href="#" className="text-[#5865f2] hover:underline">Terms of Service</a>{' '}
                    and{' '}
                    <a href="#" className="text-[#5865f2] hover:underline">Privacy Policy</a>.
                </p>
            </div>
        </div>
    )
}
