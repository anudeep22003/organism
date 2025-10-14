import {
  useEffect,
  useRef,
  forwardRef,
  useImperativeHandle,
} from "react";

import audioLogger from "../init";

interface AudioWaveformProps {
  width?: number;
  height?: number;
  backgroundColor?: string;
  waveColor?: string;
  lineWidth?: number;
}

export interface AudioWaveformHandle {
  drawWaveform: (data: Float32Array) => void;
}

/**
 * Renders a real-time audio waveform visualization
 */
export const AudioWaveform = forwardRef<
  AudioWaveformHandle,
  AudioWaveformProps
>(
  (
    {
      width = 800,
      height = 200,
      backgroundColor = "#1a1a1a",
      waveColor = "#00ff88",
      lineWidth = 2,
    },
    ref
  ) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    // Initial canvas setup
    useEffect(() => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      // Clear canvas with background color
      ctx.fillStyle = backgroundColor;
      ctx.fillRect(0, 0, width, height);

      // Draw center line
      ctx.strokeStyle = `${waveColor}33`; // 20% opacity
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();
    }, [width, height, backgroundColor, waveColor]);

    /**
     * Draw the waveform based on time domain data
     */
    const drawWaveform = (dataArray: Float32Array) => {
      const canvas = canvasRef.current;
      if (!canvas) {
        audioLogger.warn("Canvas not available");
        return;
      }

      const ctx = canvas.getContext("2d");
      if (!ctx) {
        audioLogger.warn("Canvas context not available");
        return;
      }

      // Debug: Log first few values to see if we're getting data
      audioLogger.debug(
        "Drawing waveform, sample values:",
        dataArray.slice(0, 5)
      );

      // Clear canvas
      ctx.fillStyle = backgroundColor;
      ctx.fillRect(0, 0, width, height);

      // Draw center line
      ctx.strokeStyle = `${waveColor}33`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();

      // Draw waveform
      ctx.strokeStyle = waveColor;
      ctx.lineWidth = lineWidth;
      ctx.beginPath();

      const sliceWidth = width / dataArray.length;
      let x = 0;

      for (let i = 0; i < dataArray.length; i++) {
        // Convert from [-1, 1] to [0, height]
        const amplitude = dataArray[i];
        const y = ((amplitude + 1) / 2) * height;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }

        x += sliceWidth;
      }

      ctx.stroke();
    };

    // Expose the drawWaveform method via ref
    useImperativeHandle(
      ref,
      () => ({
        drawWaveform,
      }),
      [width, height, backgroundColor, waveColor, lineWidth] // Include all dependencies
    );

    return (
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="rounded-lg shadow-lg"
        style={{ border: "1px solid #333" }}
      />
    );
  }
);

AudioWaveform.displayName = "AudioWaveform";

export default AudioWaveform;
