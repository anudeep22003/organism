import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, Protocol, Type, TypeVar

from loguru import logger
from pydantic import BaseModel, ValidationError

from core.sockets.types.envelope import (
    AckFail,
    AckOk,
    Actor,
    Envelope,
    Error,
)
from core.sockets.types.intlligence_models import ModelsEnum
from core.sockets.types.message import Message

DEFAULT_MODEL = ModelsEnum.GPT_4O

if TYPE_CHECKING:
    from socketio import AsyncServer

logger = logger.bind(name=__name__)

T = TypeVar("T", bound=BaseModel)


class StreamChunks(Protocol):
    async def __call__(
        self,
        target_room: str,
        data: list[Message],
        request_id: str,
        stream_id: str,
        actor: Actor,
        model: ModelsEnum,
        sio: "AsyncServer",
    ) -> str: ...


class BaseActor(ABC, Generic[T]):
    def __init__(
        self,
        actor_name: Actor,
        stream_chunks: StreamChunks,
        model: ModelsEnum = DEFAULT_MODEL,
    ):
        self.actor_name = actor_name
        self.model = model
        self.stream_chunks = stream_chunks

    @abstractmethod
    def prepare_messages(self, validated_request: T) -> list[Message]: ...

    def _validate_envelope(
        self, envelope: dict, data_type: Type[T]
    ) -> Envelope[T] | Error:
        try:
            validated_envelope = Envelope[data_type].model_validate(envelope)  # type: ignore[valid-type]
            return validated_envelope
        except ValidationError:
            return Error(
                code="E_INVALID",
                message="The envelope is not in the correct format",
            )
        except Exception as e:
            raise Exception("unknown error while validating envelope") from e

    def _ack_success(self, request_id: str, stream_id: str) -> str:
        return AckOk(
            ok=True,
            request_id=request_id,
            stream_id=stream_id,
        ).model_dump_json()

    def _ack_fail(self, message: str) -> str:
        return AckFail(
            ok=False,
            error=Error(
                code="invalid_envelope",
                message=message,
            ),
        ).model_dump_json()

    def _create_stream_task(
        self,
        sid: str,
        prepared_messages: list[Message],
        request_id: str,
        stream_id: str,
        sio: "AsyncServer",
    ) -> None:
        asyncio.create_task(
            self.stream_chunks(
                sid,
                prepared_messages,
                request_id,
                stream_id,
                actor=self.actor_name,
                model=self.model,
                sio=sio,
            )
        )

    def handle_stream_start(
        self, sid: str, envelope: dict, data_type: Type[T], sio: "AsyncServer"
    ) -> str:
        validated_envelope = self._validate_envelope(envelope, data_type)

        if isinstance(validated_envelope, Error):
            return self._ack_fail(validated_envelope.message)

        if validated_envelope.request_id is None:
            return self._ack_fail("The envelope is missing request_id")

        stream_id = str(uuid.uuid4())

        prepared_messages = self.prepare_messages(validated_envelope.data)

        self._create_stream_task(
            sid,
            prepared_messages,
            validated_envelope.request_id,
            stream_id,
            sio,
        )

        return self._ack_success(validated_envelope.request_id, stream_id)
