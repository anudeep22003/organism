import { useEffect, useState } from "react";
import { Giraffy } from "./Giraffy";

const ENTRIES = [
  { prefix: "bio", meaning: "the written story of a life" },
  { prefix: "calli", meaning: "the art of beautiful writing" },
  { prefix: "cinemato", meaning: "visual storytelling in motion" },
  { prefix: "choreo", meaning: "the planning of movement" },
  { prefix: "chrono", meaning: "the mapping of time" },
  { prefix: "sceno", meaning: "the design of scenes and spaces" },
  { prefix: "icono", meaning: "the language of visual symbols" },
  { prefix: "mytho", meaning: "the collection of myths and legends" },
  { prefix: "topo", meaning: "the mapping of landscapes" },
  { prefix: "cosmo", meaning: "the mapping of the universe" },
  { prefix: "carto", meaning: "the art of mapmaking" },
  { prefix: "crypto", meaning: "the writing of secret codes" },
  { prefix: "ethno", meaning: "the study of cultures" },
  { prefix: "ideo", meaning: "representing ideas through symbols" },
  {
    prefix: "historio",
    meaning: "the study of how history is written",
  },
  { prefix: "epi", meaning: "the study of ancient inscriptions" },
  { prefix: "oceano", meaning: "the exploration of the sea" },
  { prefix: "psychogeo", meaning: "how places shape human emotion" },
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
      <div className="absolute right-[30%] top-0 translate-y-[-50%] sm:translate-y-[-70%] rotate-9 pointer-events-auto">
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
              graphy
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
