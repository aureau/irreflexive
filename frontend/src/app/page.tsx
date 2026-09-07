import { Navbar } from "@/components/site/Navbar";
import { TrendingSection } from "@/components/site/TrendingSection";
import { ExploreLatest } from "@/components/site/ExploreLatest";
import { MissionBand } from "@/components/site/MissionBand";
import { Footer } from "@/components/site/Footer";

export default function HomePage() {
  return (
    <>
      <Navbar />

      <main>
        {/*
          hero video preserved per spec — kept mounted but hidden until a real
          demo clip is dropped into /public. swap `hidden` for sizing classes
          and uncomment the <source> when ready.
        */}
        <video
          id="hero-demo-video"
          className="hidden"
          aria-hidden="true"
          muted
          playsInline
          loop
        >
          {/* add `poster="/demo-poster.jpg"` and a <source /> when the demo clip lands */}
          {/* <source src="/demo.mp4" type="video/mp4" /> */}
        </video>

        <TrendingSection />
        <ExploreLatest />
        <MissionBand />
      </main>

      <Footer />
    </>
  );
}
