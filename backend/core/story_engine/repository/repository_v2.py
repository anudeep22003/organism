from sqlalchemy.ext.asyncio import AsyncSession

from .character_repository import CharacterRepository
from .edit_event_repository import EditEventRepository
from .image_repository import ImageRepository
from .panel_repository import PanelRepository
from .project_repository import ProjectRepository
from .story_repository import StoryRepository


class RepositoryV2:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.project = ProjectRepository(db)
        self.story = StoryRepository(db)
        self.character = CharacterRepository(db)
        self.edit_event = EditEventRepository(db)
        self.image = ImageRepository(db)
        self.panel = PanelRepository(db)
