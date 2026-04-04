import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig(({ mode }) => ({
  plugins: [tailwindcss(), reactRouter(), tsconfigPaths()],
  server: {
    host: '0.0.0.0',
    ...(mode === 'development' && !process.env.DOCKER && {
      proxy: {
        '/dj': {
          target: process.env.DJ_BACKEND_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/dj/, ''),
        },
        '/bot': {
          target: process.env.DISCORD_BOT_URL,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/bot/, ''),
        },
        '/ws': {
          target: process.env.DISCORD_BOT_WS,
          ws: true,
        },
      }
    }),
  },
}));
