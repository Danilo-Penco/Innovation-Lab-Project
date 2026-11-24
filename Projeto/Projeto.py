import asyncio
from dataclasses import replace

import reflex as rx

from Projeto import xano
from Projeto.catalog import (
    CATALOG_GAMES,
    CatalogGame,
    build_catalog_comparison_url,
    build_steam_search_url,
    select_catalog_games,
)
from Projeto.cheapshark import (
    CHEAPSHARK_CONVERSION_NOTICE,
    CHEAPSHARK_NO_OFFERS_MESSAGE,
    CHEAPSHARK_USD_FALLBACK_NOTICE,
    CheapSharkOffer,
    CheapSharkServiceError,
    search_cheapshark_offers,
)
from Projeto.gog import (
    GogMatchResult,
    GogOffer,
    GogServiceError,
    search_gog_offer,
)
from Projeto.price_metadata import (
    GOG_LOGO_URL,
    STEAM_LOGO_URL,
    format_price_timestamp,
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
from Projeto.theme import THEME_CSS

SESSION_EXPIRED_MESSAGE = "Sua sessão expirou. Entre novamente para continuar."


def _lowest_comparable_price(
    steam_status: str,
    steam_price_cents: int,
    gog_status: str,
    gog_price_cents: int,
    cheapshark_offers: list[CheapSharkOffer],
) -> int | None:
    prices: list[int] = []
    if steam_status in ("paid", "free"):
        prices.append(steam_price_cents)
    if gog_status in ("paid", "free"):
        prices.append(gog_price_cents)
    prices.extend(
        offer.price_brl_minor
        for offer in cheapshark_offers
        if offer.price_brl_minor is not None
    )
    return min(prices) if len(prices) > 1 else None


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
    gog_updated_label: str = ""
    gog_logo_url: str = GOG_LOGO_URL
    gog_retryable: bool = False
    cheapshark_offers: list[CheapSharkOffer] = []
    cheapshark_error: str = ""
    cheapshark_currency_notice: str = ""
    cheapshark_retryable: bool = False
    steam_updated_label: str = ""
    steam_logo_url: str = STEAM_LOGO_URL
    steam_retryable: bool = False
    is_searching: bool = False
    is_loading_price: bool = False
    is_loading_gog: bool = False
    is_loading_cheapshark: bool = False
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
        self.steam_updated_label = ""
        self.steam_logo_url = STEAM_LOGO_URL
        self.steam_retryable = False
        self.gog_title = ""
        self.gog_store_url = ""
        self.gog_cover_url = ""
        self.gog_status = ""
        self.gog_price_cents = 0
        self.gog_error = ""
        self.gog_updated_label = ""
        self.gog_logo_url = GOG_LOGO_URL
        self.gog_retryable = False
        self.cheapshark_offers = []
        self.cheapshark_error = ""
        self.cheapshark_currency_notice = ""
        self.cheapshark_retryable = False
        self.selected_app_id = 0
        self.selected_name = ""
        self.is_loading_price = False
        self.is_loading_gog = False
        self.is_loading_cheapshark = False

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
        lowest = _lowest_comparable_price(
            self.price_status,
            self.price_cents,
            self.gog_status,
            self.gog_price_cents,
            self.cheapshark_offers,
        )
        return (
            self.price_status in ("paid", "free")
            and lowest is not None
            and self.price_cents == lowest
        )

    @rx.var
    def gog_is_cheapest(self) -> bool:
        lowest = _lowest_comparable_price(
            self.price_status,
            self.price_cents,
            self.gog_status,
            self.gog_price_cents,
            self.cheapshark_offers,
        )
        return (
            self.gog_status in ("paid", "free")
            and lowest is not None
            and self.gog_price_cents == lowest
        )

    @rx.var
    def has_cheapshark_offers(self) -> bool:
        return bool(self.cheapshark_offers)

    @rx.event
    def select_game(self, app_id: int):
        game = find_game_by_app_id(self.games, app_id)
        if game is None:
            self.search_error = "Selecione um jogo da lista de resultados."
            return

        self.selected_app_id = game.app_id
        self.selected_name = game.name
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
        requested_name = (
            self.selected_name
            if self.selected_app_id == app_id
            else ""
        ) or next(
            (game.name for game in CATALOG_GAMES if game.app_id == app_id),
            "",
        )
        self._clear_comparison()
        self.selected_app_id = app_id
        self.selected_name = requested_name
        self.is_loading_price = True

        steam_result: SteamPrice | None = None
        try:
            steam_result = await get_steam_game_price(app_id)
        except SteamServiceError as error:
            if request_id == self._price_request_id:
                self.price_error = str(error)
                self.steam_retryable = True
        finally:
            if request_id == self._price_request_id:
                self.is_loading_price = False

        if request_id != self._price_request_id or self.selected_app_id != app_id:
            return

        if steam_result is not None:
            self._apply_steam_price(steam_result)

        title = self.selected_name
        self.is_loading_gog = bool(title)
        self.is_loading_cheapshark = True
        try:
            tasks = [search_cheapshark_offers(app_id)]
            if title:
                tasks.insert(0, search_gog_offer(title))
            results = await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )
            if request_id != self._price_request_id or self.selected_app_id != app_id:
                return

            if title:
                self._apply_gog_result(results[0])
                cheapshark_result = results[1]
            else:
                cheapshark_result = results[0]
            self._apply_cheapshark_result(cheapshark_result)
        finally:
            if request_id == self._price_request_id:
                self.is_loading_gog = False
                self.is_loading_cheapshark = False

    def _apply_gog_result(self, result: GogMatchResult | BaseException) -> None:
        if isinstance(result, GogServiceError):
            self.gog_error = str(result)
            self.gog_retryable = True
        elif isinstance(result, BaseException):
            raise result
        elif result.status == "not_found":
            self.gog_error = "Jogo não encontrado na GOG."
        elif result.status == "ambiguous":
            self.gog_error = "Mais de uma possível correspondência na GOG."
        elif result.offer is not None and result.offer.status == "unavailable":
            self.gog_error = "Sem preço em BRL na GOG."
        elif result.offer is not None:
            self._apply_gog_offer(result.offer)
        else:
            self.gog_error = "A comparação com a GOG está indisponível."

    def _apply_cheapshark_result(
        self,
        result: list[CheapSharkOffer] | BaseException,
    ) -> None:
        if isinstance(result, CheapSharkServiceError):
            self.cheapshark_error = (
                f"{result} Steam e GOG continuam disponíveis."
            )
            self.cheapshark_retryable = True
        elif isinstance(result, BaseException):
            raise result
        elif result:
            self._apply_cheapshark_offers(result)
        else:
            self.cheapshark_error = CHEAPSHARK_NO_OFFERS_MESSAGE
            self.cheapshark_retryable = True

    def _apply_cheapshark_offers(self, offers: list[CheapSharkOffer]) -> None:
        lowest = _lowest_comparable_price(
            self.price_status,
            self.price_cents,
            self.gog_status,
            self.gog_price_cents,
            offers,
        )
        self.cheapshark_offers = [
            replace(
                offer,
                is_cheapest=(
                    lowest is not None
                    and offer.price_brl_minor == lowest
                ),
            )
            for offer in offers
        ]
        self.cheapshark_error = ""
        self.cheapshark_retryable = False
        if any(offer.is_approximate for offer in offers):
            self.cheapshark_currency_notice = CHEAPSHARK_CONVERSION_NOTICE
        elif any(offer.price_brl_minor is None for offer in offers):
            self.cheapshark_currency_notice = CHEAPSHARK_USD_FALLBACK_NOTICE
        else:
            self.cheapshark_currency_notice = ""

    def _apply_steam_price(self, price: SteamPrice):
        self.price_status = price.status
        self.price_cents = price.final_price_minor or 0
        self.selected_cover_url = price.header_image
        self.steam_logo_url = price.store_logo_url or STEAM_LOGO_URL
        self.steam_updated_label = format_price_timestamp(
            price.source_updated_at,
            price.fetched_at,
            price.store_name,
        )
        self.price_error = ""
        self.steam_retryable = False
        if price.name:
            self.selected_name = price.name

    def _apply_gog_offer(self, offer: GogOffer):
        self.gog_title = offer.title
        self.gog_store_url = offer.store_url
        self.gog_cover_url = offer.cover_url
        self.gog_status = offer.status
        self.gog_price_cents = offer.final_price_minor or 0
        self.gog_logo_url = offer.store_logo_url or GOG_LOGO_URL
        self.gog_updated_label = format_price_timestamp(
            offer.source_updated_at,
            offer.fetched_at,
            offer.store_name,
        )
        self.gog_error = ""
        self.gog_retryable = False
        self._apply_cheapshark_offers(self.cheapshark_offers)

    @rx.event
    async def retry_steam(self):
        app_id = self.selected_app_id
        if app_id <= 0 or self.is_loading_price:
            return

        request_id = self._price_request_id
        self.price_error = ""
        self.steam_retryable = False
        self.is_loading_price = True
        try:
            price = await get_steam_game_price(app_id)
        except SteamServiceError as error:
            if request_id == self._price_request_id and self.selected_app_id == app_id:
                self.price_error = str(error)
                self.steam_retryable = True
        else:
            if request_id == self._price_request_id and self.selected_app_id == app_id:
                self._apply_steam_price(price)
                self._apply_cheapshark_offers(self.cheapshark_offers)
        finally:
            if request_id == self._price_request_id and self.selected_app_id == app_id:
                self.is_loading_price = False

    @rx.event
    async def retry_gog(self):
        title = self.selected_name
        if not title or self.is_loading_gog:
            return

        request_id = self._price_request_id
        app_id = self.selected_app_id
        self.gog_error = ""
        self.gog_retryable = False
        self.is_loading_gog = True
        try:
            result = await search_gog_offer(title)
        except GogServiceError as error:
            if request_id == self._price_request_id and self.selected_app_id == app_id:
                self.gog_error = str(error)
                self.gog_retryable = True
        else:
            if request_id == self._price_request_id and self.selected_app_id == app_id:
                self._apply_gog_result(result)
                self._apply_cheapshark_offers(self.cheapshark_offers)
        finally:
            if request_id == self._price_request_id and self.selected_app_id == app_id:
                self.is_loading_gog = False

    @rx.event
    async def retry_cheapshark(self):
        app_id = self.selected_app_id
        if app_id <= 0 or self.is_loading_cheapshark:
            return

        request_id = self._price_request_id
        self.cheapshark_error = ""
        self.cheapshark_retryable = False
        self.is_loading_cheapshark = True
        try:
            offers = await search_cheapshark_offers(app_id)
        except CheapSharkServiceError as error:
            if request_id == self._price_request_id and self.selected_app_id == app_id:
                self.cheapshark_error = (
                    f"{error} Steam e GOG continuam disponíveis."
                )
                self.cheapshark_retryable = True
        else:
            if request_id == self._price_request_id and self.selected_app_id == app_id:
                self._apply_cheapshark_result(offers)
        finally:
            if request_id == self._price_request_id and self.selected_app_id == app_id:
                self.is_loading_cheapshark = False


