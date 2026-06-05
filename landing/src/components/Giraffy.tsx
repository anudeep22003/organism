import { useCallback, useEffect, useRef, useState } from "react"

const C = {
  body: "#F5A623",
  bodyLight: "#FFCF6B",
  spots: "#C47A1A",
  spotsAlt: "#A85E0A",
  belly: "#FFF0D4",
  nose: "#E8935A",
  eyes: "#2D1B00",
  eyeWhite: "#FFFDF7",
  cheek: "#FF8FAB",
  horn: "#D4A853",
  hornTip: "#6B4226",
  leaf: "#7ECE5C",
  leafDark: "#4CAF50",
  accent: "#FF6B9D",
  accentAlt: "#845EF7",
} as const

export type GiraffyMood = "happy" | "ohh" | "excited" | "thinking" | "sleeping" | "waving"

const MOODS: GiraffyMood[] = ["happy", "ohh", "excited", "thinking", "sleeping", "waving"]

const SPEECH: Record<GiraffyMood, string> = {
  happy: "Let's read a story! \u{1F4D6}",
  ohh: "Ohhhh graffy! \u2728",
  excited: "Ooh, what happens next?!",
  thinking: "Hmm, once upon a time...",
  sleeping: "zzz... sweet dreams...",
  waving: "Hi there, friend! \u{1F44B}",
}

interface GiraffyProps {
  mood?: GiraffyMood
  size?: number
}

