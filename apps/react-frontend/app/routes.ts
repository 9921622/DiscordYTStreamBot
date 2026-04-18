import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
    index("routes/layout.tsx"),
    route("/auth/callback", "routes/AuthCallback.tsx"),
    route("/login", "routes/login.tsx"),
] satisfies RouteConfig;
