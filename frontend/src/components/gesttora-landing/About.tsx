import { CheckCircle } from "lucide-react";
import { gesttoraLanding } from "@/content/gesttoraLanding";

export function About() {
  const { about } = gesttoraLanding;

  return (
    <section id="about" className="gt-section gt-about">
      <div className="gt-container gt-about__grid">
        <div className="gt-about__visual" aria-hidden="true">
          <div className="gt-about__panel">
            <span className="gt-about__panel-label">Continuidade</span>
            <span className="gt-about__panel-line">Mandato N</span>
            <span className="gt-about__panel-arrow">→</span>
            <span className="gt-about__panel-line">Mandato N+1</span>
            <span className="gt-about__panel-note">memória · onboarding · eventos</span>
          </div>
        </div>

        <div className="gt-about__copy">
          <h2 className="gt-section__title">{about.title}</h2>
          <p className="gt-section__lead">{about.description}</p>
          <ul className="gt-about__points">
            {about.points.map((point) => (
              <li key={point}>
                <CheckCircle className="gt-about__check" aria-hidden />
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
