import { useEffect } from 'react'
import { useNavigate } from 'react-router'
import { backendAPI } from '~/api/backend-wrapper'


export default function AuthCallback() {
    const navigate = useNavigate()

    useEffect(() => {
        const params = new URLSearchParams(window.location.search)
        const access = params.get('access')
        const refresh = params.get('refresh')

        if (!access || !refresh) {
            window.location.href = backendAPI.discord.oauth2URI();
            return
        }

        localStorage.setItem('access', access)
        localStorage.setItem('refresh', refresh)

        navigate('/', { replace: true })
    }, [])

    return <p>Logging in...</p>
}
