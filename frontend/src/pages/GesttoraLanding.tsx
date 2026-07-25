import { useEffect, useState } from "react";
import {
  About,
  Benefits,
  Contact,
  Features,
  Footer,
  Hero,
  Navbar,
} from "@/components/gesttora-landing";
import "./GesttoraLanding.css";

/**
 * Landing pública do SaaS Gesttora (futuro gesttora.online).
 * Conteúdo estático — CMS do tenant e adminpanel ficam para depois.
 */
export default function GesttoraLanding() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    document.title = "Gesttora — Gestão institucional para associações científicas";

    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="gesttora-landing">
      <Navbar scrolled={scrolled} />
      <main>
        <Hero />
        <About />
        <Features />
        <Benefits />
        <Contact />
      </main>
      <Footer />
    </div>
  );
}
