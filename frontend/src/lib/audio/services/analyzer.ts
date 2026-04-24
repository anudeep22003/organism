import audioLogger from "../init";

// Result types for better error handling
type AnalyzerInitResult =
  | { success: true }
  | { success: false; error: string };

type SourceNodeResult =
  | { success: true; source: MediaStreamAudioSourceNode }
  | { success: false; error: string };

type VisualizationResult =
  | { success: true }
  | { success: false; error: string };

/**
 * Audio Analyzer - Key Learnings:
 *
 * 1. AUDIO CONTEXT REUSE:
 *    - AudioContext is expensive to create (browser limits)
 *    - Reuse AudioContext and AnalyserNode across sessions
 *    - DON'T store MediaStreamAudioSourceNode globally - recreate each time
 *
 * 2. ANALYSER NODE BEHAVIOR:
 *    - Only OBSERVATIONAL node (no input/output manipulation)
 *    - Fits into AudioContext as part of audio processing graph
 *    - Other nodes: input → process → output
 *    - Analyser: input → observe only
 *
 * 3. DATA EXTRACTION:
 *    - getFloatTimeDomainData() MUTATES the buffer you pass in
 *    - Buffer size = fftSize / 2 (Nyquist frequency symmetry)
 *    - Don't use MediaRecorder.ondataavailable (fires every 100ms)
 *    - Use requestAnimationFrame for 60fps smooth visualization
 *    - No need to maintain data history - render each frame fresh
 *
 * 4. LIFECYCLE:
 *    - AudioContext: create once, reuse, close on cleanup
 *    - AnalyserNode: create once, reuse, null on cleanup
 *    - SourceNode: create per stream, don't store globally
 *    - Stream: recreate each recording session
 */
class Analyzer {
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private animationFrameId: number | null = null;
  private onDataCallback: ((data: Float32Array) => void) | null = null;

  constructor() {}

  /**
   * Initialize the audio context and analyzer
   * REUSE: AudioContext + AnalyserNode
   */
  async init(): Promise<AnalyzerInitResult> {
    try {
      if (!this.audioContext) {
        const contextResult = this.createAudioContext();
        if (!contextResult.success) {
          return contextResult;
        }
      }

      const resumeResult = await this.resumeAudioContext();
      if (!resumeResult.success) {
        return resumeResult;
      }

      const analyserResult = this.ensureAnalyserExists();
      if (!analyserResult.success) {
        return analyserResult;
      }

      this.logAnalyzerDetails();
      return { success: true };
    } catch (error) {
      audioLogger.error("Error initializing analyzer", error);
      return {
        success: false,
        error: "Failed to initialize audio analyzer",
      };
    }
  }

  /**
   * Create a new audio context
   * EXPENSIVE: Only create once, reuse across sessions
   */
  private createAudioContext(): AnalyzerInitResult {
    try {
      this.audioContext = new AudioContext();
      audioLogger.debug("Audio context created");
      return { success: true };
    } catch (error) {
      audioLogger.error("Error creating audio context", error);
      return {
        success: false,
        error: "Failed to create audio context",
      };
    }
  }

  /**
   * Resume suspended audio context
   */
  private async resumeAudioContext(): Promise<AnalyzerInitResult> {
    if (!this.audioContext) {
      return { success: false, error: "Audio context not initialized" };
    }

    if (this.audioContext.state === "suspended") {
      try {
        await this.audioContext.resume();
        audioLogger.debug("Audio context resumed");
      } catch (error) {
        audioLogger.error("Error resuming audio context", error);
        return {
          success: false,
          error: "Failed to resume audio context",
        };
      }
    }

    return { success: true };
  }

  /**
   * Ensure analyser node exists and is properly configured
   * REUSE: AnalyserNode across sessions
   */
  private ensureAnalyserExists(): AnalyzerInitResult {
    if (!this.analyser) {
      const analyserResult = this.createAnalyserAndConfigure();
      if (!analyserResult.success) {
        return analyserResult;
      }
      this.analyser = analyserResult.analyser;
    }

    return { success: true };
  }

