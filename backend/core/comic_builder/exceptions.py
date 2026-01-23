class ComicBuilderError(Exception):
    """Base for domain errors that callers handle specifically."""

    pass


class ProjectNotFoundError(ComicBuilderError):
    """Project does not exist in database."""

    pass
