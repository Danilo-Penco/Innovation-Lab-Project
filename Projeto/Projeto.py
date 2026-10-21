import reflex as rx

from Projeto.auth import (
    AuthInputError,
    DuplicateEmailError,
    account_exists,
    register_account,
    verify_credentials,
)
from Projeto.catalog import (
    CATALOG_GAMES,
    CatalogGame,
    build_catalog_comparison_url,
    build_steam_search_url,
    select_catalog_games,
)
from Projeto.gog import (
    GogMatchResult,
    GogOffer,
    GogServiceError,
    search_gog_offer,
)
from Projeto.steam import (
    InvalidSearchTerm,
    SteamGame,
    SteamPrice,
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
    selected_cover_url: str = ""
    search_error: str = ""
    price_error: str = ""
    price_status: str = ""
    price_cents: int = 0
    gog_title: str = ""
    gog_store_url: str = ""
    gog_cover_url: str = ""
    gog_status: str = ""
    gog_price_cents: int = 0
    gog_error: str = ""
    is_searching: bool = False
    is_loading_price: bool = False
    is_loading_gog: bool = False
    no_results: bool = False
    _search_request_id: int = 0
    _price_request_id: int = 0

    @rx.event
    async def set_search_term(self, value: str):
        await self._load_search_term(value)

    async def _load_search_term(self, term: str):
        self.search_term = term
        await self._start_search(term)

    @rx.event
    async def initialize_from_query(self):
        term = self.router.url.query_parameters.get("term", "")
        await self._load_search_term(term)

    async def _start_search(self, value: str):
        self.search_term = value
        self._search_request_id += 1
        request_id = self._search_request_id
        self._price_request_id += 1
        self.games = []
        self.no_results = False
        self.search_error = ""
        self.is_searching = False
        self._clear_comparison()

        if not value.strip():
            return

        try:
            term = validate_search_term(value)
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

    def _clear_comparison(self):
        self.price_error = ""
        self.price_status = ""
        self.price_cents = 0
        self.selected_cover_url = ""
        self.gog_title = ""
        self.gog_store_url = ""
        self.gog_cover_url = ""
        self.gog_status = ""
        self.gog_price_cents = 0
        self.gog_error = ""
        self.selected_app_id = 0
        self.selected_name = ""
        self.is_loading_price = False
        self.is_loading_gog = False

    @rx.var
    def formatted_price(self) -> str:
        return format_brl(self.price_cents)

    @rx.var
    def formatted_gog_price(self) -> str:
        return format_brl(self.gog_price_cents)

    @rx.var
    def steam_cover_url(self) -> str:
        if self.selected_cover_url:
            return self.selected_cover_url
        return (
            "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/"
            f"{self.selected_app_id}/header.jpg"
        )

    @rx.var
    def steam_store_url(self) -> str:
        return f"https://store.steampowered.com/app/{self.selected_app_id}/"

    @rx.var
    def steam_is_cheapest(self) -> bool:
        return (
            self.price_status in ("paid", "free")
            and self.gog_status in ("paid", "free")
            and self.price_cents <= self.gog_price_cents
        )

    @rx.var
    def gog_is_cheapest(self) -> bool:
        return (
            self.price_status in ("paid", "free")
            and self.gog_status in ("paid", "free")
            and self.gog_price_cents <= self.price_cents
        )

    @rx.event
    def select_game(self, app_id: int):
        game = find_game_by_app_id(self.games, app_id)
        if game is None:
            self.search_error = "Selecione um jogo da lista de resultados."
            return

        return rx.redirect(f"/comparar?app_id={game.app_id}")

    @rx.event
    async def initialize_comparison(self):
        raw_app_id = self.router.url.query_parameters.get("app_id", "")
        await self._load_comparison_from_query(raw_app_id)

    async def _load_comparison_from_query(self, raw_app_id: str):
        try:
            app_id = int(raw_app_id)
        except (TypeError, ValueError):
            self._clear_comparison()
            self.price_error = "Jogo inválido. Volte à busca e selecione um resultado."
            return
        if app_id <= 0:
            self._clear_comparison()
            self.price_error = "Jogo inválido. Volte à busca e selecione um resultado."
            return

        await self._load_comparison(app_id)

    async def _load_comparison(self, app_id: int):
        self._price_request_id += 1
        request_id = self._price_request_id
        self._clear_comparison()
        self.selected_app_id = app_id
        self.is_loading_price = True

        try:
            steam_result = await get_steam_game_price(app_id)
        except SteamServiceError as error:
            if request_id == self._price_request_id:
                self.price_error = str(error)
            return
        finally:
            if request_id == self._price_request_id:
                self.is_loading_price = False

        if request_id != self._price_request_id or self.selected_app_id != app_id:
            return

        self._apply_steam_price(steam_result)
        self.is_loading_gog = True

        try:
            gog_result = await search_gog_offer(steam_result.name)
        except GogServiceError:
            if request_id == self._price_request_id:
                self.gog_error = (
                    "A comparação com a GOG está indisponível no momento."
                )
        else:
            if (
                request_id != self._price_request_id
                or self.selected_app_id != app_id
            ):
                return
            if gog_result.status == "not_found":
                self.gog_error = "Jogo não encontrado na GOG."
            elif gog_result.status == "ambiguous":
                self.gog_error = "Mais de uma possível correspondência na GOG."
            elif (
                gog_result.offer is not None
                and gog_result.offer.status == "unavailable"
            ):
                self.gog_error = "Sem preço em BRL na GOG."
            elif gog_result.offer is not None:
                self._apply_gog_offer(gog_result.offer)
            else:
                self.gog_error = "A comparação com a GOG está indisponível no momento."
        finally:
            if request_id == self._price_request_id:
                self.is_loading_gog = False

    def _apply_steam_price(self, price: SteamPrice):
        self.price_status = price.status
        self.price_cents = price.final_price_minor or 0
        self.selected_cover_url = price.header_image
        if price.name:
            self.selected_name = price.name

    def _apply_gog_offer(self, offer: GogOffer):
        self.gog_title = offer.title
        self.gog_store_url = offer.store_url
        self.gog_cover_url = offer.cover_url
        self.gog_status = offer.status
        self.gog_price_cents = offer.final_price_minor or 0


class AuthState(rx.State):
    email: str = ""
    password: str = ""
    auth_error: str = ""
    is_splash_visible: bool = False
    is_submitting: bool = False
    _user_id: int | None = None
    _catalog_authorized: bool = False

    @rx.var
    def catalog_authorized(self) -> bool:
        return self._catalog_authorized

    @rx.var
    def is_authenticated(self) -> bool:
        return isinstance(self._user_id, int) and not isinstance(self._user_id, bool)

    @rx.event
    def set_email(self, value: str):
        self.email = value
        self.auth_error = ""

    @rx.event
    def set_password(self, value: str):
        self.password = value
        self.auth_error = ""

    @rx.event
    def open_register(self):
        self.auth_error = ""
        self.password = ""
        return rx.redirect("/cadastro")

    @rx.event
    def open_login(self):
        self.auth_error = ""
        self.password = ""
        return rx.redirect("/")

    @rx.event
    def prepare_form(self):
        self.auth_error = ""
        self.password = ""

    @rx.event
    def logout(self):
        self._user_id = None
        self._catalog_authorized = False
        self.is_splash_visible = False
        self.is_submitting = False
        self.email = ""
        self.password = ""
        self.auth_error = ""
        return rx.redirect("/")

    def _start_authenticated_transition(self, user_id: int):
        self._user_id = user_id
        self._catalog_authorized = False
        self.password = ""
        self.auth_error = ""
        self.is_submitting = False
        self.is_splash_visible = True
        return rx.call_script(
            "setTimeout(() => window.location.assign('/catalogo'), 900);"
        )

    @rx.event
    def login(self):
        self.auth_error = ""
        self.is_submitting = True
        self._user_id = None
        user_id = verify_credentials(self.email, self.password)
        if user_id is None:
            self.password = ""
            self.is_submitting = False
            self.auth_error = "E-mail ou senha inválidos."
            return
        return self._start_authenticated_transition(user_id)

    @rx.event
    def register(self):
        self.auth_error = ""
        self.is_submitting = True
        self._user_id = None
        try:
            user_id = register_account(self.email, self.password)
        except (AuthInputError, DuplicateEmailError) as error:
            self.password = ""
            self.is_submitting = False
            self.auth_error = str(error)
            return
        return self._start_authenticated_transition(user_id)

    @rx.event
    def guard_catalog(self):
        user_id = self._user_id
        if (
            not isinstance(user_id, int)
            or isinstance(user_id, bool)
            or not account_exists(user_id)
        ):
            self._user_id = None
            self._catalog_authorized = False
            return rx.redirect("/")
        self._catalog_authorized = True
        self.is_splash_visible = False


class CatalogState(rx.State):
    search_term: str = ""
    search_error: str = ""
    visible_app_ids: list[int] = []
    featured_app_id: int = 0

    @rx.event
    def prepare_page(self):
        self.search_error = ""
        selected, featured = select_catalog_games()
        self.visible_app_ids = [game.app_id for game in selected]
        self.featured_app_id = featured.app_id

    @rx.event
    def set_search_term(self, value: str):
        self.search_term = value
        self.search_error = ""

    @rx.event
    def search(self):
        try:
            search_url = build_steam_search_url(self.search_term)
        except InvalidSearchTerm as error:
            self.search_error = str(error)
            return
        return rx.redirect(search_url)


# Estilo global: fade-in suave ao carregar a página
GLOBAL_CSS = """
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
.fade-in {
    animation: fadeIn 0.5s ease-out;
}
@keyframes glow {
    0%, 100% { box-shadow: 0 0 22px rgba(139, 92, 246, 0.18); }
    50% { box-shadow: 0 0 42px rgba(139, 92, 246, 0.48); }
}
.auth-card {
    animation: fadeIn 0.5s ease-out, glow 2.4s ease-in-out infinite;
}
@media (max-height: 720px) {
    .auth-card {
        padding: 1rem !important;
    }
}
.price-comparison-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr));
    gap: 1rem;
    width: 100%;
}
"""


def navbar() -> rx.Component:
    return rx.hstack(
        rx.link(
            rx.hstack(
                rx.icon("gamepad-2", color="var(--violet-9)", size=22),
                rx.text("ComparaKeys", weight="bold", size="4"),
                align="center",
                spacing="2",
            ),
            href="/catalogo",
            color="inherit",
            text_decoration="none",
        ),
        rx.spacer(),
        rx.cond(
            AuthState.is_authenticated,
            rx.button(
                "Sair",
                on_click=AuthState.logout,
                variant="outline",
                size="2",
                style={
                    "cursor": "pointer",
                    "_hover": {"background_color": "var(--violet-3)"},
                },
            ),
            rx.button(
                "Entrar",
                on_click=rx.redirect("/"),
                variant="outline",
                size="2",
                style={
                    "cursor": "pointer",
                    "_hover": {"background_color": "var(--violet-3)"},
                },
            ),
        ),
        width="100%",
        padding="1rem 2rem",
        align="center",
        border_bottom="1px solid var(--gray-5)",
    )


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
        style={
            "cursor": "pointer",
            "transition": "all 0.15s ease",
            "_hover": {
                "background_color": "var(--violet-3)",
                "border_color": "var(--violet-8)",
                "transform": "translateY(-1px)",
            },
        },
    )