class AuthState(rx.State):
    name: str = ""
    email: str = ""
    password: str = ""
    password_visible: bool = False
    auth_error: str = ""
    is_splash_visible: bool = False
    is_submitting: bool = False
    _auth_token: str | None = None
    _catalog_authorized: bool = False

    @rx.var
    def catalog_authorized(self) -> bool:
        return self._catalog_authorized

    @rx.var
    def is_authenticated(self) -> bool:
        return isinstance(self._auth_token, str) and bool(self._auth_token)

    @rx.event
    def set_name(self, value: str):
        self.name = value
        self.auth_error = ""

    @rx.event
    def set_email(self, value: str):
        self.email = value
        self.auth_error = ""

    @rx.event
    def set_password(self, value: str):
        self.password = value
        self.auth_error = ""

    @rx.event
    def toggle_password_visibility(self):
        self.password_visible = not self.password_visible

    @rx.event
    def open_register(self):
        self.auth_error = ""
        self.password = ""
        self.password_visible = False
        self.name = ""
        return rx.redirect("/cadastro")

    @rx.event
    def open_login(self):
        self.auth_error = ""
        self.password = ""
        self.password_visible = False
        self.name = ""
        return rx.redirect("/entrar")

    @rx.event
    def prepare_form(self):
        query_parameters = self.router.url.query_parameters
        self.auth_error = (
            SESSION_EXPIRED_MESSAGE
            if query_parameters.get("session") == "expired"
            else ""
        )
        self.password = ""
        self.password_visible = False
        self.name = ""
        self.is_submitting = False

    def _api_error_message(self, error: xano.XanoApiError) -> str:
        message = error.message
        if self.password:
            message = message.replace(self.password, "[redigida]")
        details = f"HTTP {error.status_code}, {error.code}"
        if error.payload_param:
            details = f"{details}, campo {error.payload_param}"
        return f"{message} ({details})"

    @rx.event
    def logout(self):
        self._auth_token = None
        self._catalog_authorized = False
        self.is_splash_visible = False
        self.is_submitting = False
        self.name = ""
        self.email = ""
        self.password = ""
        self.password_visible = False
        self.auth_error = ""
        return rx.redirect("/entrar")

    def _start_authenticated_transition(self, session: xano.AuthSession):
        self._auth_token = session.auth_token
        self._catalog_authorized = False
        self.name = ""
        self.password = ""
        self.password_visible = False
        self.auth_error = ""
        self.is_submitting = False
        self.is_splash_visible = True
        return rx.call_script(
            "setTimeout(() => window.location.assign('/catalogo'), 900);"
        )

    @rx.event
    async def login(self):
        self.auth_error = ""
        self.password_visible = False

        if not self.email.strip():
            self.auth_error = "Informe seu e-mail."
            return
        if not self.password:
            self.auth_error = "Informe a senha."
            return
        if len(self.password) > xano.MAX_PASSWORD_LENGTH:
            self.auth_error = (
                "A senha deve ter no máximo "
                f"{xano.MAX_PASSWORD_LENGTH} caracteres."
            )
            return

        self.is_submitting = True
        self._auth_token = None
        self._catalog_authorized = False
        try:
            session = await xano.login(self.email, self.password)
        except xano.InvalidCredentialsError:
            self.password = ""
            self.password_visible = False
            self.is_submitting = False
            self.auth_error = "E-mail ou senha inválidos."
            return
        except xano.AuthInputError:
            self.password = ""
            self.password_visible = False
            self.is_submitting = False
            self.auth_error = "E-mail ou senha inválidos."
            return
        except xano.XanoApiError:
            self.auth_error = "E-mail ou senha inválidos."
            self.password = ""
            self.password_visible = False
            self.is_submitting = False
            return
        except xano.XanoUnavailableError:
            self.password = ""
            self.password_visible = False
            self.is_submitting = False
            self.auth_error = xano.AUTH_SERVICE_UNAVAILABLE_MESSAGE
            return
        return self._start_authenticated_transition(session)

    @rx.event
    async def register(self):
        self.auth_error = ""
        self.is_submitting = True
        self.password_visible = False
        self._auth_token = None
        self._catalog_authorized = False
        try:
            session = await xano.signup(self.name, self.email, self.password)
        except (xano.AuthInputError, xano.DuplicateEmailError) as error:
            self.password = ""
            self.password_visible = False
            self.is_submitting = False
            self.auth_error = str(error)
            return
        except xano.XanoApiError as error:
            self.auth_error = self._api_error_message(error)
            self.password = ""
            self.password_visible = False
            self.is_submitting = False
            return
        except xano.XanoUnavailableError:
            self.password = ""
            self.password_visible = False
            self.is_submitting = False
            self.auth_error = xano.AUTH_SERVICE_UNAVAILABLE_MESSAGE
            return
        return self._start_authenticated_transition(session)

    @rx.event
    async def guard_catalog(self):
        auth_token = self._auth_token
        self._catalog_authorized = False
        self.auth_error = ""
        if not isinstance(auth_token, str) or not auth_token:
            self._auth_token = None
            return rx.redirect("/entrar")

        try:
            user = await xano.me(auth_token)
        except xano.InvalidTokenError:
            self._auth_token = None
            return rx.redirect("/entrar?session=expired")
        except xano.XanoApiError as error:
            self.auth_error = self._api_error_message(error)
            return
        except xano.XanoUnavailableError:
            self.auth_error = xano.AUTH_SERVICE_UNAVAILABLE_MESSAGE
            return

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


