import { useEffect } from "react";
import { useLocation } from "react-router-dom";

// Só páginas da própria Gesttora: sites das associações (/site) e painel (/app) não são medidos,
// e outras rotas levam tokens na URL (definir senha, descadastro, formulários).
const ROTAS_MEDIDAS = new Set(["/", "/login", "/signup"]);

const GA_ID = import.meta.env.VITE_GA_ID ?? "";

type Gtag = (...args: unknown[]) => void;

declare global {
  interface Window {
    dataLayer?: unknown[];
    gtag?: Gtag;
    [chave: `ga-disable-${string}`]: boolean | undefined;
  }
}

function carregar(): Gtag {
  if (window.gtag) return window.gtag;
  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag() {
    // gtag.js exige o objeto `arguments`, não um array.
    // eslint-disable-next-line prefer-rest-params
    window.dataLayer!.push(arguments);
  };
  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
  document.head.appendChild(script);
  window.gtag("js", new Date());
  window.gtag("config", GA_ID, { send_page_view: false });
  return window.gtag;
}

export default function GoogleAnalytics() {
  const { pathname } = useLocation();

  useEffect(() => {
    if (!GA_ID) return;
    const medir = ROTAS_MEDIDAS.has(pathname);
    window[`ga-disable-${GA_ID}`] = !medir;
    if (!medir) return;
    carregar()("event", "page_view", {
      page_location: window.location.origin + pathname,
      page_path: pathname,
      page_title: document.title,
    });
  }, [pathname]);

  return null;
}
