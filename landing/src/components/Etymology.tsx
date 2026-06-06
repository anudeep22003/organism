import { useEffect, useState } from "react";
import { Giraffy } from "./Giraffy";

const ENTRIES = [
  { prefix: "bio", meaning: "writing a life into story" },
  { prefix: "calli", meaning: "giving words a visible voice" },
  { prefix: "cinemato", meaning: "writing in light and motion" },
  { prefix: "choreo", meaning: "turning movement into meaning" },
  { prefix: "chrono", meaning: "tracing the arc of time" },
  { prefix: "sceno", meaning: "building worlds scene by scene" },
  { prefix: "icono", meaning: "telling stories through symbols" },
  { prefix: "mytho", meaning: "preserving stories older than memory" },
  { prefix: "topo", meaning: "reading the story a place tells" },
  { prefix: "cosmo", meaning: "writing the story of everything" },
  { prefix: "carto", meaning: "drawing the paths between places" },
  { prefix: "crypto", meaning: "hiding one story inside another" },
  {
    prefix: "ethno",
    meaning: "recording how a people narrate themselves",
  },
  { prefix: "ideo", meaning: "giving shape to abstract thought" },
  { prefix: "historio", meaning: "questioning who tells the story" },
  { prefix: "epi", meaning: "decoding stories carved in stone" },
  { prefix: "oceano", meaning: "charting the narratives of the deep" },
  {
    prefix: "psychogeo",
    meaning: "how places write themselves into us",
  },
];

export function Etymology() {
  const [index, setIndex] = useState(0);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setFading(true);
      setTimeout(() => {
        setIndex((i) => (i + 1) % ENTRIES.length);
        setFading(false);
      }, 300);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const entry = ENTRIES[index];

  return (
    <section className="relative">
      <div className="absolute left sm:left-[28%] top-0 translate-y-[-44%] sm:translate-y-[-70%] rotate-[-12deg] pointer-events-auto">
        <Giraffy mood="ohh" size={180} />
      </div>
      <div className="relative z-10 bg-background py-12 px-6 border-t border-border">
        <div className="max-w-4xl mx-auto flex flex-col items-center gap-2">
          <div className="grid grid-cols-[1fr_auto_1fr] items-center text-sm sm:text-base tracking-wide">
            <span
              className={`justify-self-end inline-block px-2 py-0.5 rounded border border-border text-muted-foreground/70 transition-opacity duration-300 ${fading ? "opacity-0" : "opacity-100"}`}
            >
              {entry.prefix}
            </span>
            <span className="mx-2 text-muted-foreground/40">+</span>
            <span className="justify-self-start inline-block px-2 py-0.5 rounded border border-border text-muted-foreground/70">
              gra
              <span className="font-extrabold">ff</span>y
            </span>
          </div>
          <p
            className={`text-sm text-muted-foreground/50 italic transition-opacity duration-300 ${fading ? "opacity-0" : "opacity-100"}`}
          >
            {entry.meaning}
          </p>
        </div>
      </div>
    </section>
  );
}
