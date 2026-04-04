import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig, loadEnv } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [tailwindcss(), reactRouter(), tsconfigPaths()],
    server: {
      host: '0.0.0.0',
      ...(mode === 'development' && !env.DOCKER && {
        proxy: {
          '/dj': {
            target: env.DJ_BACKEND_URL,
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/dj/, ''),
          },
          '/bot': {
            target: env.DISCORD_BOT_URL,
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/bot/, ''),
          },
          '/ws': {
            target: env.DISCORD_BOT_WS,
            ws: true,
          },
        }
      }),
    },
  };
});
