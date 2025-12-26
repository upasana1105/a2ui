import { AppConfig } from "./types.js";

export const config: AppConfig = {
  key: "real_estate",
  title: "Real Estate Agent",
  heroImage: "/hero.png",
  heroImageDark: "/hero-dark.png",
  background: `radial-gradient(
    at 0% 0%,
    light-dark(rgba(161, 196, 253, 0.3), rgba(6, 182, 212, 0.15)) 0px,
    transparent 50%
  ),
  radial-gradient(
    at 100% 0%,
    light-dark(rgba(255, 192, 203, 0.3), rgba(236, 72, 153, 0.15)) 0px,
    transparent 50%
  ),
  linear-gradient(
    120deg,
    light-dark(#f8fafc, #020617) 0%,
    light-dark(#f1f5f9, #0f172a) 100%
  )`,
  placeholder: "Find me houses in Palo Alto near a gym...",
  loadingText: [
    "Scouting the neighborhood...",
    "Finding the best deals...",
    "Consulting local experts...",
    "Hang tight...",
  ],
  serverUrl: "http://localhost:10003",
};
