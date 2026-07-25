import { BookOpen, Calendar, RefreshCw } from "lucide-react";
import { gesttoraLanding } from "@/content/gesttoraLanding";

const iconMap = {
  RefreshCw,
  BookOpen,
  Calendar,
} as const;

export function Features() {
  const { features } = gesttoraLanding;

  return (
    <section id="features" className="gt-section gt-features">
      <div className="gt-container">
        <div className="gt-features__intro">
          <p className="gt-eyebrow">{features.eyebrow}</p>
          <h2 className="gt-section__title">{features.title}</h2>
          <p className="gt-section__lead">{features.description}</p>
        </div>

        <div className="gt-features__list">
          {features.items.map((item, index) => {
            const Icon = iconMap[item.icon];
            return (
              <article
                key={item.title}
                className="gt-feature"
                style={{ animationDelay: `${0.08 * (index + 1)}s` }}
              >
                <div className="gt-feature__icon">
                  <Icon aria-hidden />
                </div>
                <div className="gt-feature__body">
                  <h3 className="gt-feature__title">{item.title}</h3>
                  <p className="gt-feature__desc">{item.description}</p>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
