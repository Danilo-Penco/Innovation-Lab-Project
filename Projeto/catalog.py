"""Static catalog examples and safe navigation to the public Steam search."""

from __future__ import annotations

import random
from dataclasses import dataclass
from random import Random
from urllib.parse import urlencode

from Projeto.steam import validate_search_term


CATALOG_DISPLAY_COUNT = 8


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
    CatalogGame(name="Stardew Valley", app_id=413150),
    CatalogGame(name="Hades", app_id=1145360),
    CatalogGame(name="Hollow Knight", app_id=367520),
    CatalogGame(name="Celeste", app_id=504230),
    CatalogGame(name="Terraria", app_id=105600),
    CatalogGame(name="The Elder Scrolls V: Skyrim Special Edition", app_id=489830),
    CatalogGame(name="ELDEN RING", app_id=1245620),
    CatalogGame(name="Baldur's Gate 3", app_id=1086940),
    CatalogGame(name="Cyberpunk 2077", app_id=1091500),
    CatalogGame(name="Slay the Spire", app_id=646570),
    CatalogGame(name="Left 4 Dead 2", app_id=550),
)


def select_catalog_games(
    rng: Random | None = None,
) -> tuple[tuple[CatalogGame, ...], CatalogGame]:
    """Choose a distinct sample and one featured game for a catalog load."""
    randomizer = rng or random.Random()
    selected = tuple(randomizer.sample(CATALOG_GAMES, k=CATALOG_DISPLAY_COUNT))
    return selected, randomizer.choice(selected)


def build_steam_search_url(term: str) -> str:
    normalized_term = validate_search_term(term)
    return f"/buscar?{urlencode({'term': normalized_term})}"


def build_catalog_comparison_url(app_id: int) -> str:
    if app_id <= 0:
        raise ValueError("O App ID Steam deve ser positivo.")
    return f"/comparar?{urlencode({'app_id': app_id})}"
