import { useEffect, useState } from "react";

const API_URL =
  import.meta.env.VITE_API_URL ?? "https://api.ohgraffy.com";
const APP_URL =
  import.meta.env.VITE_APP_URL ?? "https://app.ohgraffy.com";

interface PlanFeature {
  label: string;
  description: string | null;
}

interface PlanPrice {
  amountMinor: number;
  currency: string;
  interval: string;
}

interface Plan {
  planId: string;
  displayName: string;
  description: string | null;
  features: PlanFeature[];
  price: PlanPrice;
}

const DEFAULT_PLANS: Plan[] = [
  {
    planId: "free",
    displayName: "Starter",
    description: "Try it out, no credit card required.",
    features: [
      { label: "1 story", description: null },
      { label: "10 panels", description: null },
      { label: "Access to 3 existing stories", description: null },
    ],
    price: { amountMinor: 0, currency: "usd", interval: "month" },
  },
  {
    planId: "base_monthly",
    displayName: "Base",
    description: "Base subscription for monthly story creation.",
    features: [
      { label: "5 stories", description: null },
      { label: "50 story renders", description: null },
      { label: "1,000 edits", description: null },
      { label: "Unlimited PDF export", description: null },
    ],
    price: { amountMinor: 2500, currency: "usd", interval: "month" },
  },
];

function formatPrice(amountMinor: number, currency: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
  }).format(amountMinor / 100);
}

export function Pricing() {
  const [plans, setPlans] = useState<Plan[]>(DEFAULT_PLANS);

  useEffect(() => {
    fetch(`${API_URL}/api/billing/plans`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch plans");
        return res.json();
      })
      .then((data) => {
        setPlans(data.plans);
      })
      .catch(() => {
        // Keep default plans on failure
      });
  }, []);

  return (
    <section id="pricing" className="py-24 px-6 border-t border-border">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-sm font-medium tracking-widest uppercase text-muted-foreground mb-4">
          Pricing
        </h2>
        <h3 className="text-3xl sm:text-4xl font-bold mb-12">
          Simple, transparent pricing
        </h3>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.planId}
              className="p-8 rounded-xl border border-border flex flex-col"
            >
              <h4 className="text-xl font-semibold mb-1">
                {plan.displayName}
              </h4>
              {plan.description && (
                <p className="text-sm text-muted-foreground mb-4">
                  {plan.description}
                </p>
              )}
              <div className="mb-6">
                <span className="text-4xl font-bold">
                  {formatPrice(
                    plan.price.amountMinor,
                    plan.price.currency,
                  )}
                </span>
                <span className="text-muted-foreground ml-1">
                  /{plan.price.interval}
                </span>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map((feature) => (
                  <li
                    key={feature.label}
                    className="flex items-start gap-2 text-sm"
                  >
                    <span className="text-foreground mt-0.5 shrink-0">
                      +
                    </span>
                    <span className="text-muted-foreground">
                      {feature.label}
                    </span>
                  </li>
                ))}
              </ul>
              <a
                href={APP_URL}
                className="block text-center px-6 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity"
              >
                {plan.price.amountMinor === 0 ? "Create a Free Comic" : "Get Started"}
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
