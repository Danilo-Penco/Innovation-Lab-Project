COLORS = {
    "black": "#050407",
    "black_soft": "#08060c",
    "surface": "#110d1a",
    "purple": "#a78bfa",
    "purple_light": "#c4b5fd",
    "purple_border": "#48336a",
    "text": "#ffffff",
    "text_muted": "#b8afc8",
}

THEME_CSS = f"""
:root {{
    --ck-black: {COLORS["black"]};
    --ck-black-soft: {COLORS["black_soft"]};
    --ck-surface: {COLORS["surface"]};
    --ck-purple: {COLORS["purple"]};
    --ck-purple-light: {COLORS["purple_light"]};
    --ck-purple-border: {COLORS["purple_border"]};
    --ck-text: {COLORS["text"]};
    --ck-text-muted: {COLORS["text_muted"]};
}}
"""
