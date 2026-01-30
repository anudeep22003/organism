from uuid import UUID

from loguru import logger
from slugify import slugify

from .exceptions import CharacterNotFoundError
from .state import ConsolidatedComicState

type RegistryType = dict[UUID, str | None]


class AssetManager:
    def __init__(self, state: ConsolidatedComicState) -> None:
        self._id_to_url_map = self.build_id_to_url_map(state)
        self._name_to_id_map = self.build_name_to_id_map(state)

    def build_id_to_url_map(self, state: ConsolidatedComicState) -> RegistryType:
        asset_to_url_registry: RegistryType = {}
        for id, character in state.characters.items():
            if character.render:
                asset_to_url_registry[id] = character.render.url
            else:
                asset_to_url_registry[id] = None

        return asset_to_url_registry

    def build_name_to_id_map(self, state: ConsolidatedComicState) -> dict[str, UUID]:
        registry: dict[str, UUID] = {}
        for id, character in state.characters.items():
            sanitized_name = slugify(character.name)
            registry[sanitized_name] = id
        return registry

    # def sanitize_character_name(self, name: str) -> str:
    #     name = slugify(name)
    #     if name in self._name_to_id_map:
    #         counter = self.get_character_collision_count(name) + 1
    #         name = f"{name}-{counter}"
    #     return name

    # def get_character_collision_count(self, name: str) -> int:
    #     # get the last number in the name if it exists otherwise return 0
    #     count = name.split("-")[-1]
    #     if not count.isnumeric():
    #         return 0
    #     return int(count)

    def get_cast_list(self) -> list[str]:
        return list(self._name_to_id_map.keys())

    def get_url_for_character(self, name: str) -> str | None:
        sanitized_name = slugify(name)
        character_id = self._name_to_id_map.get(sanitized_name)
        if not character_id:
            raise CharacterNotFoundError(f"Character {name} not found")
        url = self._id_to_url_map[character_id]
        return url

    def get_urls_for_characters(self, names: list[str]) -> list[str]:
        character_urls = []
        missing_characters = []
        for name in names:
            url = self.get_url_for_character(name)
            if not url:
                missing_characters.append(name)
            else:
                character_urls.append(url)
        if missing_characters:
            logger.warning(
                "Evaluate if the below missing characters need generation...."
            )
            missing_characters_str = ", ".join(missing_characters)
            logger.warning(
                f"Characters {missing_characters_str} not found in asset manager, skipping..."
            )
        return character_urls
