import { Link } from "react-router-dom";
import { gesttoraLanding } from "@/content/gesttoraLanding";

interface NavbarProps {
  scrolled?: boolean;
}

export function Navbar({ scrolled = false }: NavbarProps) {
  const { brand, nav } = gesttoraLanding;

  return (
    <nav className={`gt-nav${scrolled ? " gt-nav--scrolled" : ""}`}>
      <div className="gt-nav__inner">
        <a href="#home" className="gt-nav__brand">
          {brand}
        </a>

        <div className="gt-nav__links">
          {nav.links.map((link) => (
            <a key={link.href} href={link.href} className="gt-nav__link">
              {link.label}
            </a>
          ))}
        </div>

        <div className="gt-nav__actions">
          <Link to={nav.loginUrl} className="gt-btn gt-btn--ghost">
            {nav.loginLabel}
          </Link>
          <Link to={nav.signupUrl} className="gt-btn gt-nav__cta">
            {nav.signupLabel}
          </Link>
        </div>
      </div>
    </nav>
  );
}
