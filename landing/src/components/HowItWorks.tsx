const steps = [
  {
    number: "01",
    title: "Write Your Story",
    description: "Describe what you want to tell. A bedtime story for your child, a family adventure, a concept you want to learn.",
  },
  {
    number: "02",
    title: "Characters Come Alive",
    description: "The engine extracts characters from your narrative. Upload reference images to ground them in reality.",
  },
  {
    number: "03",
    title: "Panels Generated",
    description: "Your story is broken into comic panels with dialogue, backgrounds, and composition — all driven by narrative structure.",
  },
  {
    number: "04",
    title: "Export & Share",
    description: "Download your finished comic. Share it with your family, friends, or keep it as a personal keepsake.",
  },
]

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 px-6 border-t border-border">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-sm font-medium tracking-widest uppercase text-muted-foreground mb-4">
          How It Works
        </h2>
        <h3 className="text-3xl sm:text-4xl font-bold mb-16">
          From idea to comic in minutes
        </h3>

        <div className="space-y-12">
          {steps.map((step) => (
            <div key={step.number} className="flex gap-6 items-start">
              <span className="text-3xl font-bold text-muted-foreground/50 shrink-0 w-12">
                {step.number}
              </span>
              <div>
                <h4 className="text-xl font-semibold mb-2">{step.title}</h4>
                <p className="text-muted-foreground leading-relaxed">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
