import uuid

from fastapi import APIRouter, File, UploadFile
from loguru import logger

from core.sockets import async_openai_client

router = APIRouter(prefix="/transcribe", tags=["transcribe"])

logger = logger.bind(name=__name__)


@router.post("/whisper")
async def transcribe_whisper(file: UploadFile = File(...)) -> str:
    audio_bytes = await file.read()

    content_type = file.content_type or "audio/webm"
    if not content_type.startswith("audio/"):
        raise ValueError(f"Invalid file content type: {content_type}")

    # Extract extension from content type
    extension = content_type.split("/")[-1]
    unique_file_name = f"{uuid.uuid4()}.{extension}"

    logger.info(
        "Transcribing audio file",
        file=unique_file_name,
        file_size=len(audio_bytes),
        file_type=file.content_type,
    )
    file_tuple = (unique_file_name, audio_bytes, file.content_type)
    transcript = await async_openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=file_tuple,
    )
    return transcript.text


@router.post("/whisper-test")
async def transcribe_whisper_test(file: UploadFile = File(...)) -> str:
    return "transcription requested and mock done with audio file"
