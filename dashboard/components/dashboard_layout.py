"""Mise en page commune du dashboard CheckIt.AI.

Ce module centralise les principaux composants visuels utilisés dans
les différentes pages Streamlit du dashboard.

Il permet de :

- appliquer un style cohérent à toutes les pages ;
- personnaliser la couleur d'accent de chaque onglet ;
- afficher les en-têtes de page ;
- afficher des blocs d'information ou d'alerte ;
- afficher des cartes de contenu ;
- afficher des badges et des pieds de page.

Le module ne contient aucune logique métier ni aucun accès aux données.
"""

from __future__ import annotations

from html import escape
from typing import Literal

import streamlit as st


# Types

AccentName = Literal[
    "blue",
    "green",
    "orange",
    "purple",
    "red",
    "teal"
]

NoticeType = Literal[
    "danger",
    "info",
    "success",
    "warning"
]


# Configuration

DEFAULT_ACCENT = "blue"

ACCENT_COLORS = {
    "blue": {
        "primary": "69, 126, 255",
        "text": "#6f9dff"
    },
    "green": {
        "primary": "49, 199, 106",
        "text": "#54d889"
    },
    "orange": {
        "primary": "255, 155, 72",
        "text": "#ffac66"
    },
    "purple": {
        "primary": "157, 112, 255",
        "text": "#ae8cff"
    },
    "red": {
        "primary": "255, 93, 93",
        "text": "#ff7c7c"
    },
    "teal": {
        "primary": "15, 157, 132",
        "text": "#2db9a0"
    }
}

NOTICE_ICONS = {
    "danger": "⚠️",
    "info": "ℹ️",
    "success": "✅",
    "warning": "🟠"
}


# Validation

def get_accent_configuration(
    accent: str
) -> dict[str, str]:
    """Retourne la configuration d'une couleur d'accent."""

    normalized_accent = str(accent).strip().lower()

    return ACCENT_COLORS.get(
        normalized_accent,
        ACCENT_COLORS[DEFAULT_ACCENT]
    )


def normalize_notice_type(
    notice_type: str
) -> NoticeType:
    """Normalise le type d'un bloc d'information."""

    normalized_type = str(notice_type).strip().lower()

    if normalized_type in NOTICE_ICONS:
        return normalized_type  # type: ignore[return-value]

    return "info"


# Style global

