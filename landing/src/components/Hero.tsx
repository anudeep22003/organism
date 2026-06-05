const APP_URL = import.meta.env.VITE_APP_URL ?? "https://app.ohgraffy.com"

export function Hero() {
  return (
    <section className="pt-32 pb-24 px-6">
      <div className="max-w-4xl mx-auto text-center">
        <p className="text-sm font-medium tracking-widest uppercase text-muted-foreground mb-6">
          A storytelling research lab
        </p>
        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] mb-6">
          Stories, reimagined<br />
          <span className="text-muted-foreground">through AI</span>
        </h1>
        <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
          We study the art of storytelling and embed it into artificial intelligence
          so that powerful stories are accessible to everybody.
        </p>
        <div className="flex items-center justify-center gap-4">
          <a
            href={APP_URL}
            className="px-6 py-3 rounded-lg bg-primary text-primary-foreground font-medium text-base hover:opacity-90 transition-opacity"
          >
            Start Creating
          </a>
          <a
            href="#how-it-works"
            className="px-6 py-3 rounded-lg border border-border text-foreground font-medium text-base hover:bg-muted transition-colors"
          >
            See How It Works
          </a>
        </div>
      </div>
    </section>
  )
}
