import { ThemeToggle } from "./ThemeToggle"

const APP_URL = import.meta.env.VITE_APP_URL ?? "https://app.ohgraffy.com"

export function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md bg-background/80 border-b border-border">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <a href="/" className="text-lg font-semibold tracking-tight">
          oh<span className="text-giraffy-body">graffy</span>
        </a>
        <nav className="flex items-center gap-6">
          <a href="#pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Pricing
          </a>
          <ThemeToggle />
          <a
            href={APP_URL}
            className="text-sm px-4 py-2 rounded-lg bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity"
          >
            Start Free
          </a>
        </nav>
      </div>
    </header>
  )
}
