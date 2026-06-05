export function Product() {
  return (
    <section className="py-24 px-6 border-t border-border">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-sm font-medium tracking-widest uppercase text-muted-foreground mb-4">
          First Product
        </h2>
        <h3 className="text-3xl sm:text-4xl font-bold mb-6">
          The Comic Engine
        </h3>
        <p className="text-lg text-muted-foreground max-w-2xl mb-12 leading-relaxed">
          Construct a story and project it into a comic. Tell stories of yourself, your
          family, friends, and groups &mdash; with AI that honors your image references
          to place real people into the narrative.
        </p>

        <div className="grid sm:grid-cols-3 gap-6">
          <FeatureCard
            title="Personal Stories"
            description="Upload image references of yourself or loved ones. The AI honors likenesses to create comics starring the real you."
          />
          <FeatureCard
            title="Story-First AI"
            description="The engine focuses on narrative structure, pacing, and emotional beats before generating a single panel."
          />
          <FeatureCard
            title="Share Instantly"
            description="Export your comics and share stories with family, friends, or the world."
          />
        </div>
      </div>
    </section>
  )
}

function FeatureCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="p-6 rounded-xl border border-border bg-muted/50">
      <h4 className="font-semibold mb-2">{title}</h4>
      <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
    </div>
  )
}
