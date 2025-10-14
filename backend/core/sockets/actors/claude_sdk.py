import asyncio
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

from claude_code_sdk import (
    ClaudeCodeOptions,
    ClaudeSDKClient,
    ContentBlock,
    TextBlock,
    ToolUseBlock,
)
from claude_code_sdk import Message as ClaudeSDKMessage
from loguru import logger
from pydantic import Field, ValidationError

from core.sockets.types.envelope import AckFail, AckOk, AliasedBaseModel, Envelope, Error

from .. import sio

logger = logger.bind(name=__name__)


class ClaudeSDKRequest(AliasedBaseModel):
    query: str = Field(description="The query for Claude SDK")


DATA_DIR = Path("data")


class ClaudeSDKActor:
    def __init__(
        self,
        test: bool = False,
    ):
        self.actor_name = "claude"
        self.model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        self.operation_timeout = int(
            os.getenv("OPERATION_TIMEOUT", "3600")
        )  # 1 hour default
        self.test = test

    def handle_stream_start(self, sid: str, envelope: dict) -> str:
        try:
            validated_envelope = Envelope[ClaudeSDKRequest].model_validate(envelope)  # type: ignore

            if validated_envelope.request_id is None:
                return self._ack_fail("The envelope is missing request_id")

        except ValidationError:
            return self._ack_fail("The envelope is not in the correct format")

        stream_id = str(uuid.uuid4())

        if not validated_envelope.data.query:
            raise ValueError("Query is required")

        cwd = Path(tempfile.mkdtemp(dir="tmp"))
        asyncio.create_task(
            self.stream_claude_code_sdk_chunks(
                sid=sid,
                user_query=validated_envelope.data.query,
                request_id=validated_envelope.request_id,
                stream_id=stream_id,
                cwd=cwd,
            )
        )

        return AckOk(
            ok=True,
            request_id=validated_envelope.request_id,
            stream_id=stream_id,
        ).model_dump_json()

    def _ack_fail(self, message: str) -> str:
        """Create a standardized invalid envelope error response."""
        return AckFail(
            ok=False,
            error=Error(
                code="invalid_envelope",
                message=message,
            ),
        ).model_dump_json()

    async def stream_claude_code_sdk_chunks(
        self,
        sid: str,
        user_query: str,
        request_id: str,
        stream_id: str,
        cwd: Path,
        model: str = "claude-3-5-sonnet-20241022",
    ) -> None:
        """Stream Claude SDK chunks to the client."""
        cwd = cwd or Path.cwd()

        async with self._create_claude_client(cwd, model) as client:
            await client.query(user_query)
            stream = client.receive_response()
            await self._process_stream(stream, request_id, stream_id, sid)

    def _create_claude_client(self, cwd: Path, model: str) -> ClaudeSDKClient:
        """Create and configure a Claude SDK client."""
        return ClaudeSDKClient(
            ClaudeCodeOptions(
                model=model,
                cwd=cwd,
                allowed_tools=["Read", "Write", "Bash", "Grep"],
                disallowed_tools=["WebSearch", "Bash(rm -r*)"],
                permission_mode="acceptEdits",
                extra_args={
                    "verbose": "true",
                },
            )
        )

    async def _process_stream(
        self, stream, request_id: str, stream_id: str, sid: str
    ) -> None:
        """Process the stream of chunks from Claude SDK."""
        seq = 0
        async for chunk in stream:
            logger.info(f"Chunk: {chunk}")
            try:
                await self.chunk_processor(chunk, request_id, stream_id, sid, seq)
            except Exception as e:
                logger.error(f"Error in chunk processor: {e}")

    async def chunk_processor(
        self,
        chunk: ClaudeSDKMessage,
        request_id: str,
        stream_id: str,
        sid: str,
        seq: int,
    ) -> None:
        """Process individual chunks from Claude SDK."""
        if not hasattr(chunk, "content"):
            return

        for block in chunk.content:
            seq += 1
            await self._process_content_block(block, request_id, stream_id, sid, seq)

        if self._is_result_message(chunk):
            await self._send_stream_end(request_id, stream_id, sid, seq)

    async def _process_content_block(
        self,
        block: ContentBlock | str | Any,
        request_id: str,
        stream_id: str,
        sid: str,
        seq: int,
    ) -> None:
        """Process individual content blocks within a chunk."""
        if isinstance(block, TextBlock):
            await self._send_text_chunk(block.text, request_id, stream_id, sid, seq)
        elif isinstance(block, ToolUseBlock):
            await self._send_tool_use_chunk(
                block.input, request_id, stream_id, sid, seq
            )
        else:
            logger.info(f"Unhandled block type: {type(block)}")

    async def _send_text_chunk(
        self, text: str, request_id: str, stream_id: str, sid: str, seq: int
    ) -> None:
        """Send a text chunk to the client."""
        envelope = self._create_chunk_envelope(
            request_id, stream_id, seq, sid, {"delta": text}
        )
        await sio.emit("s2c.claude.stream.chunk", envelope, to=sid)

    async def _send_tool_use_chunk(
        self, tool_input: dict, request_id: str, stream_id: str, sid: str, seq: int
    ) -> None:
        """Send a tool use chunk to the client."""
        formatted_input = self._format_tool_input(tool_input)
        envelope = self._create_chunk_envelope(
            request_id, stream_id, seq, sid, {"delta": formatted_input}
        )
        await sio.emit("s2c.claude.stream.chunk", envelope, to=sid)

    def _format_tool_input(self, tool_input: dict) -> str:
        """Format tool input as a code block."""
        return "\n```json\n" + json.dumps(tool_input) + "\n```\n"

    def _create_chunk_envelope(
        self, request_id: str, stream_id: str, seq: int, sid: str, data: dict
    ) -> str:
        """Create a standardized chunk envelope."""
        envelope = Envelope(
            request_id=request_id,
            stream_id=stream_id,
            seq=seq,
            direction="s2c",
            actor="claude",
            action="stream",
            modifier="chunk",
            data=data,
        )
        return envelope.model_dump_json()

    def _is_result_message(self, chunk: ClaudeSDKMessage) -> bool:
        """Check if the chunk is a result message."""
        return type(chunk).__name__ == "ResultMessage"

    async def _send_stream_end(
        self, request_id: str, stream_id: str, sid: str, seq: int
    ) -> None:
        """Send stream end message to the client."""
        envelope = Envelope(
            request_id=request_id,
            stream_id=stream_id,
            seq=seq,
            direction="s2c",
            actor="claude",
            action="stream",
            modifier="end",
            data={"finish_reason": "stop"},
        )
        await sio.emit("s2c.claude.stream.end", envelope.model_dump_json(), to=sid)

    async def close_claude_stream(
        self, sid: str, request_id: str, stream_id: str
    ) -> None:
        """Close the Claude stream and notify the client."""
        logger.info(f"Closing Claude stream: {stream_id}")
        envelope = Envelope(
            request_id=request_id,
            stream_id=stream_id,
            direction="s2c",
            actor="claude",
            action="stream",
            modifier="end",
            data={"finish_reason": "stop"},
        )
        await sio.emit("s2c.claude.stream.end", envelope.model_dump_json(), to=sid)


@sio.on("c2s.claude.stream.start")
async def request_claude_stream(sid: str, envelope: dict) -> str:
    claude_sdk_actor = ClaudeSDKActor()
    return claude_sdk_actor.handle_stream_start(sid, envelope)
