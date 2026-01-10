import { Navigate } from "@solidjs/router";

// Redirect to /me/today for backwards compatibility
export default function Home() {
  return <Navigate href="/me/today" />;
}
