import reflex as rx

from Projeto.steam import (
    InvalidSearchTerm,
    SteamGame,
    SteamServiceError,
    find_game_by_app_id,
    format_brl,
    get_steam_game_price,
    search_steam_games,
    validate_search_term,
)


class SearchState(rx.State):
    search_term: str = ""
    games: list[SteamGame] = []
    selected_app_id: int = 0
    selected_name: str = ""
    search_error: str = ""
    price_error: str = ""
    price_status: str = ""
    price_cents: int = 0
    is_searching: bool = False
    is_loading_price: bool = False
    no_results: bool = False
    _search_request_id: int = 0
    _price_request_id: int = 0

    @rx.event
    def set_search_term(self, value: str):
        self.search_term = value

    @rx.var
    def formatted_price(self) -> str:
        return format_brl(self.price_cents)

    @rx.event
    async def search(self):
        self._search_request_id += 1
        request_id = self._search_request_id
        self._price_request_id += 1
        self.search_error = ""
        self.price_error = ""
        self.price_status = ""
        self.price_cents = 0
        self.selected_app_id = 0
        self.selected_name = ""
        self.games = []
        self.no_results = False
        self.is_searching = False
        self.is_loading_price = False

        try:
            term = validate_search_term(self.search_term)
        except InvalidSearchTerm as error:
            self.search_error = str(error)
            return

        self.is_searching = True
        try:
            games = await search_steam_games(term)
        except SteamServiceError as error:
            if request_id == self._search_request_id:
                self.search_error = str(error)
                self.is_searching = False
            return

        if request_id != self._search_request_id:
            return
        self.games = games
        self.no_results = not games
        self.is_searching = False

    @rx.event
    async def select_game(self, app_id: int):
        game = find_game_by_app_id(self.games, app_id)
        if game is None:
            self.price_error = "Selecione um jogo da lista de resultados."
            return

        self._price_request_id += 1
        request_id = self._price_request_id
        self.selected_app_id = game.app_id
        self.selected_name = game.name
        self.price_error = ""
        self.price_status = ""
        self.price_cents = 0
        self.is_loading_price = True

        try:
            price = await get_steam_game_price(game.app_id)
        except SteamServiceError as error:
            if request_id == self._price_request_id:
                self.price_error = str(error)
                self.is_loading_price = False
            return

        if (
            request_id != self._price_request_id
            or self.selected_app_id != game.app_id
        ):
            return
        self.price_status = price.status
        self.price_cents = price.final_price_minor or 0
        if price.name:
            self.selected_name = price.name
        self.is_loading_price = False


def game_result(game: SteamGame) -> rx.Component:
    return rx.button(
        rx.hstack(
            rx.text(game.name, weight="medium"),
            rx.text(f"App ID {game.app_id}", color="gray"),
            justify="between",
            width="100%",
        ),
        on_click=SearchState.select_game(game.app_id),
        variant="outline",
        size="3",
        width="100%",
    )


def index() -> rx.Component:
    return rx.center(
        rx.box(
            rx.vstack(
                rx.text("COMPARAKEYS", size="2", weight="bold", color="violet"),
                rx.heading("Encontre seu próximo jogo", size="8"),
                rx.text(
                    "Pesquise na Steam e consulte o preço atual para o Brasil.",
                    color="gray",
                    size="4",
                ),
                rx.hstack(
                    rx.input(
                        value=SearchState.search_term,
                        on_change=SearchState.set_search_term,
                        placeholder="Digite o nome de um jogo",
                        aria_label="Nome do jogo",
                        max_length=100,
                        size="3",
                        width="100%",
                    ),
                    rx.button(
                        rx.cond(SearchState.is_searching, "Buscando...", "Buscar"),
                        on_click=SearchState.search,
                        is_disabled=SearchState.is_searching,
                        size="3",
                    ),
                    align="center",
                    width="100%",
                ),
                rx.cond(
                    SearchState.search_error != "",
                    rx.text(SearchState.search_error, color="tomato"),
                    rx.fragment(),
                ),
                rx.cond(
                    SearchState.no_results,
                    rx.text("Nenhum jogo encontrado. Tente outro nome.", color="gray"),
                    rx.fragment(),
                ),
                rx.cond(
                    SearchState.games.length() > 0,
                    rx.vstack(
                        rx.heading("Escolha o jogo", size="4"),
                        rx.foreach(SearchState.games, game_result),
                        align="stretch",
                        width="100%",
                        spacing="2",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    SearchState.selected_app_id > 0,
                    rx.card(
                        rx.vstack(
                            rx.text("PREÇO NA STEAM", size="2", weight="bold", color="gray"),
                            rx.heading(SearchState.selected_name, size="5"),
                            rx.cond(
                                SearchState.is_loading_price,
                                rx.hstack(
                                    rx.spinner(),
                                    rx.text("Consultando preço atual..."),
                                    align="center",
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                SearchState.price_status == "paid",
                                rx.heading(
                                    SearchState.formatted_price,
                                    size="7",
                                    color="green",
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                SearchState.price_status == "free",
                                rx.text("Gratuito na Steam", color="green"),
                                rx.fragment(),
                            ),
                            rx.cond(
                                SearchState.price_status == "unavailable",
                                rx.text(
                                    "Preço em BRL indisponível para este jogo.",
                                    color="gray",
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                SearchState.price_error != "",
                                rx.text(SearchState.price_error, color="tomato"),
                                rx.fragment(),
                            ),
                            align="start",
                            width="100%",
                            spacing="3",
                        ),
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                align="stretch",
                spacing="5",
                width="100%",
            ),
            max_width="720px",
            width="100%",
            padding="2rem",
        ),
        min_height="100vh",
        padding="1rem",
    )


app = rx.App()
app.add_page(index)
