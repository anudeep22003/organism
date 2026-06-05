const useCases = [
  {
    title: "Teach values to your children",
    description: "Create personalized stories that teach empathy, courage, and kindness — starring characters your kids recognize.",
  },
  {
    title: "Learn new concepts",
    description: "Transform complex topics into visual narratives that make learning intuitive and memorable.",
  },
  {
    title: "Capture family memories",
    description: "Turn real events into illustrated stories. Anniversaries, trips, milestones — preserved as comics.",
  },
  {
    title: "Create with friends",
    description: "Collaborative storytelling. Build narratives together and see yourselves in the adventure.",
  },
]

export function UseCases() {
  return (
    <section className="py-24 px-6 border-t border-border">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-sm font-medium tracking-widest uppercase text-muted-foreground mb-4">
          Use Cases
        </h2>
        <h3 className="text-3xl sm:text-4xl font-bold mb-12">
          Stories for every part of life
        </h3>

        <div className="grid sm:grid-cols-2 gap-6">
          {useCases.map((useCase) => (
            <div key={useCase.title} className="p-6 rounded-xl border border-border">
              <h4 className="font-semibold mb-2">{useCase.title}</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">{useCase.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
