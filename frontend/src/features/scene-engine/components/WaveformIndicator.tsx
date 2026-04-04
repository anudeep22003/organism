import { useEffect, useRef } from "react";

type WaveformIndicatorProps = {
  data: Float32Array;
};

const BAR_COUNT = 24;
const BAR_WIDTH = 2;
const BAR_GAP = 1.5;
const MIN_BAR_HEIGHT = 2;
const TOTAL_WIDTH = BAR_COUNT * (BAR_WIDTH + BAR_GAP) - BAR_GAP;

export default function WaveformIndicator({ data }: WaveformIndicatorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const color = getComputedStyle(canvas).color;
    const { width, height } = canvas;
    ctx.clearRect(0, 0, width, height);

    const step = Math.floor(data.length / BAR_COUNT);
    const centerY = height / 2;

    ctx.fillStyle = color;

    for (let i = 0; i < BAR_COUNT; i++) {
      const amplitude = Math.abs(data[i * step] ?? 0);
      const barHeight = Math.max(amplitude * height * 3, MIN_BAR_HEIGHT);
      const x = i * (BAR_WIDTH + BAR_GAP);
      const y = centerY - barHeight / 2;

      ctx.beginPath();
      ctx.roundRect(x, y, BAR_WIDTH, barHeight, 1);
      ctx.fill();
    }
  }, [data]);

  return (
    <canvas
      ref={canvasRef}
      width={TOTAL_WIDTH}
      height={24}
      className="h-6 text-foreground"
    />
  );
}
