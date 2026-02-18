import uuid

from .exceptions import InvalidUserIDError, NotFoundError, NotOwnedError
from .repository import Repository
from .schemas.story import GenerateStoryRequest


class Service:
    def __init__(self, repository: Repository):
        self.repository = repository

    def _get_user_id(self, user_id: str) -> uuid.UUID:
        """
        Convert user ID string to UUID.

        Internal user_id is _user_id to avoid shadowing the parameter.
        It is always guaranteed to be a valid UUID.
        """
        try:
            return uuid.UUID(user_id)
        except ValueError:
            raise InvalidUserIDError(f"Invalid user ID: {user_id}")

    async def check_story_ownership(
        self, _user_id: uuid.UUID, story_id: uuid.UUID
    ) -> None:
        story = await self.repository.get_story_with_project(story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")
        if story.project.user_id != _user_id:
            raise NotOwnedError(f"User {_user_id} does not own story {story_id}")

    async def generate_story(
        self, user_id: str, story_id: uuid.UUID, request: GenerateStoryRequest
    ) -> None:
        _user_id = self._get_user_id(user_id)
        await self.check_story_ownership(_user_id, story_id)
        return None
