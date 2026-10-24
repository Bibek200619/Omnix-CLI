import HomePage from "@/components/marketing/home-page";
import { fetchReleaseState } from "@/lib/github";

export const revalidate = 3600;

export default async function Home() {
  const releaseState = await fetchReleaseState();
  return <HomePage releaseState={releaseState} />;
}
