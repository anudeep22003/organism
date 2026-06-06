import { Link } from "react-router"
import { SUPPORT_EMAIL, ROUTES } from "@/constants"
import { Logo } from "./Logo"

export function Footer() {
  return (
    <footer className="py-12 px-6 border-t border-border">
      <div className="max-w-4xl mx-auto">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div>
            <p className="mb-1"><Logo /></p>
            <p className="text-sm text-muted-foreground">
              Stories, reimagined through AI.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-4 text-sm text-muted-foreground">
            <a href={`mailto:${SUPPORT_EMAIL}`} className="hover:text-foreground transition-colors">
              Contact
            </a>
            <Link to={ROUTES.terms} className="hover:text-foreground transition-colors">
              Terms
            </Link>
            <Link to={ROUTES.privacy} className="hover:text-foreground transition-colors">
              Privacy
            </Link>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-border text-sm text-muted-foreground">
          &copy; {new Date().getFullYear()} Ohgraffy. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
