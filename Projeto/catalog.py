"""Static catalog examples and safe navigation to the public Steam search."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

from Projeto.steam import validate_search_term


@dataclass(frozen=True)
class CatalogGame:
    name: str
    app_id: int

    @property
    def cover_url(self) -> str:
        return (
            "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/"
            f"{self.app_id}/header.jpg"
        )


CATALOG_GAMES = (
    CatalogGame(name="Portal 2", app_id=620),
    CatalogGame(name="Dota 2", app_id=570),
    CatalogGame(name="Team Fortress 2", app_id=440),
    CatalogGame(name="The Witcher 3: Wild Hunt", app_id=292030),
)


def build_steam_search_url(term: str) -> str:
    normalized_term = validate_search_term(term)
    return f"/buscar?{urlencode({'term': normalized_term})}"
