import reflex as rx


def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("ComparaKeys", size="9"),
            rx.text("Compare preços de keys de jogos em um só lugar", color="gray"),
            rx.box(height="2em"),
            rx.vstack(
                rx.input(placeholder="E-mail", width="100%"),
                rx.input(placeholder="Senha", type="password", width="100%"),
                rx.button("Entrar", width="100%", size="3"),
                spacing="3",
                width="300px",
            ),
            spacing="4",
            align="center",
        ),
        height="100vh",
    )


app = rx.App()
app.add_page(index)