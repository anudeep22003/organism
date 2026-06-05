import { useEffect, useState } from "react"

const API_URL = import.meta.env.VITE_API_URL ?? "https://api.ohgraffy.com"
const APP_URL = import.meta.env.VITE_APP_URL ?? "https://app.ohgraffy.com"

interface PlanFeature {
  label: string
  description: string | null
}

interface PlanPrice {
  amountMinor: number
  currency: string
  interval: string
}

interface Plan {
  planId: string
  displayName: string
  description: string | null
  features: PlanFeature[]
  price: PlanPrice
}

function formatPrice(amountMinor: number, currency: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
  }).format(amountMinor / 100)
}

export function Pricing() {
  const [plans, setPlans] = useState<Plan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch(`${API_URL}/api/billing/plans`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch plans")
        return res.json()
      })
      .then((data) => {
        setPlans(data.plans)
        setLoading(false)
      })
      .catch(() => {
        setError(true)
        setLoading(false)
      })
  }, [])

  return (
    <section id="pricing" className="py-24 px-6 border-t border-border">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-sm font-medium tracking-widest uppercase text-muted-foreground mb-4">
          Pricing
        </h2>
        <h3 className="text-3xl sm:text-4xl font-bold mb-12">
          Simple, transparent pricing
        </h3>

        {loading && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2].map((i) => (
              <div key={i} className="p-8 rounded-xl border border-border animate-pulse">
                <div className="h-6 bg-muted rounded w-1/2 mb-4" />
                <div className="h-10 bg-muted rounded w-1/3 mb-6" />
                <div className="space-y-3">
                  <div className="h-4 bg-muted rounded w-3/4" />
                  <div className="h-4 bg-muted rounded w-2/3" />
                  <div className="h-4 bg-muted rounded w-3/4" />
                </div>
              </div>
            ))}
          </div>
        )}

        {error && (
          <p className="text-muted-foreground">
            Pricing information is currently unavailable. Please check back shortly or{" "}
            <a href={APP_URL} className="underline hover:text-foreground">sign up</a> to see current plans.
          </p>
        )}

        {!loading && !error && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <div key={plan.planId} className="p-8 rounded-xl border border-border flex flex-col">
                <h4 className="text-xl font-semibold mb-1">{plan.displayName}</h4>
                {plan.description && (
                  <p className="text-sm text-muted-foreground mb-4">{plan.description}</p>
                )}
                <div className="mb-6">
                  <span className="text-4xl font-bold">
                    {formatPrice(plan.price.amountMinor, plan.price.currency)}
                  </span>
                  <span className="text-muted-foreground ml-1">/{plan.price.interval}</span>
                </div>
                <ul className="space-y-3 mb-8 flex-1">
                  {plan.features.map((feature) => (
                    <li key={feature.label} className="flex items-start gap-2 text-sm">
                      <span className="text-foreground mt-0.5 shrink-0">+</span>
                      <span className="text-muted-foreground">{feature.label}</span>
                    </li>
                  ))}
                </ul>
                <a
                  href={APP_URL}
                  className="block text-center px-6 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity"
                >
                  Get Started
                </a>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