def apply_dashboard_layout(
    *,
    accent: AccentName = DEFAULT_ACCENT
) -> None:
    """Applique la mise en page commune du dashboard."""

    accent_configuration = get_accent_configuration(accent)
    accent_primary = accent_configuration["primary"]
    accent_text = accent_configuration["text"]

    st.markdown(
        f"""
        <style>
            :root {{
                --checkit-accent-rgb: {accent_primary};
                --checkit-accent-text: {accent_text};
                --checkit-border: rgba(128, 132, 149, 0.18);
                --checkit-border-light: rgba(128, 132, 149, 0.12);
                --checkit-background: rgba(128, 132, 149, 0.04);
                --checkit-background-light: rgba(128, 132, 149, 0.025);
                --checkit-muted: #9296a8;
                --checkit-muted-light: #9a9eae;
                --checkit-radius-small: 0.7rem;
                --checkit-radius-medium: 0.9rem;
                --checkit-radius-large: 1.1rem;
            }}

            .block-container {{
                max-width: 96rem;
                padding-top: 1.6rem;
                padding-bottom: 2rem;
            }}

            .checkit-page-header {{
                position: relative;
                padding: 1.35rem 1.5rem;
                margin-bottom: 1.25rem;
                overflow: hidden;
                border: 1px solid var(--checkit-border);
                border-radius: var(--checkit-radius-large);
                background:
                    radial-gradient(
                        circle at top right,
                        rgba(var(--checkit-accent-rgb), 0.18),
                        transparent 38%
                    ),
                    linear-gradient(
                        135deg,
                        rgba(var(--checkit-accent-rgb), 0.045),
                        var(--checkit-background-light)
                    );
            }}

            .checkit-page-header::after {{
                position: absolute;
                top: 0;
                right: 0;
                width: 7rem;
                height: 0.2rem;
                border-radius: 0 0 0 0.3rem;
                background: rgba(var(--checkit-accent-rgb), 0.8);
                content: "";
            }}

            .checkit-page-eyebrow {{
                margin-bottom: 0.45rem;
                color: var(--checkit-muted);
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.11em;
                text-transform: uppercase;
            }}

            .checkit-page-title {{
                margin: 0;
                font-size: 2rem;
                font-weight: 780;
                line-height: 1.15;
            }}

            .checkit-page-description {{
                max-width: 58rem;
                margin-top: 0.55rem;
                color: #9397a8;
                font-size: 0.92rem;
                line-height: 1.5;
            }}

            .checkit-page-meta {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-top: 0.9rem;
            }}

            .checkit-section-header {{
                display: flex;
                align-items: center;
                gap: 0.65rem;
                margin: 1.1rem 0 0.85rem;
            }}

            .checkit-section-icon {{
                display: flex;
                align-items: center;
                justify-content: center;
                width: 2rem;
                height: 2rem;
                flex: 0 0 2rem;
                border-radius: 0.65rem;
                font-size: 0.92rem;
                background: rgba(var(--checkit-accent-rgb), 0.14);
            }}

            .checkit-section-content {{
                min-width: 0;
            }}

            .checkit-section-title {{
                margin: 0;
                font-size: 1.05rem;
                font-weight: 720;
                line-height: 1.2;
            }}

            .checkit-section-description {{
                margin-top: 0.15rem;
                color: #8d91a4;
                font-size: 0.76rem;
                line-height: 1.35;
            }}

            .checkit-card {{
                height: 100%;
                padding: 1rem;
                border: 1px solid var(--checkit-border);
                border-radius: var(--checkit-radius-medium);
                background: var(--checkit-background);
            }}

            .checkit-card-title {{
                display: flex;
                align-items: center;
                gap: 0.45rem;
                margin-bottom: 0.45rem;
                font-size: 0.98rem;
                font-weight: 720;
            }}

            .checkit-card-text {{
                color: var(--checkit-muted-light);
                font-size: 0.8rem;
                line-height: 1.5;
            }}

            .checkit-card-text p {{
                margin: 0;
            }}

            .checkit-info-card {{
                padding: 0.9rem 1rem;
                border: 1px solid var(--checkit-border);
                border-radius: 0.8rem;
                background: var(--checkit-background);
            }}

            .checkit-info-row {{
                padding: 0.55rem 0;
                border-bottom: 1px solid var(--checkit-border-light);
            }}

            .checkit-info-row:first-child {{
                padding-top: 0;
            }}

            .checkit-info-row:last-child {{
                padding-bottom: 0;
                border-bottom: none;
            }}

            .checkit-info-label {{
                color: #8d91a4;
                font-size: 0.68rem;
                font-weight: 700;
                letter-spacing: 0.05em;
                text-transform: uppercase;
            }}

            .checkit-info-value {{
                margin-top: 0.18rem;
                font-size: 0.84rem;
                line-height: 1.35;
                word-break: break-word;
            }}

            .checkit-notice {{
                display: flex;
                align-items: flex-start;
                gap: 0.65rem;
                padding: 0.9rem 1rem;
                margin-bottom: 0.85rem;
                border: 1px solid var(--checkit-border);
                border-radius: 0.8rem;
                font-size: 0.82rem;
                line-height: 1.45;
            }}

            .checkit-notice-icon {{
                flex: 0 0 auto;
                font-size: 0.95rem;
            }}

            .checkit-notice-content {{
                min-width: 0;
            }}

            .checkit-notice-title {{
                margin-bottom: 0.15rem;
                font-weight: 700;
            }}

            .checkit-notice-info {{
                border-color: rgba(69, 126, 255, 0.24);
                background: rgba(69, 126, 255, 0.08);
                color: #7fa4ff;
            }}

            .checkit-notice-success {{
                border-color: rgba(49, 199, 106, 0.24);
                background: rgba(49, 199, 106, 0.08);
                color: #54d889;
            }}

            .checkit-notice-warning {{
                border-color: rgba(255, 155, 72, 0.26);
                background: rgba(255, 155, 72, 0.08);
                color: #ffac66;
            }}

            .checkit-notice-danger {{
                border-color: rgba(255, 93, 93, 0.26);
                background: rgba(255, 93, 93, 0.08);
                color: #ff7c7c;
            }}

            .checkit-badge {{
                display: inline-flex;
                align-items: center;
                gap: 0.3rem;
                padding: 0.28rem 0.55rem;
                border: 1px solid rgba(var(--checkit-accent-rgb), 0.2);
                border-radius: 999px;
                background: rgba(var(--checkit-accent-rgb), 0.09);
                color: var(--checkit-accent-text);
                font-size: 0.68rem;
                font-weight: 700;
                line-height: 1;
            }}

            .checkit-result-summary {{
                padding: 0.7rem 0.9rem;
                margin: 0.75rem 0;
                border-left: 3px solid rgba(
                    var(--checkit-accent-rgb),
                    0.75
                );
                border-radius: 0 0.65rem 0.65rem 0;
                background: rgba(var(--checkit-accent-rgb), 0.07);
                color: #989cac;
                font-size: 0.78rem;
            }}

            .checkit-selection-help {{
                padding: 0.8rem 1rem;
                margin-top: 0.75rem;
                border: 1px dashed rgba(128, 132, 149, 0.25);
                border-radius: 0.75rem;
                color: #8d91a4;
                font-size: 0.78rem;
                text-align: center;
            }}

            .checkit-footer {{
                padding-top: 1rem;
                margin-top: 1rem;
                border-top: 1px solid var(--checkit-border-light);
                color: #85899b;
                font-size: 0.72rem;
                line-height: 1.4;
                text-align: center;
            }}

            div[data-testid="stMetric"] {{
                padding: 0.15rem 0;
            }}

            div[data-testid="stMetricLabel"] {{
                color: var(--checkit-muted);
                font-size: 0.78rem;
            }}

            div[data-testid="stMetricValue"] {{
                font-size: 1.35rem;
                font-weight: 750;
            }}

            div[data-testid="stVerticalBlockBorderWrapper"] {{
                border-color: var(--checkit-border);
                border-radius: var(--checkit-radius-medium);
                background: var(--checkit-background-light);
            }}

            div[data-testid="stAlert"] {{
                border-radius: 0.8rem;
            }}

            div[data-testid="stExpander"] {{
                border-color: var(--checkit-border);
                border-radius: 0.8rem;
                overflow: hidden;
            }}

            div[data-testid="stDataFrame"] {{
                border: 1px solid rgba(128, 132, 149, 0.16);
                border-radius: 0.8rem;
                overflow: hidden;
            }}

            div[data-testid="stTable"] {{
                border: 1px solid rgba(128, 132, 149, 0.16);
                border-radius: 0.8rem;
                overflow: hidden;
            }}

            button[data-baseweb="tab"] {{
                height: 3rem;
                padding-right: 1rem;
                padding-left: 1rem;
                font-weight: 650;
            }}

            button[data-baseweb="tab"][aria-selected="true"] {{
                color: var(--checkit-accent-text);
            }}

            div[data-testid="stSelectbox"] label,
            div[data-testid="stTextInput"] label,
            div[data-testid="stTextArea"] label,
            div[data-testid="stNumberInput"] label,
            div[data-testid="stCheckbox"] label,
            div[data-testid="stSlider"] label,
            div[data-testid="stDateInput"] label,
            div[data-testid="stMultiSelect"] label {{
                color: #8d91a4;
                font-size: 0.77rem;
                font-weight: 600;
            }}

            div[data-testid="stButton"] button,
            div[data-testid="stFormSubmitButton"] button,
            div[data-testid="stDownloadButton"] button,
            div[data-testid="stLinkButton"] a {{
                min-height: 2.6rem;
                border-radius: 0.75rem;
                font-weight: 650;
            }}

            div[data-testid="stFormSubmitButton"] button[kind="primary"],
            div[data-testid="stButton"] button[kind="primary"] {{
                border-color: rgba(var(--checkit-accent-rgb), 0.8);
                background: rgba(var(--checkit-accent-rgb), 0.9);
            }}

            div[data-testid="stFormSubmitButton"]
            button[kind="primary"]:hover,
            div[data-testid="stButton"]
            button[kind="primary"]:hover {{
                border-color: rgba(var(--checkit-accent-rgb), 1);
                background: rgba(var(--checkit-accent-rgb), 1);
            }}

            code {{
                border-radius: 0.3rem;
                color: var(--checkit-accent-text);
            }}

            @media (max-width: 768px) {{
                .block-container {{
                    padding-top: 1rem;
                    padding-right: 1rem;
                    padding-left: 1rem;
                }}

                .checkit-page-header {{
                    padding: 1.1rem;
                }}

                .checkit-page-title {{
                    font-size: 1.6rem;
                }}

                .checkit-page-description {{
                    font-size: 0.85rem;
                }}

                button[data-baseweb="tab"] {{
                    padding-right: 0.6rem;
                    padding-left: 0.6rem;
                    font-size: 0.78rem;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True
    )


# En-tête

def render_page_header(
    *,
    eyebrow: str,
    title: str,
    description: str,
    badges: list[str] | None = None
) -> None:
    """Affiche l'en-tête principal d'une page."""

    safe_eyebrow = escape(str(eyebrow))
    safe_title = escape(str(title))
    safe_description = escape(str(description))

    badge_html = ""

    if badges:
        rendered_badges = [
            (
                '<span class="checkit-badge">'
                f"{escape(str(badge))}"
                "</span>"
            )
            for badge in badges
            if str(badge).strip()
        ]

        if rendered_badges:
            badge_html = (
                '<div class="checkit-page-meta">'
                f"{''.join(rendered_badges)}"
                "</div>"
            )

    st.markdown(
        '<div class="checkit-page-header">'
        '<div class="checkit-page-eyebrow">'
        f"{safe_eyebrow}"
        "</div>"
        '<div class="checkit-page-title">'
        f"{safe_title}"
        "</div>"
        '<div class="checkit-page-description">'
        f"{safe_description}"
        "</div>"
        f"{badge_html}"
        "</div>",
        unsafe_allow_html=True
    )


# Sections

def render_layout_section_header(
    icon: str,
    title: str,
    description: str | None = None
) -> None:
    """Affiche l'en-tête visuel d'une section."""

    safe_icon = escape(str(icon))
    safe_title = escape(str(title))
    safe_description = escape(str(description or ""))

    description_html = ""

    if safe_description:
        description_html = (
            '<div class="checkit-section-description">'
            f"{safe_description}"
            "</div>"
        )

    st.markdown(
        '<div class="checkit-section-header">'
        '<div class="checkit-section-icon">'
        f"{safe_icon}"
        "</div>"
        '<div class="checkit-section-content">'
        '<div class="checkit-section-title">'
        f"{safe_title}"
        "</div>"
        f"{description_html}"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )


# Blocs d'information

def render_notice(
    message: str,
    *,
    notice_type: NoticeType = "info",
    title: str | None = None,
    icon: str | None = None
) -> None:
    """Affiche un bloc d'information personnalisé."""

    normalized_type = normalize_notice_type(notice_type)
    displayed_icon = icon or NOTICE_ICONS[normalized_type]

    safe_icon = escape(str(displayed_icon))
    safe_message = escape(str(message))
    safe_title = escape(str(title or ""))

    title_html = ""

    if safe_title:
        title_html = (
            '<div class="checkit-notice-title">'
            f"{safe_title}"
            "</div>"
        )

    st.markdown(
        '<div class="checkit-notice '
        f'checkit-notice-{normalized_type}">'
        '<div class="checkit-notice-icon">'
        f"{safe_icon}"
        "</div>"
        '<div class="checkit-notice-content">'
        f"{title_html}"
        f"{safe_message}"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )


def render_information_rows(
    rows: list[tuple[str, object]]
) -> None:
    """Affiche une liste d'informations sous forme de carte."""

    rendered_rows = []

    for label, value in rows:
        if value is None or value == "":
            continue

        rendered_rows.append(
            '<div class="checkit-info-row">'
            '<div class="checkit-info-label">'
            f"{escape(str(label))}"
            "</div>"
            '<div class="checkit-info-value">'
            f"{escape(str(value))}"
            "</div>"
            "</div>"
        )

    if not rendered_rows:
        st.caption("Aucune information disponible.")
        return

    st.markdown(
        '<div class="checkit-info-card">'
        f"{''.join(rendered_rows)}"
        "</div>",
        unsafe_allow_html=True
    )


# Cartes

def render_content_card(
    *,
    title: str,
    text: str,
    icon: str | None = None,
    allow_html: bool = False
) -> None:
    """Affiche une carte de contenu générique."""

    safe_title = escape(str(title))
    safe_icon = escape(str(icon or ""))

    displayed_text = (
        str(text)
        if allow_html
        else escape(str(text))
    )

    title_content = (
        f"{safe_icon} {safe_title}"
        if safe_icon
        else safe_title
    )

    st.markdown(
        '<div class="checkit-card">'
        '<div class="checkit-card-title">'
        f"{title_content}"
        "</div>"
        '<div class="checkit-card-text">'
        f"{displayed_text}"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )


def render_result_summary(
    message: str
) -> None:
    """Affiche un résumé visuel au-dessus d'un résultat."""

    st.markdown(
        '<div class="checkit-result-summary">'
        f"{escape(str(message))}"
        "</div>",
        unsafe_allow_html=True
    )


def render_layout_selection_help(
    message: str
) -> None:
    """Affiche une aide invitant à sélectionner un élément."""

    st.markdown(
        '<div class="checkit-selection-help">'
        f"{escape(str(message))}"
        "</div>",
        unsafe_allow_html=True
    )


# Badges

def render_badges(
    badges: list[str]
) -> None:
    """Affiche une collection de badges."""

    rendered_badges = [
        (
            '<span class="checkit-badge">'
            f"{escape(str(badge))}"
            "</span>"
        )
        for badge in badges
        if str(badge).strip()
    ]

    if not rendered_badges:
        return

    st.markdown(
        '<div class="checkit-page-meta">'
        f"{''.join(rendered_badges)}"
        "</div>",
        unsafe_allow_html=True
    )


# Pied de page

def render_dashboard_footer(
    message: str = (
        "CheckIt.AI · Dashboard de supervision du pipeline multimodal"
    )
) -> None:
    """Affiche le pied de page commun du dashboard."""

    st.markdown(
        '<div class="checkit-footer">'
        f"{escape(str(message))}"
        "</div>",
        unsafe_allow_html=True
    )