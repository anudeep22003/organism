import { useCallback, useEffect, useState } from "react"
import { Sun02Icon, Moon02Icon } from "@hugeicons/core-free-icons"
import { HugeiconsIcon } from "@hugeicons/react"

function getInitialTheme(): "light" | "dark" {
  const stored = localStorage.getItem("theme")
  if (stored === "dark" || stored === "light") return stored
  return matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">(getInitialTheme)

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark")
    localStorage.setItem("theme", theme)
  }, [theme])

  const toggle = useCallback(() => {
    setTheme((t) => (t === "dark" ? "light" : "dark"))
  }, [])

  return (
    <button
      onClick={toggle}
      className="text-muted-foreground hover:text-foreground transition-colors"
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
    >
      <HugeiconsIcon
        icon={theme === "dark" ? Sun02Icon : Moon02Icon}
        size={18}
      />
    </button>
  )
}
