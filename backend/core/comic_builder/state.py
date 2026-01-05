import uuid
from typing import Any, Literal

from core.common import AliasedBaseModel

ContentStatus = Literal["idle", "streaming", "completed", "error"]


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


def init_comic_state() -> dict[str, Any]:
    return ComicState(
        phases=[
            ComicPhase(
                id=uuid.uuid4(),
                name="write-story",
                input_text="",
            ),
            ComicPhase(
                id=uuid.uuid4(),
                name="extract-characters",
                input_text="",
            ),
        ],
        current_phase_index=0,
    ).model_dump(by_alias=True)
