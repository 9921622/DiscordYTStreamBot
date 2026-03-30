import axios from "axios"
import { backendAPI } from "./api/backend-wrapper"


axios.interceptors.response.use(
    response => response,
    async error => {
        const original = error.config
        if (error.response?.status === 401 && !original._retry) {
            original._retry = true
            try {
                const refresh_token_uri = backendAPI.refresh_token_uri();
                const { data } = await axios.post(refresh_token_uri, {
                    refresh: localStorage.getItem('refresh')
                })
                localStorage.setItem('access', data.access)
                original.headers['Authorization'] = `Bearer ${data.access}`
                return axios(original)
            } catch {
                localStorage.removeItem('access')
                localStorage.removeItem('refresh')
                window.location.href = '/login'
            }
        }
        return Promise.reject(error)
    }
)
