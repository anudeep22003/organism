export function Logo({ className = "text-lg" }: { className?: string }) {
  return (
    <span className={`font-semibold tracking-tight ${className}`}>
      oh<span className="text-giraffy-body">graffy</span>
    </span>
  )
}
