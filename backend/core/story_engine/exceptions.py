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


class StoryGeneratorError(ComicBuilderError):
    """Error generating story."""

    pass


class StreamGeneratorError(ComicBuilderError):
    """Error streaming story."""

    pass


class CharacterNotFoundError(ComicBuilderError):
    """Character not found in asset manager."""

    pass


#############################################
############### New Errors ################
#############################################


class BaseError(Exception):
    """Base for domain errors that callers handle specifically."""

    pass


class DatabaseError(BaseError):
    """Error accessing the database."""

    pass


class NotFoundError(BaseError):
    """Resource not found."""

    pass


class NotOwnedError(BaseError):
    """User does not own the story."""

    pass


class InvalidUserIDError(BaseError):
    """Invalid user ID format."""

    pass


class NoStoryTextError(BaseError):
    """No story text available for story."""

    pass


class NoCharactersError(BaseError):
    """No characters extracted for story — extract characters before generating panels."""

    pass


class CharacterExtractionError(BaseError):
    """Error extracting characters from story."""


class CharacterRefinementError(BaseError):
    """Error refining a character."""

    pass


class FalResponseError(BaseError):
    """Error from Fal response."""

    pass


class UploadImageError(BaseError):
    """Error uploading image to bucket."""

    pass
