import { type RouteConfig, index, route, layout } from "@react-router/dev/routes";

export default [
    layout("routes/layout.tsx", [
        index("routes/home.tsx"),
    ]),

    route("/auth/callback", "routes/AuthCallback.tsx"),
    route("/login", "routes/login.tsx"),
] satisfies RouteConfig;
