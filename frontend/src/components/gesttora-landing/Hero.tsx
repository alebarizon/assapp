import { Link } from "react-router-dom";
import { gesttoraLanding } from "@/content/gesttoraLanding";

export function Hero() {
  const { hero } = gesttoraLanding;

  return (
    <section id="home" className="gt-hero">
      <div
        className="gt-hero__bg"
        style={{ backgroundImage: `url(${hero.backgroundImage})` }}
        role="img"
        aria-label="Ambiente de evento científico"
      />
      <div className="gt-hero__veil" />

      <div className="gt-hero__content">
        <p className="gt-hero__brand">{hero.brand}</p>
        <h1 className="gt-hero__headline">{hero.headline}</h1>
        <p className="gt-hero__subtitle">{hero.subtitle}</p>
        <div className="gt-hero__ctas">
          <Link to={hero.primaryCta.url} className="gt-btn gt-btn--accent">
            {hero.primaryCta.label}
          </Link>
          <Link to={hero.secondaryCta.url} className="gt-btn gt-btn--outline">
            {hero.secondaryCta.label}
          </Link>
        </div>
      </div>
    </section>
  );
}