def price_comparison() -> rx.Component:
    return rx.vstack(
        rx.cond(
            SearchState.is_loading_price | SearchState.is_loading_gog,
            rx.hstack(
                rx.spinner(),
                rx.text("Consultando preços atuais na Steam e na GOG..."),
                align="center",
            ),
            rx.fragment(),
        ),
        rx.box(
            rx.card(
                rx.vstack(
                    rx.text("STEAM", size="2", weight="bold", color="gray"),
                    rx.image(
                        src=SearchState.steam_cover_url,
                        alt=f"Capa de {SearchState.selected_name}",
                        width="100%",
                        height="170px",
                        object_fit="cover",
                        border_radius="12px",
                        background="linear-gradient(135deg, #39235c, #130e1c)",
                    ),
                    rx.link(
                        SearchState.selected_name,
                        href=SearchState.steam_store_url,
                        is_external=True,
                        rel="noopener noreferrer",
                        color="#c4b5fd",
                        weight="bold",
                        size="4",
                    ),
                    rx.cond(
                        SearchState.price_status == "paid",
                        rx.heading(
                            SearchState.formatted_price,
                            size="7",
                            color=rx.cond(
                                SearchState.steam_is_cheapest,
                                "#4ade80",
                                "white",
                            ),
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        SearchState.price_status == "free",
                        rx.hstack(
                            rx.text("Grátis —"),
                            rx.text(
                                SearchState.formatted_price,
                                color=rx.cond(
                                    SearchState.steam_is_cheapest,
                                    "#4ade80",
                                    "white",
                                ),
                            ),
                        ),
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
                    align="stretch",
                    width="100%",
                    spacing="3",
                ),
                width="100%",
                height="100%",
                background="rgba(17, 13, 26, 0.94)",
                border="1px solid #48336a",
            ),
            rx.cond(
                (SearchState.gog_status == "paid")
                | (SearchState.gog_status == "free"),
                rx.card(
                    rx.vstack(
                        rx.text("GOG", size="2", weight="bold", color="gray"),
                        rx.image(
                            src=SearchState.gog_cover_url,
                            alt=f"Capa de {SearchState.gog_title}",
                            width="100%",
                            height="170px",
                            object_fit="cover",
                            border_radius="12px",
                            background="linear-gradient(135deg, #39235c, #130e1c)",
                        ),
                        rx.link(
                            SearchState.gog_title,
                            href=SearchState.gog_store_url,
                            is_external=True,
                            rel="noopener noreferrer",
                            color="#c4b5fd",
                            weight="bold",
                            size="4",
                        ),
                        rx.cond(
                            SearchState.gog_status == "paid",
                            rx.heading(
                                SearchState.formatted_gog_price,
                                size="7",
                                color=rx.cond(
                                    SearchState.gog_is_cheapest,
                                    "#4ade80",
                                    "white",
                                ),
                            ),
                            rx.fragment(),
                        ),
                        rx.cond(
                            SearchState.gog_status == "free",
                            rx.hstack(
                                rx.text("Grátis —"),
                                rx.text(
                                    SearchState.formatted_gog_price,
                                    color=rx.cond(
                                        SearchState.gog_is_cheapest,
                                        "#4ade80",
                                        "white",
                                    ),
                                ),
                            ),
                            rx.fragment(),
                        ),
                        align="stretch",
                        width="100%",
                        spacing="3",
                    ),
                    width="100%",
                    height="100%",
                    background="rgba(17, 13, 26, 0.94)",
                    border="1px solid #48336a",
                ),
                rx.fragment(),
            ),
            class_name="price-comparison-grid",
        ),
        rx.cond(
            SearchState.price_error != "",
            rx.text(SearchState.price_error, color="tomato", role="alert"),
            rx.fragment(),
        ),
        rx.cond(
            SearchState.gog_error != "",
            rx.text(SearchState.gog_error, color="gray", role="status"),
            rx.fragment(),
        ),
        align="stretch",
        width="100%",
        spacing="3",
    )


def catalog_game_card(game: CatalogGame, featured: bool = False) -> rx.Component:
    cover_height = "320px" if featured else "170px"
    return rx.link(
        rx.box(
            rx.box(
                rx.image(
                    src=game.cover_url,
                    alt=f"Capa de {game.name}",
                    id=f"catalog-cover-{game.app_id}",
                    width="100%",
                    height=cover_height,
                    object_fit="cover",
                    border_radius="14px",
                    background="linear-gradient(135deg, #39235c, #130e1c)",
                    loading="lazy",
                ),
                rx.center(
                    rx.text(
                        game.name,
                        color="white",
                        weight="medium",
                        size="5" if featured else "3",
                        text_align="center",
                        padding="1rem",
                    ),
                    width="100%",
                    height=cover_height,
                    border_radius="14px",
                    background="linear-gradient(135deg, #39235c, #130e1c)",
                    id=f"catalog-fallback-{game.app_id}",
                    display="none",
                    role="img",
                    aria_label=f"Capa indisponível: {game.name}",
                ),
                position="relative",
                width="100%",
            ),
            rx.text(
                game.name,
                color="white",
                weight="medium",
                size="6" if featured else "4",
                margin_top="0.8rem",
            ),
            width="100%",
            padding="1rem" if featured else "0.85rem",
            border="1px solid #48336a",
            border_radius="18px",
            background="rgba(17, 13, 26, 0.94)",
            box_shadow="0 0 34px rgba(139, 92, 246, 0.22)" if featured else "none",
        ),
        href=build_catalog_comparison_url(game.app_id),
        width="100%",
        aria_label=f"Comparar preços de {game.name}",
        text_decoration="none",
        color="inherit",
    )


def steam_search() -> rx.Component:
    return rx.fragment(
        rx.html(f"<style>{GLOBAL_CSS}</style>"),
        rx.vstack(
            navbar(),
            rx.center(
                rx.box(
                    rx.vstack(
                        rx.text(
                            "COMPARAKEYS",
                            size="2",
                            weight="bold",
                            color="violet",
                            letter_spacing="0.1em",
                        ),
                        rx.heading("Encontre seu próximo jogo", size="8"),
                        rx.text(
                            "Digite para encontrar jogos e comparar preços atuais no Brasil.",
                            color="gray",
                            size="4",
                        ),
                        rx.input(
                            value=SearchState.search_term,
                            on_change=SearchState.set_search_term,
                            placeholder="Digite o nome de um jogo",
                            aria_label="Nome do jogo",
                            max_length=100,
                            size="3",
                            width="100%",
                        ),
                        rx.cond(
                            SearchState.is_searching,
                            rx.hstack(
                                rx.spinner(),
                                rx.text("Buscando jogos na Steam..."),
                                align="center",
                            ),
                            rx.fragment(),
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
                        align="stretch",
                        spacing="5",
                        width="100%",
                    ),
                    max_width="920px",
                    width="100%",
                    padding="2rem",
                    class_name="fade-in",
                ),
                width="100%",
                padding="1rem",
            ),
            width="100%",
            spacing="0",
        ),
    )


def price_comparison_page() -> rx.Component:
    return rx.fragment(
        rx.html(f"<style>{GLOBAL_CSS}</style>"),
        rx.vstack(
            navbar(),
            rx.center(
                rx.box(
                    rx.vstack(
                        rx.button(
                            "Voltar à busca",
                            on_click=rx.redirect("/buscar"),
                            variant="outline",
                            size="2",
                            align_self="start",
                        ),
                        rx.heading("Comparação de preços", size="7"),
                        rx.cond(
                            SearchState.selected_name != "",
                            rx.text(SearchState.selected_name, color="gray"),
                            rx.fragment(),
                        ),
                        price_comparison(),
                        align="stretch",
                        spacing="5",
                        width="100%",
                    ),
                    max_width="920px",
                    width="100%",
                    padding="2rem",
                    class_name="fade-in",
                ),
                width="100%",
                padding="1rem",
            ),
            width="100%",
            spacing="0",
        ),
    )


def auth_brand(clickable: bool = False) -> rx.Component:
    brand = rx.vstack(
        rx.icon("gamepad-2", size=38, color="#a78bfa"),
        rx.text(
            "COMPARAKEYS",
            size="2",
            weight="bold",
            color="#c4b5fd",
            letter_spacing="0.18em",
        ),
        align="center",
        spacing="2",
    )
    if clickable:
        return rx.link(
            brand,
            href="/catalogo",
            color="inherit",
            text_decoration="none",
        )
    return brand


def splash_screen() -> rx.Component:
    return rx.center(
        rx.vstack(
            auth_brand(),
            rx.spinner(size="3", color="#c4b5fd"),
            rx.text("Preparando seu catálogo...", color="#c4b5fd"),
            align="center",
            spacing="5",
        ),
        width="100%",
        min_height="100vh",
        padding="1.5rem",
        background="radial-gradient(circle at center, #24133f 0%, #0b0910 58%, #050407 100%)",
    )


def login_card() -> rx.Component:
    return rx.box(
        rx.vstack(
            auth_brand(),
            rx.heading("Bem-vindo de volta", size="6", color="white"),
            rx.text(
                "Entre para continuar para o ComparaKeys.",
                color="#b8afc8",
                text_align="center",
            ),
            rx.vstack(
                rx.text("E-mail", color="#e9ddff", size="2", weight="medium"),
                rx.input(
                    value=AuthState.email,
                    on_change=AuthState.set_email,
                    placeholder="voce@exemplo.com",
                    aria_label="E-mail",
                    type="email",
                    max_length=254,
                    width="100%",
                    size="3",
                ),
                rx.text("Senha", color="#e9ddff", size="2", weight="medium"),
                rx.input(
                    value=AuthState.password,
                    on_change=AuthState.set_password,
                    placeholder="Sua senha",
                    aria_label="Senha",
                    type="password",
                    max_length=128,
                    width="100%",
                    size="3",
                ),
                rx.button(
                    "Cadastrar-se",
                    on_click=AuthState.open_register,
                    variant="outline",
                    width="100%",
                    size="3",
                    color_scheme="violet",
                    cursor="pointer",
                ),
                rx.button(
                    rx.cond(AuthState.is_submitting, "Entrando...", "Entrar"),
                    on_click=AuthState.login,
                    is_disabled=AuthState.is_submitting,
                    width="100%",
                    size="3",
                    color_scheme="violet",
                    cursor="pointer",
                ),
                rx.cond(
                    AuthState.auth_error != "",
                    rx.text(
                        AuthState.auth_error,
                        role="alert",
                        color="#fca5a5",
                        size="2",
                    ),
                    rx.fragment(),
                ),
                width="100%",
                align="stretch",
                spacing="3",
            ),
            width="100%",
            align="center",
            spacing="4",
        ),
        width="100%",
        max_width="440px",
        padding="clamp(1rem, 3vh, 1.5rem)",
        border="1px solid #48336a",
        border_radius="24px",
        background="rgba(17, 13, 26, 0.94)",
        class_name="auth-card",
    )


def register_card() -> rx.Component:
    return rx.box(
        rx.vstack(
            auth_brand(clickable=True),
            rx.heading("Crie sua conta", size="6", color="white"),
            rx.text(
                "Use seu e-mail e uma senha para se cadastrar.",
                color="#b8afc8",
                text_align="center",
            ),
            rx.vstack(
                rx.text("E-mail", color="#e9ddff", size="2", weight="medium"),
                rx.input(
                    value=AuthState.email,
                    on_change=AuthState.set_email,
                    placeholder="voce@exemplo.com",
                    aria_label="E-mail",
                    type="email",
                    max_length=254,
                    width="100%",
                    size="3",
                ),
                rx.text("Senha", color="#e9ddff", size="2", weight="medium"),
                rx.input(
                    value=AuthState.password,
                    on_change=AuthState.set_password,
                    placeholder="Mínimo de 8 caracteres",
                    aria_label="Senha",
                    type="password",
                    min_length=8,
                    max_length=128,
                    width="100%",
                    size="3",
                ),
                rx.button(
                    rx.cond(
                        AuthState.is_submitting,
                        "Cadastrando...",
                        "Cadastrar-se",
                    ),
                    on_click=AuthState.register,
                    is_disabled=AuthState.is_submitting,
                    width="100%",
                    size="3",
                    color_scheme="violet",
                    cursor="pointer",
                ),
                rx.cond(
                    AuthState.auth_error != "",
                    rx.text(
                        AuthState.auth_error,
                        role="alert",
                        color="#fca5a5",
                        size="2",
                    ),
                    rx.fragment(),
                ),
                rx.link(
                    "Voltar para login",
                    on_click=AuthState.open_login,
                    color="#c4b5fd",
                    align_self="center",
                    margin_top="0.5rem",
                ),
                width="100%",
                align="stretch",
                spacing="3",
            ),
            width="100%",
            align="center",
            spacing="4",
        ),
        width="100%",
        max_width="440px",
        padding="clamp(1rem, 3vh, 1.5rem)",
        border="1px solid #48336a",
        border_radius="24px",
        background="rgba(17, 13, 26, 0.94)",
        class_name="auth-card",
    )


def login_page() -> rx.Component:
    return rx.fragment(
        rx.html(f"<style>{GLOBAL_CSS}</style>"),
        rx.cond(
            AuthState.is_splash_visible,
            splash_screen(),
            rx.center(
                login_card(),
                width="100%",
                min_height="100vh",
                padding="0.75rem",
                background="radial-gradient(circle at 50% 25%, #261442 0%, #0b0910 54%, #050407 100%)",
            ),
        ),
    )


def register_page() -> rx.Component:
    return rx.fragment(
        rx.html(f"<style>{GLOBAL_CSS}</style>"),
        rx.cond(
            AuthState.is_splash_visible,
            splash_screen(),
            rx.center(
                register_card(),
                width="100%",
                min_height="100vh",
                padding="0.75rem",
                background="radial-gradient(circle at 50% 25%, #261442 0%, #0b0910 54%, #050407 100%)",
            ),
        ),
    )


def catalog_page() -> rx.Component:
    return rx.fragment(
        rx.html(f"<style>{GLOBAL_CSS}</style>"),
        rx.script(src="/catalog-image-fallback.js"),
        rx.cond(
            AuthState.catalog_authorized,
            rx.vstack(
                navbar(),
                rx.center(
                    rx.vstack(
                        rx.hstack(
                            rx.input(
                                value=CatalogState.search_term,
                                on_change=CatalogState.set_search_term,
                                placeholder="Comparar Preços",
                                aria_label="Comparar Preços",
                                max_length=100,
                                size="3",
                                width="100%",
                            ),
                            rx.button(
                                "Buscar",
                                on_click=CatalogState.search,
                                size="3",
                                color_scheme="violet",
                                cursor="pointer",
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.cond(
                            CatalogState.search_error != "",
                            rx.text(
                                CatalogState.search_error,
                                role="alert",
                                color="#fca5a5",
                            ),
                            rx.fragment(),
                        ),
                        rx.heading("Jogos para descobrir", size="7", color="white"),
                        rx.text(
                            "Conheça alguns jogos e pesquise na Steam.",
                            color="#b8afc8",
                        ),
                        rx.box(
                            *[
                                rx.cond(
                                    CatalogState.featured_app_id == game.app_id,
                                    catalog_game_card(game, featured=True),
                                    rx.fragment(),
                                )
                                for game in CATALOG_GAMES
                            ],
                            width="100%",
                        ),
                        rx.grid(
                            *[
                                rx.cond(
                                    CatalogState.visible_app_ids.contains(game.app_id)
                                    & (CatalogState.featured_app_id != game.app_id),
                                    catalog_game_card(game),
                                    rx.fragment(),
                                )
                                for game in CATALOG_GAMES
                            ],
                            id="catalog-games-grid",
                            width="100%",
                            style={
                                "gridTemplateColumns": (
                                    "repeat(auto-fit, minmax(min(100%, 220px), 1fr))"
                                ),
                                "gap": "1rem",
                            },
                        ),
                        rx.hstack(
                            rx.text(
                                "ComparaKeys ajuda você a encontrar onde jogar pagando menos.",
                                color="#b8afc8",
                                size="2",
                            ),
                            rx.link(
                                "Buscar jogos",
                                href="/buscar",
                                color="#c4b5fd",
                                weight="medium",
                            ),
                            id="catalog-footer",
                            width="100%",
                            justify="between",
                            align="center",
                            flex_wrap="wrap",
                            border_top="1px solid #48336a",
                            padding_top="1rem",
                            margin_top="1rem",
                        ),
                        width="100%",
                        max_width="1100px",
                        padding="2rem 1.25rem",
                        align="stretch",
                        spacing="4",
                    ),
                    width="100%",
                    flex="1",
                ),
                width="100%",
                min_height="100vh",
                background="radial-gradient(circle at 50% 25%, #261442 0%, #0b0910 54%, #050407 100%)",
                spacing="0",
            ),
            rx.center(
                rx.spinner(size="3", color="#c4b5fd"),
                width="100%",
                min_height="100vh",
                background="#08060c",
            ),
        ),
    )


app = rx.App(theme=rx.theme(accent_color="violet", radius="large", appearance="dark"))
app.add_page(login_page, route="/", on_load=AuthState.prepare_form)
app.add_page(register_page, route="/cadastro", on_load=AuthState.prepare_form)
app.add_page(
    catalog_page,
    route="/catalogo",
    on_load=[AuthState.guard_catalog, CatalogState.prepare_page],
)
app.add_page(steam_search, route="/buscar", on_load=SearchState.initialize_from_query)
app.add_page(
    price_comparison_page,
    route="/comparar",
    on_load=SearchState.initialize_comparison,
)