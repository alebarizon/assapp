"""Planos SaaS estáticos — sem AdminPlan neste ciclo (Stripe fica para depois)."""

SAAS_PLANS = [
    {
        "slug": "starter",
        "name": "Starter",
        "description": "Ideal para associações em início de digitalização.",
        "price_label": "Gratuito no trial",
        "trial_days": 30,
    },
    {
        "slug": "profissional",
        "name": "Profissional",
        "description": "Mandatos, memória, membros e eventos científicos.",
        "price_label": "A definir",
        "trial_days": 30,
    },
]

PLAN_SLUGS = {p["slug"] for p in SAAS_PLANS}


def get_plan(slug: str) -> dict | None:
    for plan in SAAS_PLANS:
        if plan["slug"] == slug:
            return plan
    return None
