import { useEffect, useState } from "react";
import { getPublicSite } from "@/services/website";
import type { PublicSitePayload } from "@/types/website";

/** Payload do SiteShell para páginas públicas fora da home. */
export function useSiteShell(schema: string): { payload: PublicSitePayload | null; error: boolean } {
  const [payload, setPayload] = useState<PublicSitePayload | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    setError(false);
    getPublicSite(schema)
      .then(setPayload)
      .catch(() => setError(true));
  }, [schema]);

  return { payload, error };
}
