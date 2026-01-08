import uuid
from typing import Any, Literal

from core.common import AliasedBaseModel

ContentStatus = Literal["idle", "streaming", "completed", "error"]

PHASES: list[str] = ["write-story", "extract-characters"]


class ComicContent(AliasedBaseModel):
    id: uuid.UUID
    text: str
    type: Literal["text"] = "text"
    status: ContentStatus
    payload: list[dict]


class ComicPhase(AliasedBaseModel):
    id: uuid.UUID
    name: str
    input_text: str
    content: ComicContent | None = None


class ComicState(AliasedBaseModel):
    phases: list[ComicPhase]
    current_phase_index: int


class StateFactory:
    @staticmethod
    def init_empty_state() -> dict[str, Any]:
        return StateFactory.init_empty_comic_state().model_dump(by_alias=True)

    @staticmethod
    def init_empty_comic_content() -> ComicContent:
        return ComicContent(
            id=uuid.uuid4(),
            text="",
            type="text",
            status="idle",
            payload=[],
        )

    @staticmethod
    def init_empty_comic_phases(names: list[str]) -> list[ComicPhase]:
        return [
            ComicPhase(
                id=uuid.uuid4(),
                name=name,
                input_text="",
                content=StateFactory.init_empty_comic_content(),
            )
            for name in names
        ]

    @staticmethod
    def init_empty_comic_state() -> ComicState:
        return ComicState(
            phases=StateFactory.init_empty_comic_phases(PHASES),
            current_phase_index=0,
        )
