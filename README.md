![Build and Tests](https://github.com/9921622/DiscordYTStreamBot/actions/workflows/tests.yml/badge.svg?branch=main)
[![codecov discordbot](https://codecov.io/gh/9921622/DiscordYTStreamBot/branch/main/graph/badge.svg?flag=discordbot)](https://codecov.io/gh/9921622/DiscordYTStreamBot)
[![codecov dj-backend](https://codecov.io/gh/9921622/DiscordYTStreamBot/branch/main/graph/badge.svg?flag=dj-backend)](https://codecov.io/gh/9921622/DiscordYTStreamBot)

# DiscordYTStreamBot

![Homepage](assets/homepage.png)

A self-hosted Discord music bot with a web frontend. Users authenticate via Discord OAuth, and the bot streams YouTube audio in voice channels. The stack is fully containerised and served behind Nginx.

---

## Architecture

```
Browser
  └── Nginx (:80)
        ├── /          → React Frontend (:5173)
        ├── /dj/       → DJ Backend — Django + DRF (:8000)
        ├── /bot/      → Discord Bot — FastAPI + Uvicorn (:8080)
        └── /ws/       → Discord Bot WebSocket (:8080)
```

### Services

| Service | Stack | Port |
|---|---|---|
| `react-frontend` | React Router, Vite, TailwindCSS, DaisyUI | 5173 |
| `dj-backend` | Django 5, Django REST Framework, SimpleJWT | 8000 |
| `discordbot` | FastAPI, Uvicorn, discord.py, FFmpeg | 8080 |
| `nginx` | Nginx Alpine | 80 |

---

## Project Structure

```
DiscordYTStreamBot/
├── apps/
│   ├── discordbot/         # FastAPI + discord.py bot
│   ├── dj-backend/         # Django REST API
│   ├── react-frontend/     # React Router frontend
│   └── nginx/
│       ├── nginx.dev.conf
│       └── nginx.prod.conf
├── docker-compose.yml
├── docker-compose.dev.yml
```

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- A [Discord application](https://discord.com/developers/applications) with:
  - OAuth2 redirect URI registered
  - Privileged Gateway Intents enabled (Server Members, Message Content, Presence)

---

TODO:
....


