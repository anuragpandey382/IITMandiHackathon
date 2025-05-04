import TopMovie from "@/components/home/top-movie";
import FilmSection from "@/components/home/playlist-section";
import Footer from "@/components/root/footer";
import HistorySection from "@/components/home/history-section";

export default function HomePage() {
  return (
    <main className="relative z-0 h-full min-h-screen w-full overflow-x-clip bg-zinc-950">
      <TopMovie />
      <FilmSection />
      <HistorySection />
      {/*<FilmSection />*/}
      {/*<FilmSection />*/}

      <Footer />
    </main>
  );
}