def brand_content(horizontal: bool = False) -> rx.Component:
    children = [
        rx.icon("gamepad-2", size=22 if horizontal else 38, color="var(--ck-purple)"),
        rx.text(
            "ComparaKeys",
            size="4" if horizontal else "2",
            weight="bold",
            color="var(--ck-purple-light)",
            letter_spacing="0.08em" if horizontal else "0.18em",
        ),
    ]
    if horizontal:
        return rx.hstack(*children, align="center", spacing="2")
    return rx.vstack(*children, align="center", spacing="2")


def brand_link(href: str, horizontal: bool = False) -> rx.Component:
    return rx.link(
        brand_content(horizontal),
        href=href,
        color="inherit",
        text_decoration="none",
        aria_label="ComparaKeys — início",
    )


def session_brand_link(horizontal: bool = False) -> rx.Component:
    return rx.cond(
        AuthState.is_authenticated,
        brand_link("/catalogo", horizontal=horizontal),
        brand_link("/", horizontal=horizontal),
    )


# Estilo global: fade-in suave ao carregar a página
GLOBAL_CSS = THEME_CSS + """
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
    background: var(--ck-surface);
    border-color: var(--ck-purple-border);
    animation: fadeIn 0.5s ease-out, glow 2.4s ease-in-out infinite;
}
.auth-page {
    background: radial-gradient(circle at 50% 25%, #261442 0%, #0b0910 54%, var(--ck-black) 100%);
}
@media (max-height: 720px) {
    .auth-card {
        padding: 1rem !important;
    }
}
.site-navbar {
    gap: 0.75rem;
}
.catalog-search input {
    flex: 1 1 0;
    min-width: 0;
}
.catalog-search button {
    flex: 0 0 auto;
}
:where(a, button, input):focus-visible {
    outline: 3px solid #c4b5fd;
    outline-offset: 2px;
}
.price-comparison-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr));
    gap: 1rem;
    width: 100%;
}
.landing-page {
    width: 100%;
    min-height: 100vh;
    overflow-x: clip;
    background: var(--ck-black);
    color: var(--ck-text);
}
.landing-hero {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    width: 100%;
    min-height: calc(100vh - 64px);
    min-height: calc(100svh - 64px);
    background: var(--ck-black);
}
.landing-topbar {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-sizing: border-box;
    width: 100%;
    height: 64px;
    min-height: 64px;
    min-width: 0;
    padding: 0 clamp(0.75rem, 4vw, 2rem);
    border-bottom: 1px solid var(--ck-purple-border);
    background-color: var(--ck-black);
}
@supports (backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px)) {
    .landing-topbar {
        background-color: rgba(5, 4, 7, 0.9);
        -webkit-backdrop-filter: blur(12px);
        backdrop-filter: blur(12px);
    }
}
.landing-topbar-brand {
    display: flex;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    width: 2.75rem;
    height: 2.75rem;
    border-radius: 0.5rem;
    text-decoration: none;
}
.landing-topbar-actions {
    display: flex;
    flex: 0 0 auto;
    align-items: center;
    justify-content: flex-end;
    gap: 0.5rem;
    min-width: 0;
}
.landing-nav-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 2.5rem;
    padding: 0.55rem 0.75rem;
    border: 1px solid var(--ck-purple);
    border-radius: 0.65rem;
    background: transparent;
    color: var(--ck-purple-light);
    font: inherit;
    font-size: 0.875rem;
    font-weight: 600;
    line-height: 1;
    text-decoration: none;
    white-space: nowrap;
    cursor: pointer;
}
.landing-nav-button:hover {
    filter: brightness(1.12);
}
.landing-nav-primary {
    border-color: var(--ck-purple);
    background: var(--ck-purple);
    color: var(--ck-black);
}
.landing-hero-copy {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 0;
    padding: clamp(1.5rem, 5vw, 4rem);
    text-align: center;
    background: radial-gradient(circle at 50% 45%, #171022 0%, var(--ck-black) 72%);
}
.landing-hero-copy h1 {
    margin: 0;
    color: var(--ck-text);
    font-size: clamp(2.4rem, 5vw, 5rem);
    line-height: 1;
    letter-spacing: -0.045em;
}
.landing-hero-art {
    position: relative;
    min-width: 0;
    overflow: hidden;
    isolation: isolate;
    clip-path: polygon(18% 0, 100% 0, 100% 100%, 0 100%);
    background:
        radial-gradient(ellipse at 68% 32%, rgba(168, 85, 247, 0.8), transparent 34%),
        radial-gradient(ellipse at 32% 78%, rgba(91, 33, 182, 0.7), transparent 38%),
        linear-gradient(138deg, #09070e 4%, #24103d 47%, #08060c 100%);
}
.landing-hero-art::before,
.landing-hero-art::after {
    position: absolute;
    inset: -15%;
    content: "";
    pointer-events: none;
}
.landing-hero-art::before {
    z-index: -1;
    background:
        linear-gradient(116deg, transparent 20%, rgba(216, 180, 254, 0.7) 20.3%, transparent 21.1%),
        linear-gradient(116deg, transparent 45%, rgba(168, 85, 247, 0.45) 45.3%, transparent 46%),
        linear-gradient(116deg, transparent 72%, rgba(196, 181, 253, 0.55) 72.3%, transparent 73%);
    filter: blur(1px);
    transform: skewY(-8deg);
}
.landing-hero-art::after {
    z-index: -2;
    background:
        radial-gradient(ellipse at 58% 47%, rgba(192, 132, 252, 0.3), transparent 20%),
        linear-gradient(180deg, transparent 43%, rgba(5, 4, 7, 0.8) 100%);
}
.landing-divider {
    width: 100%;
    height: 2px;
    background: #000000;
}
.landing-info-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: clamp(1rem, 2.5vw, 1.5rem);
    width: min(100% - 2rem, 1100px);
    margin: 0 auto;
    padding: clamp(1.5rem, 4vw, 3rem) 0;
}
.landing-info-card {
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-width: 0;
    aspect-ratio: 1 / 1;
    padding: clamp(1.25rem, 4vw, 3rem);
    border: 1px solid rgba(167, 139, 250, 0.48);
    border-radius: 1.25rem;
    background: var(--ck-black);
}
.landing-info-card h2 {
    color: var(--ck-purple-light);
    font-size: clamp(1.3rem, 2.8vw, 2rem);
    line-height: 1.2;
}
.landing-info-card p {
    color: var(--ck-text-muted);
    font-size: clamp(1rem, 1.5vw, 1.15rem);
    line-height: 1.65;
}
@media (max-width: 600px) {
    .site-navbar {
        padding-inline: 0.75rem !important;
    }
    .catalog-search {
        align-items: stretch;
        flex-direction: column;
    }
    .catalog-search > * {
        width: 100% !important;
    }
}
@media (max-width: 700px) {
    .landing-hero {
        grid-template-columns: minmax(0, 1fr);
        grid-template-rows: 1fr 1fr;
    }
    .landing-hero-art {
        clip-path: polygon(0 10%, 100% 0, 100% 100%, 0 100%);
    }
    .landing-info-grid {
        grid-template-columns: minmax(0, 1fr);
        width: min(100% - 2rem, 520px);
    }
}
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
    }
}
"""


