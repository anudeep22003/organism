from typing import Literal, cast

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["user", "assistant", "human", "generative", "system"]
    content: str

    def to_openai_message(
        self,
    ) -> ChatCompletionMessageParam:
        if self.role == "generative":
            return cast(
                ChatCompletionMessageParam,
                {"role": "assistant", "content": self.content},
            )
        elif self.role == "human":
            return cast(
                ChatCompletionMessageParam, {"role": "user", "content": self.content}
            )
        else:
            return cast(
                ChatCompletionMessageParam, {"role": self.role, "content": self.content}
            )
