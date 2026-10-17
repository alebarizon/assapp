import type { ReactNode } from "react";
import { BookMarked } from "lucide-react";
import "@/pages/Login.css";

export default function AuthShell({ title, subtitle, children }: { title: string; subtitle?: ReactNode; children: ReactNode }) {
  return (
    <div className="login-page">
      <aside className="login-hero">
        <div className="login-hero-fallback" aria-hidden />
        <div className="login-hero-overlay" />
        <div className="login-hero-content">
          <div className="login-hero-brand">
            <div className="login-hero-brand-icon">
              <BookMarked className="login-hero-brand-leaf" />
            </div>
            <span className="login-hero-brand-name">Gesttora</span>
          </div>
        </div>
      </aside>
      <div className="login-form-panel">
        <div className="login-form-content">
          <div className="login-mobile-brand">
            <div className="login-mobile-brand-icon">
              <BookMarked className="login-mobile-brand-leaf" />
            </div>
            <span className="login-mobile-brand-name">Gesttora</span>
          </div>
          <h2 className="login-form-title">{title}</h2>
          {subtitle && <p className="login-form-subtitle">{subtitle}</p>}
          {children}
        </div>
      </div>
    </div>
  );
}
