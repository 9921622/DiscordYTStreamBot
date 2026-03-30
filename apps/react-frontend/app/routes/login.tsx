// routes/login.tsx
import { useEffect } from 'react'
import { backendAPI } from '~/api/backend-wrapper'

export default function Login() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-base-200">
            <div className="card w-96 bg-base-100 shadow-xl">
                <div className="card-body items-center text-center gap-6">
                    <div className="flex flex-col items-center gap-2">
                        <img
                            src="https://assets-global.website-files.com/6257adef93867e50d84d30e2/636e0a6a49cf127bf92de1e2_icon_clyde_blurple_RGB.png"
                            alt="Discord"
                            className="w-16 h-16"
                        />
                        <h2 className="card-title text-2xl">Welcome</h2>
                        <p className="text-base-content/60 text-sm">Sign in with your Discord account to continue</p>
                    </div>

                    <a
                        href={backendAPI.discord.oauth2URI()}
                        className="btn btn-primary w-full gap-2"
                    >
                        Login with Discord
                    </a>
                </div>
            </div>
        </div>
    )
}
