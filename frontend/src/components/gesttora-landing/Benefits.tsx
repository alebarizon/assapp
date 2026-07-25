import { Building2, Clock, Shield, Users } from "lucide-react";
import { gesttoraLanding } from "@/content/gesttoraLanding";

const iconMap = {
  Clock,
  Shield,
  Users,
  Building2,
} as const;

export function Benefits() {
  const { benefits } = gesttoraLanding;

  return (
    <section id="benefits" className="gt-section gt-benefits">
      <div className="gt-container">
        <h2 className="gt-section__title gt-section__title--center">{benefits.title}</h2>
        <div className="gt-benefits__grid">
          {benefits.items.map((item) => {
            const Icon = iconMap[item.icon];
            return (
              <article key={item.title} className="gt-benefit">
                <div className="gt-benefit__icon">
                  <Icon aria-hidden />
                </div>
                <h3 className="gt-benefit__title">{item.title}</h3>
                <p className="gt-benefit__desc">{item.description}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
