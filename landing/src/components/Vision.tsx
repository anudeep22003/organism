export function Vision() {
  return (
    <section className="py-24 px-6 border-t border-border">
      <div className="max-w-4xl mx-auto">
        <div className="grid md:grid-cols-2 gap-16">
          <div>
            <h2 className="text-sm font-medium tracking-widest uppercase text-muted-foreground mb-4">
              The Thesis
            </h2>
            <p className="text-2xl sm:text-3xl font-semibold leading-snug">
              In the age of AI, everyone focuses on media fidelity.
              We focus on the story.
            </p>
          </div>
          <div className="space-y-6 text-muted-foreground leading-relaxed">
            <p>
              We study storytelling across manga, screenplays, sci-fi, animation, and
              literary fiction: distilling the principles that make narrative
              work, then embedding them into AI.
            </p>
            <p className="text-foreground font-medium">
              The story is separate from the projection: a comic, a film, a
              game. That is what we are building.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
