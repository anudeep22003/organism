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
              Stories are how we receive information, knowledge, and understanding
              at the highest fidelity. Image generation, video generation, audio generation
              &mdash; they are only as good as the story being told.
            </p>
            <p>
              We study the great short story writers to understand the principles of
              powerful storytelling, then embed those principles into AI. Once we have
              the story, we project it into any form: a comic, an animation, a video.
            </p>
            <p className="text-foreground font-medium">
              The projection is separate from the story. That is what we are building.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