def navbar() -> rx.Component:
    return rx.hstack(
        session_brand_link(horizontal=True),
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
                on_click=rx.redirect("/entrar"),
                variant="outline",
                size="2",
                style={
                    "cursor": "pointer",
                    "_hover": {"background_color": "var(--violet-3)"},
                },
            ),
        ),
        width="100%",
        padding="1rem clamp(0.75rem, 4vw, 2rem)",
        align="center",
        border_bottom="1px solid var(--gray-5)",
        class_name="site-navbar",
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


def store_brand(
    name: rx.Var[str] | str,
    logo_url: rx.Var[str] | str,
) -> rx.Component:
    return rx.hstack(
        rx.cond(
            logo_url != "",
            rx.box(
                role="img",
                aria_label=f"Logotipo da loja {name}",
                width="2.5rem",
                height="2.5rem",
                flex="0 0 2.5rem",
                border_radius="0.5rem",
                background_color="var(--ck-surface)",
                background_image=f'url("{logo_url}")',
                background_position="center",
                background_repeat="no-repeat",
                background_size="contain",
            ),
            rx.fragment(),
        ),
        rx.text(name, weight="bold", color="white"),
        align="center",
        spacing="2",
    )


def price_comparison() -> rx.Component:
    return rx.vstack(
        rx.cond(
            SearchState.is_loading_price
            | SearchState.is_loading_gog
            | SearchState.is_loading_cheapshark,
            rx.hstack(
                rx.spinner(),
                rx.text(
                    "Consultando preços atuais na Steam, na GOG e em outras lojas..."
                ),
                align="center",
                role="status",
            ),
            rx.fragment(),
        ),
        rx.box(
            rx.card(
                rx.vstack(
                    store_brand("Steam", SearchState.steam_logo_url),
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
                        rx.vstack(
                            rx.heading(
                                SearchState.formatted_price,
                                size="7",
                                color=rx.cond(
                                    SearchState.steam_is_cheapest,
                                    "#4ade80",
                                    "white",
                                ),
                            ),
                            rx.cond(
                                SearchState.steam_is_cheapest,
                                rx.text("Menor preço", color="#4ade80", size="2"),
                                rx.fragment(),
                            ),
                            spacing="1",
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
                            rx.cond(
                                SearchState.steam_is_cheapest,
                                rx.text("Menor preço", color="#4ade80", size="2"),
                                rx.fragment(),
                            ),
                            align="center",
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
                    rx.cond(
                        SearchState.steam_updated_label != "",
                        rx.text(
                            SearchState.steam_updated_label,
                            color="#b8afc8",
                            size="1",
                            role="status",
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
                        store_brand("GOG", SearchState.gog_logo_url),
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
                            rx.vstack(
                                rx.heading(
                                    SearchState.formatted_gog_price,
                                    size="7",
                                    color=rx.cond(
                                        SearchState.gog_is_cheapest,
                                        "#4ade80",
                                        "white",
                                    ),
                                ),
                                rx.cond(
                                    SearchState.gog_is_cheapest,
                                    rx.text("Menor preço", color="#4ade80", size="2"),
                                    rx.fragment(),
                                ),
                                spacing="1",
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
                                rx.cond(
                                    SearchState.gog_is_cheapest,
                                    rx.text("Menor preço", color="#4ade80", size="2"),
                                    rx.fragment(),
                                ),
                                align="center",
                            ),
                            rx.fragment(),
                        ),
                        rx.cond(
                            SearchState.gog_updated_label != "",
                            rx.text(
                                SearchState.gog_updated_label,
                                color="#b8afc8",
                                size="1",
                                role="status",
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
            SearchState.has_cheapshark_offers,
            rx.vstack(
                rx.heading("Outras lojas", size="5", color="#e9ddff"),
                rx.cond(
                    SearchState.cheapshark_currency_notice != "",
                    rx.text(
                        SearchState.cheapshark_currency_notice,
                        color="#b8afc8",
                        size="2",
                        role="status",
                    ),
                    rx.fragment(),
                ),
                rx.foreach(
                    SearchState.cheapshark_offers,
                    cheapshark_offer_card,
                ),
                align="stretch",
                width="100%",
                spacing="2",
            ),
            rx.fragment(),
        ),
        rx.cond(
            SearchState.cheapshark_error != "",
            rx.vstack(
                rx.text(
                    SearchState.cheapshark_error,
                    color="gray",
                    role="status",
                ),
                rx.cond(
                    SearchState.cheapshark_retryable,
                    rx.button(
                        "Tentar novamente na CheapShark",
                        on_click=SearchState.retry_cheapshark,
                        disabled=SearchState.is_loading_cheapshark,
                        variant="outline",
                        size="2",
                    ),
                    rx.fragment(),
                ),
                align="start",
                spacing="2",
            ),
            rx.fragment(),
        ),
        rx.cond(
            SearchState.price_error != "",
            rx.vstack(
                rx.text(SearchState.price_error, color="tomato", role="alert"),
                rx.cond(
                    SearchState.steam_retryable,
                    rx.button(
                        "Tentar novamente na Steam",
                        on_click=SearchState.retry_steam,
                        disabled=SearchState.is_loading_price,
                        variant="outline",
                        size="2",
                    ),
                    rx.fragment(),
                ),
                align="start",
                spacing="2",
            ),
            rx.fragment(),
        ),
        rx.cond(
            SearchState.gog_error != "",
            rx.vstack(
                rx.text(SearchState.gog_error, color="gray", role="status"),
                rx.cond(
                    SearchState.gog_retryable,
                    rx.button(
                        "Tentar novamente na GOG",
                        on_click=SearchState.retry_gog,
                        disabled=SearchState.is_loading_gog,
                        variant="outline",
                        size="2",
                    ),
                    rx.fragment(),
                ),
                align="start",
                spacing="2",
            ),
            rx.fragment(),
        ),
        align="stretch",
        width="100%",
        spacing="3",
    )


def cheapshark_offer_card(offer: CheapSharkOffer) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                store_brand(offer.store_name, offer.store_logo_url),
                rx.link(
                    "Ver oferta",
                    href=offer.deal_url,
                    is_external=True,
                    target="_blank",
                    rel="noopener noreferrer",
                    color="#c4b5fd",
                    size="2",
                ),
                align="start",
                spacing="1",
            ),
            rx.vstack(
                rx.text(
                    offer.price_label,
                    color=rx.cond(offer.is_cheapest, "#4ade80", "white"),
                    weight="bold",
                ),
                rx.cond(
                    offer.is_cheapest,
                    rx.text("Menor preço", color="#4ade80", size="2"),
                    rx.fragment(),
                ),
                rx.cond(
                    offer.rate_label != "",
                    rx.text(
                        offer.rate_label,
                        color="#b8afc8",
                        size="1",
                        text_align="right",
                    ),
                    rx.fragment(),
                ),
                align="end",
                spacing="1",
            ),
            align="center",
            justify="between",
            width="100%",
            spacing="3",
        ),
        rx.cond(
            offer.timestamp_label != "",
            rx.text(
                offer.timestamp_label,
                color="#b8afc8",
                size="1",
                role="status",
                margin_top="0.5rem",
            ),
            rx.fragment(),
        ),
        width="100%",
        background="rgba(17, 13, 26, 0.94)",
        border="1px solid #48336a",
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
                            debounce_timeout=300,
                            size="3",
                            width="100%",
                        ),
                        rx.cond(
                            SearchState.is_searching,
                            rx.hstack(
                                rx.spinner(),
                                rx.text("Buscando jogos na Steam..."),
                                align="center",
                                role="status",
                            ),
                            rx.fragment(),
                        ),
                        rx.cond(
                            SearchState.search_error != "",
                            rx.text(
                                SearchState.search_error,
                                color="tomato",
                                role="alert",
                            ),
                            rx.fragment(),
                        ),
                        rx.cond(
                            SearchState.no_results,
                            rx.text(
                                "Nenhum jogo encontrado. Tente outro nome.",
                                color="gray",
                                role="status",
                            ),
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


def auth_brand() -> rx.Component:
    return session_brand_link()


def splash_screen() -> rx.Component:
    return rx.center(
        rx.vstack(
            auth_brand(),
            rx.spinner(size="3", color="#c4b5fd"),
            rx.text(
                "Preparando seu catálogo...",
                color="#c4b5fd",
                role="status",
            ),
            align="center",
            spacing="5",
        ),
        width="100%",
        min_height="100vh",
        padding="1.5rem",
        background="radial-gradient(circle at center, #24133f 0%, #0b0910 58%, #050407 100%)",
    )


def password_visibility_toggle() -> rx.Component:
    label = rx.cond(
        AuthState.password_visible,
        "Ocultar senha",
        "Mostrar senha",
    )
    return rx.button(
        label,
        on_click=AuthState.toggle_password_visibility,
        aria_label=label,
        variant="ghost",
        size="2",
        color_scheme="violet",
        align_self="flex-end",
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
                    type=rx.cond(
                        AuthState.password_visible,
                        "text",
                        "password",
                    ),
                    max_length=128,
                    width="100%",
                    size="3",
                ),
                password_visibility_toggle(),
                rx.button(
                    "Cadastrar",
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
        border="1px solid var(--ck-purple-border)",
        border_radius="24px",
        background="var(--ck-surface)",
        class_name="auth-card",
    )


def register_card() -> rx.Component:
    return rx.box(
        rx.vstack(
            auth_brand(),
            rx.heading("Crie sua conta", size="6", color="white"),
            rx.text(
                "Informe seu nome, e-mail e uma senha para se cadastrar.",
                color="#b8afc8",
                text_align="center",
            ),
            rx.vstack(
                rx.text("Nome", color="#e9ddff", size="2", weight="medium"),
                rx.input(
                    value=AuthState.name,
                    on_change=AuthState.set_name,
                    placeholder="Seu nome",
                    aria_label="Nome",
                    type="text",
                    required=True,
                    width="100%",
                    size="3",
                ),
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
                    aria_describedby="register-password-rule",
                    type=rx.cond(
                        AuthState.password_visible,
                        "text",
                        "password",
                    ),
                    min_length=8,
                    max_length=128,
                    width="100%",
                    size="3",
                ),
                password_visibility_toggle(),
                rx.text(
                    "Mínimo de 8 caracteres e ao menos uma letra.",
                    id="register-password-rule",
                    color="#b8afc8",
                    size="1",
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
        border="1px solid var(--ck-purple-border)",
        border_radius="24px",
        background="var(--ck-surface)",
        class_name="auth-card",
    )


def landing_page() -> rx.Component:
    return rx.fragment(
        rx.html(f"<style>{GLOBAL_CSS}</style>"),
        rx.vstack(
            rx.box(
                rx.link(
                    rx.icon("gamepad-2", size=38, color="var(--ck-purple)"),
                    href="/",
                    aria_label="ComparaKeys — início",
                    class_name="landing-topbar-brand",
                ),
                rx.cond(
                    AuthState.is_authenticated,
                    rx.hstack(
                        rx.button(
                            "Ir para o catálogo",
                            on_click=rx.redirect("/catalogo"),
                            class_name="landing-nav-button landing-nav-primary",
                        ),
                        rx.button(
                            "Sair",
                            on_click=AuthState.logout,
                            class_name="landing-nav-button",
                        ),
                        spacing="2",
                        class_name="landing-topbar-actions",
                    ),
                    rx.hstack(
                        rx.button(
                            "Entrar",
                            on_click=rx.redirect("/entrar"),
                            class_name="landing-nav-button",
                        ),
                        rx.button(
                            "Cadastrar",
                            on_click=rx.redirect("/cadastro"),
                            class_name="landing-nav-button landing-nav-primary",
                        ),
                        spacing="2",
                        class_name="landing-topbar-actions",
                    ),
                ),
                class_name="landing-topbar",
            ),
            rx.box(
                rx.box(
                    rx.heading("Compara Keys", size="9"),
                    class_name="landing-hero-copy",
                ),
                rx.box(
                    role="presentation",
                    class_name="landing-hero-art",
                ),
                class_name="landing-hero",
            ),
            rx.box(role="separator", class_name="landing-divider"),
            rx.grid(
                rx.box(
                    rx.heading("Quem somos", size="5", as_="h2"),
                    rx.text(
                        "Somos um projeto acadêmico desenvolvido em grupo para "
                        "jogadores que querem comparar preços de jogos.",
                    ),
                    class_name="landing-info-card",
                ),
                rx.box(
                    rx.heading("Objetivo do site e por que usar", size="5", as_="h2"),
                    rx.text(
                        "Compare o preço do mesmo jogo em várias lojas em um só "
                        "lugar. Veja o menor preço e siga pelos links diretos "
                        "para as lojas. A compra acontece fora do site.",
                    ),
                    class_name="landing-info-card",
                ),
                class_name="landing-info-grid",
            ),
            width="100%",
            spacing="0",
            class_name="landing-page",
        ),
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
                class_name="auth-page",
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
                class_name="auth-page",
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
                            class_name="catalog-search",
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
            rx.cond(
                AuthState.auth_error != "",
                rx.center(
                    rx.vstack(
                        rx.text(
                            AuthState.auth_error,
                            role="alert",
                            color="#fca5a5",
                            text_align="center",
                        ),
                        rx.button(
                            "Tentar novamente",
                            on_click=AuthState.guard_catalog,
                            color_scheme="violet",
                        ),
                        rx.button(
                            "Voltar para login",
                            on_click=AuthState.logout,
                            variant="outline",
                        ),
                        align="center",
                        spacing="3",
                    ),
                    width="100%",
                    min_height="100vh",
                    padding="1.5rem",
                    background="#08060c",
                ),
                rx.center(
                    rx.spinner(size="3", color="#c4b5fd"),
                    width="100%",
                    min_height="100vh",
                    background="#08060c",
                ),
            ),
        ),
    )


app = rx.App(theme=rx.theme(accent_color="violet", radius="large", appearance="dark"))
app.add_page(landing_page, route="/")
app.add_page(login_page, route="/entrar", on_load=AuthState.prepare_form)
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