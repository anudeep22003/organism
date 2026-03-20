from .exception import NotFoundError
from .repository_old import RepositoryOld as Repository

__all__ = [
    "Repository",
    "NotFoundError",
]
