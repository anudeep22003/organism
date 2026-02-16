import { useEffect, useRef } from "react";

type WaveformIndicatorProps = {
  data: Float32Array | null;
};

const BAR_COUNT = 24;
const BAR_WIDTH = 2;
const BAR_GAP = 1.5;
const MIN_BAR_HEIGHT = 2;

function WaveformIndicator({ data }: WaveformIndicatorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const { width, height } = canvas;
    ctx.clearRect(0, 0, width, height);

    const step = Math.floor(data.length / BAR_COUNT);
    const centerY = height / 2;

    ctx.fillStyle = "oklch(0.577 0.245 27.325)";

    for (let i = 0; i < BAR_COUNT; i++) {
      const amplitude = Math.abs(data[i * step] ?? 0);
      const barHeight = Math.max(
        amplitude * height * 3,
        MIN_BAR_HEIGHT,
      );
      const x = i * (BAR_WIDTH + BAR_GAP);
      const y = centerY - barHeight / 2;

      ctx.beginPath();
      ctx.roundRect(x, y, BAR_WIDTH, barHeight, 1);
      ctx.fill();
    }
  }, [data]);

  const totalWidth = BAR_COUNT * (BAR_WIDTH + BAR_GAP) - BAR_GAP;

  return (
    <canvas
      ref={canvasRef}
      width={totalWidth}
      height={24}
      className="h-6"
    />
  );
}

export default WaveformIndicator;
