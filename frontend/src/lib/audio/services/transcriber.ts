import { httpClient } from "../init";
import audioLogger from "../init";

export interface Transcriber {
  transcribe(audio: Blob): Promise<string>;
}

export class WhisperTranscriber implements Transcriber {
  private url: string = "/api/transcribe/whisper";
  constructor() {}

  async transcribe(audio: Blob): Promise<string> {
    audioLogger.debug("transcribing audio, payload", { audio });
    const formData = new FormData();
    formData.append("file", audio);
    try {
      const transcribedText = await httpClient.post<string>(
        this.url,
        formData
      );
      return transcribedText;
    } catch (error) {
      audioLogger.error("error transcribing audio", { error });
      throw error;
    }
  }
}