  /**
   * Create and configure the analyser node
   * Buffer size = fftSize / 2 (Nyquist frequency symmetry)
   */
  private createAnalyserAndConfigure():
    | { success: true; analyser: AnalyserNode }
    | { success: false; error: string } {
    if (!this.audioContext) {
      return {
        success: false,
        error: "Audio context not initialized",
      };
    }

    try {
      const analyser = this.audioContext.createAnalyser();

      // Configure analyser settings
      analyser.fftSize = 256; // Buffer size will be 128 (fftSize / 2)
      analyser.smoothingTimeConstant = 0.8;
      analyser.minDecibels = -90;
      analyser.maxDecibels = -10;

      audioLogger.debug("Analyser created and configured");
      return { success: true, analyser };
    } catch (error) {
      audioLogger.error("Error creating analyser", error);
      return {
        success: false,
        error: "Failed to create analyser node",
      };
    }
  }

  /**
   * Create a source node from a media stream
   * RECREATE: Don't store globally, create per stream
   */
  createSourceNode(stream: MediaStream): SourceNodeResult {
    if (!this.audioContext) {
      return {
        success: false,
        error: "Audio context not initialized",
      };
    }

    try {
      const source = this.audioContext.createMediaStreamSource(stream);
      audioLogger.debug("Source node created");
      return { success: true, source };
    } catch (error) {
      audioLogger.error("Error creating source node", error);
      return {
        success: false,
        error: "Failed to create source node",
      };
    }
  }

  /**
   * Connect a media stream to the analyser
   */
  connectToStream(stream: MediaStream): AnalyzerInitResult {
    try {
      const sourceResult = this.createSourceNode(stream);
      if (!sourceResult.success) {
        return { success: false, error: sourceResult.error };
      }

      if (!this.analyser) {
        return {
          success: false,
          error: "Analyser not initialized",
        };
      }

      sourceResult.source.connect(this.analyser);
      audioLogger.debug("Connected to stream");
      return { success: true };
    } catch (error) {
      audioLogger.error("Error connecting to stream", error);
      return {
        success: false,
        error: "Failed to connect to stream",
      };
    }
  }

  /**
   * Get time domain data from the analyser
   * MUTATES: Buffer is modified in-place by getFloatTimeDomainData()
   */
  getTimeDomainData(): Float32Array | null {
    if (!this.analyser) {
      audioLogger.warn("Analyser not initialized");
      return null;
    }

    try {
      // Buffer size = fftSize / 2 (Nyquist frequency symmetry)
      const buffer = new Float32Array(this.analyser.frequencyBinCount);
      this.analyser.getFloatTimeDomainData(buffer); // MUTATES buffer
      return buffer;
    } catch (error) {
      audioLogger.error("Error getting time domain data", error);
      return null;
    }
  }

  /**
   * Register a callback to receive time domain data updates
   */
  setDataCallback(callback: (data: Float32Array) => void): void {
    this.onDataCallback = callback;
  }

  /**
   * Start the visualization animation loop
   * 60FPS: Use requestAnimationFrame, NOT MediaRecorder.ondataavailable (100ms)
   */
  startVisualization(): VisualizationResult {
    if (!this.analyser) {
      return {
        success: false,
        error: "Analyser not initialized",
      };
    }

    if (this.animationFrameId !== null) {
      return {
        success: false,
        error: "Visualization already running",
      };
    }

    try {
      const animate = () => {
        const buffer = this.getTimeDomainData();
        if (buffer && this.onDataCallback) {
          this.onDataCallback(buffer); // Fresh data each frame
        }
        this.animationFrameId = requestAnimationFrame(animate);
      };

      animate();
      audioLogger.debug("Visualization started");
      return { success: true };
    } catch (error) {
      audioLogger.error("Error starting visualization", error);
      return {
        success: false,
        error: "Failed to start visualization",
      };
    }
  }

  /**
   * Stop the visualization animation loop
   */
  stopVisualization(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
      audioLogger.debug("Visualization stopped");
    }
  }

  /**
   * Clean up all resources
   * REUSE: AudioContext + AnalyserNode
   * RECREATE: SourceNode (per stream)
   */
  cleanup(): void {
    this.stopVisualization();
    this.onDataCallback = null;

    if (this.audioContext && this.audioContext.state !== "closed") {
      this.audioContext.close();
      this.audioContext = null;
    }

    this.analyser = null;
    audioLogger.debug("Analyzer cleaned up");
  }

  /**
   * Log analyzer details for debugging
   */
  private logAnalyzerDetails(): void {
    if (!this.audioContext) {
      audioLogger.warn("Audio context not available for logging");
      return;
    }

    audioLogger.debug("Analyzer details", {
      audioContextState: this.audioContext.state,
      analyserExists: !!this.analyser,
      analyserFftSize: this.analyser?.fftSize,
      analyserFrequencyBinCount: this.analyser?.frequencyBinCount,
    });
  }
}

export default Analyzer;