export function Giraffy({ mood = "happy", size = 200 }: GiraffyProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [m, setM] = useState<GiraffyMood>(mood)
  const [px, setPx] = useState(0)
  const [py, setPy] = useState(0)
  const [blink, setBlink] = useState(false)
  const [speech, setSpeech] = useState(true)

  useEffect(() => setM(mood), [mood])

  // Eye tracking
  useEffect(() => {
    if (m === "sleeping") { setPx(0); setPy(0); return }
    const onMove = (e: MouseEvent) => {
      const el = svgRef.current
      if (!el) return
      const r = el.getBoundingClientRect()
      const dx = e.clientX - (r.left + r.width / 2)
      const dy = e.clientY - (r.top + r.height * 0.3)
      const dist = Math.hypot(dx, dy)
      const t = Math.min(dist / 250, 1)
      const a = Math.atan2(dy, dx)
      setPx(Math.cos(a) * t * 3.5)
      setPy(Math.sin(a) * t * 3.5)
    }
    window.addEventListener("mousemove", onMove)
    return () => window.removeEventListener("mousemove", onMove)
  }, [m])

  // Blink
  useEffect(() => {
    if (m === "sleeping") return
    let tid: number
    const next = () => {
      tid = window.setTimeout(() => {
        setBlink(true)
        window.setTimeout(() => { setBlink(false); next() }, 150)
      }, 3000 + Math.random() * 2000)
    }
    next()
    return () => clearTimeout(tid)
  }, [m])

  // Speech bubble
  useEffect(() => {
    setSpeech(true)
    const tid = window.setTimeout(() => setSpeech(false), 3000)
    return () => clearTimeout(tid)
  }, [m])

  const onClick = useCallback(() => {
    setM((prev) => MOODS[(MOODS.indexOf(prev) + 1) % MOODS.length])
  }, [])

  const closed = m === "sleeping" || blink
  const isOhh = m === "ohh"

  return (
    <svg
      ref={svgRef}
      viewBox="0 0 200 300"
      width={size}
      style={{ overflow: "visible", cursor: "pointer" }}
      onClick={onClick}
      role="img"
      aria-label={`Giraffy mascot feeling ${m}`}
    >
      <style>{`
        @keyframes giraffy-wave { 0%,100%{transform:rotate(-15deg)}50%{transform:rotate(25deg)} }
        @keyframes giraffy-sparkle { 0%,100%{opacity:.2;transform:scale(.7)}50%{opacity:1;transform:scale(1.2)} }
        @keyframes giraffy-float { 0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)} }
        @keyframes giraffy-speech { 0%{opacity:0;transform:translateY(4px)}10%{opacity:1;transform:translateY(0)}80%{opacity:1}100%{opacity:0} }
      `}</style>

      <defs>
        <radialGradient id="g-body" cx="40%" cy="30%">
          <stop offset="0%" stopColor={C.bodyLight} />
          <stop offset="100%" stopColor={C.body} />
        </radialGradient>
        <radialGradient id="g-head" cx="40%" cy="35%">
          <stop offset="0%" stopColor={C.bodyLight} />
          <stop offset="100%" stopColor={C.body} />
        </radialGradient>
      </defs>

      {/* Shadow */}
      <ellipse cx="100" cy="275" rx="50" ry="8" fill={C.body} opacity=".12" />

      {/* Tail */}
      <path d="M142 208Q165 195 160 175" stroke={C.body} strokeWidth="4" fill="none" strokeLinecap="round" />
      <ellipse cx="160" cy="172" rx="6" ry="5" fill={C.spots} transform="rotate(-20 160 172)" />

      {/* Back legs */}
      <rect x="80" y="237" width="14" height="28" rx="7" fill={C.spots} />
      <rect x="106" y="237" width="14" height="28" rx="7" fill={C.spots} />
      <rect x="80" y="258" width="14" height="8" rx="5" fill={C.spotsAlt} />
      <rect x="106" y="258" width="14" height="8" rx="5" fill={C.spotsAlt} />

      {/* Body */}
      <ellipse cx="100" cy="217" rx="45" ry="36" fill="url(#g-body)" />
      <ellipse cx="100" cy="224" rx="30" ry="24" fill={C.belly} opacity=".85" />
      {/* Body spots */}
      <ellipse cx="70" cy="207" rx="8" ry="6" fill={C.spots} opacity=".6" transform="rotate(-10 70 207)" />
      <ellipse cx="130" cy="210" rx="7" ry="5" fill={C.spots} opacity=".6" transform="rotate(10 130 210)" />
      <ellipse cx="82" cy="230" rx="5" ry="7" fill={C.spots} opacity=".4" />

      {/* Front legs */}
      {m !== "waving" && (
        <>
          <rect x="68" y="240" width="16" height="30" rx="8" fill={C.body} />
          <rect x="68" y="262" width="16" height="8" rx="5" fill={C.spotsAlt} />
        </>
      )}
      <rect x="116" y="240" width="16" height="30" rx="8" fill={C.body} />
      <rect x="116" y="262" width="16" height="8" rx="5" fill={C.spotsAlt} />

      {/* Waving arm */}
      {m === "waving" && (
        <g style={{ transformOrigin: "60px 220px", animation: "giraffy-wave .8s ease-in-out infinite" }}>
          <rect x="46" y="192" width="16" height="35" rx="8" fill={C.body} />
          <rect x="46" y="189" width="16" height="10" rx="5" fill={C.spotsAlt} />
        </g>
      )}

      {/* Neck */}
      <path d="M83 128Q80 170 85 200L115 200Q120 170 117 128Z" fill="url(#g-body)" />
      <ellipse cx="95" cy="148" rx="6" ry="5" fill={C.spots} opacity=".6" />
      <ellipse cx="110" cy="165" rx="5" ry="6" fill={C.spots} opacity=".6" />
      <ellipse cx="90" cy="180" rx="5" ry="4" fill={C.spots} opacity=".6" />

      {/* Head */}
      <ellipse cx="100" cy="92" rx="52" ry="46" fill="url(#g-head)" />
      <ellipse cx="66" cy="74" rx="7" ry="5" fill={C.spots} opacity=".4" transform="rotate(-15 66 74)" />
      <ellipse cx="137" cy="77" rx="6" ry="4" fill={C.spots} opacity=".4" transform="rotate(10 137 77)" />

      {/* Ears */}
      <ellipse cx="53" cy="70" rx="14" ry="8" fill={C.body} transform="rotate(-25 53 70)" />
      <ellipse cx="53" cy="70" rx="9" ry="5" fill={C.nose} opacity=".7" transform="rotate(-25 53 70)" />
      <ellipse cx="147" cy="70" rx="14" ry="8" fill={C.body} transform="rotate(25 147 70)" />
      <ellipse cx="147" cy="70" rx="9" ry="5" fill={C.nose} opacity=".7" transform="rotate(25 147 70)" />

      {/* Ossicones */}
      <rect x="79" y="44" width="7" height="20" rx="3.5" fill={C.horn} />
      <circle cx="82.5" cy="41" r="6" fill={C.hornTip} />
      <rect x="114" y="44" width="7" height="20" rx="3.5" fill={C.horn} />
      <circle cx="117.5" cy="41" r="6" fill={C.hornTip} />

      {/* Leaf */}
      <g transform="translate(117.5,35)">
        <path d="M0 0Q12-10 17-3Q10 3 0 0" fill={C.leaf} />
        <path d="M1 0Q8-5 13-2" stroke={C.leafDark} strokeWidth=".8" fill="none" />
      </g>

      {/* Muzzle */}
      <ellipse cx="100" cy="108" rx="30" ry="20" fill={C.nose} />

      {/* Cheek blush */}
      <ellipse cx="60" cy="102" rx="10" ry="5" fill={C.cheek} opacity={isOhh ? ".7" : ".35"} />
      <ellipse cx="140" cy="102" rx="10" ry="5" fill={C.cheek} opacity={isOhh ? ".7" : ".35"} />

      {/* Eyes */}
      {closed ? (
        <>
          <path d="M65 87Q78 93 91 87" stroke={C.eyes} strokeWidth="2.5" fill="none" strokeLinecap="round" />
          <path d="M109 87Q122 93 135 87" stroke={C.eyes} strokeWidth="2.5" fill="none" strokeLinecap="round" />
        </>
      ) : (
        <>
          <ellipse cx="78" cy="86" rx={isOhh ? 16 : 15} ry={isOhh ? 19 : 17} fill={C.eyeWhite} />
          <ellipse cx="122" cy="86" rx={isOhh ? 16 : 15} ry={isOhh ? 19 : 17} fill={C.eyeWhite} />
          <circle cx={78 + px} cy={86 + py + (m === "thinking" ? -3 : 0)} r={isOhh ? 8 : 7} fill={C.eyes} />
          <circle cx={122 + px} cy={86 + py + (m === "thinking" ? -3 : 0)} r={isOhh ? 8 : 7} fill={C.eyes} />
          <circle cx={81 + px * .4} cy={82 + py * .4} r="3" fill="white" />
          <circle cx={125 + px * .4} cy={82 + py * .4} r="3" fill="white" />
          <circle cx={76 + px * .2} cy={88 + py * .2} r="1.5" fill="white" opacity=".5" />
          <circle cx={120 + px * .2} cy={88 + py * .2} r="1.5" fill="white" opacity=".5" />
          {m === "excited" && (
            <>
              <path d="M63 92Q78 86 93 92" fill="url(#g-head)" />
              <path d="M107 92Q122 86 137 92" fill="url(#g-head)" />
            </>
          )}
        </>
      )}

      {/* Nostrils */}
      <circle cx="94" cy="108" r="2" fill={C.spotsAlt} opacity=".4" />
      <circle cx="106" cy="108" r="2" fill={C.spotsAlt} opacity=".4" />

      {/* Mouth */}
      {isOhh ? (
        <ellipse cx="100" cy="118" rx="7" ry="9" fill={C.spotsAlt} />
      ) : m === "thinking" ? (
        <path d="M93 117Q97 119 100 117Q103 115 107 117" stroke={C.spotsAlt} strokeWidth="2" fill="none" strokeLinecap="round" />
      ) : m === "excited" ? (
        <path d="M89 115Q100 126 111 115" stroke={C.spotsAlt} strokeWidth="2.5" fill="none" strokeLinecap="round" />
      ) : (
        <path d="M91 116Q100 122 109 116" stroke={C.spotsAlt} strokeWidth="2" fill="none" strokeLinecap="round" />
      )}

      {/* Ohh sparkles */}
      {isOhh && (
        <>
          <path d="M42 55L44 49L46 55L52 57L46 59L44 65L42 59L36 57Z" fill={C.accent}
            style={{ animation: "giraffy-sparkle 1.5s ease-in-out infinite", transformOrigin: "44px 57px" }} />
          <path d="M152 48L154 43L156 48L161 50L156 52L154 57L152 52L147 50Z" fill={C.accentAlt}
            style={{ animation: "giraffy-sparkle 1.5s ease-in-out .5s infinite", transformOrigin: "154px 50px" }} />
          <path d="M162 88L163.5 84L165 88L169 89.5L165 91L163.5 95L162 91L158 89.5Z" fill={C.accent} opacity=".7"
            style={{ animation: "giraffy-sparkle 1.5s ease-in-out 1s infinite", transformOrigin: "163.5px 89.5px" }} />
        </>
      )}

      {/* Thinking bubbles */}
      {m === "thinking" && (
        <>
          <circle cx="148" cy="68" r="4" fill={C.eyeWhite} opacity=".5" />
          <circle cx="158" cy="53" r="6" fill={C.eyeWhite} opacity=".4" />
          <circle cx="165" cy="38" r="3" fill={C.eyeWhite} opacity=".3" />
        </>
      )}

      {/* Sleeping Zzz */}
      {m === "sleeping" && (
        <g style={{ animation: "giraffy-float 3s ease-in-out infinite" }}>
          <text x="138" y="68" fontSize="13" fontWeight="bold" fill={C.accentAlt} opacity=".7" fontFamily="sans-serif">z</text>
          <text x="150" y="52" fontSize="17" fontWeight="bold" fill={C.accentAlt} opacity=".5" fontFamily="sans-serif">z</text>
          <text x="162" y="34" fontSize="21" fontWeight="bold" fill={C.accentAlt} opacity=".3" fontFamily="sans-serif">z</text>
        </g>
      )}

      {/* Speech bubble */}
      {speech && (
        <g style={{ animation: "giraffy-speech 3s ease-in-out forwards" }}>
          <rect x="25" y="-20" width="150" height="28" rx="14" fill="white" />
          <polygon points="92,8 100,16 108,8" fill="white" />
          <text x="100" y="0" textAnchor="middle" fontSize="10" fill="#333" fontFamily="sans-serif">
            {SPEECH[m]}
          </text>
        </g>
      )}
    </svg>
  )
}
