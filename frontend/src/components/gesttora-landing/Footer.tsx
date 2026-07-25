import { Link } from "react-router-dom";
import { gesttoraLanding } from "@/content/gesttoraLanding";

export function Footer() {
  const { brand, domain, footer } = gesttoraLanding;

  return (
    <footer className="gt-footer">
      <div className="gt-container gt-footer__grid">
        <div className="gt-footer__brand">
          <p className="gt-footer__name">{brand}</p>
          <p className="gt-footer__tagline">{footer.tagline}</p>
          <p className="gt-footer__domain">{domain}</p>
        </div>

        <div>
          <p className="gt-footer__heading">Produto</p>
          <ul className="gt-footer__list">
            {footer.productLinks.map((link) =>
              link.href.startsWith("/") ? (
                <li key={link.label}>
                  <Link to={link.href}>{link.label}</Link>
                </li>
              ) : (
                <li key={link.label}>
                  <a href={link.href}>{link.label}</a>
                </li>
              )
            )}
          </ul>
        </div>

        <div>
          <p className="gt-footer__heading">Legal</p>
          <ul className="gt-footer__list">
            {footer.legalLinks.map((link) => (
              <li key={link.label}>
                <a href={link.href}>{link.label}</a>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="gt-footer__bottom">
        <p>{footer.copyright}</p>
      </div>
    </footer>
  );
}
