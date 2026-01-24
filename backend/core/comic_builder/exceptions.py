class ComicBuilderError(Exception):
    """Base for domain errors that callers handle specifically."""

    pass


class ProjectNotFoundError(ComicBuilderError):
    """Project does not exist in database."""

    pass


class CharacterExtractorError(ComicBuilderError):
    pass


class NoStoryError(ComicBuilderError):
    """No story available for project."""

    pass


class PanelGeneratorError(ComicBuilderError):
    """Error generating panel."""

    pass


class RenderError(ComicBuilderError):
    """External image generation failed."""

    pass
