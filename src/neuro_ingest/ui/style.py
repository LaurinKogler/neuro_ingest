from __future__ import annotations

import html

import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ni-ink: #111827;
            --ni-muted: #4b5563;
            --ni-line: #cbd5e1;
            --ni-panel: #ffffff;
            --ni-soft: #f8fafc;
            --ni-accent: #1f2937;
        }
        .block-container {
            padding-top: 0.7rem;
            padding-bottom: 1.5rem;
            max-width: 1480px;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fafc 0, #ffffff 100%);
            border-right: 1px solid var(--ni-line);
        }
        [data-testid="stWidgetLabel"] p {
            color: var(--ni-ink) !important;
            font-weight: 650;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 0.65rem;
        }
        div[data-testid="column"] div[data-testid="stVerticalBlock"] {
            gap: 0.35rem;
        }
        .stTextInput input,
        .stDateInput input,
        .stNumberInput input,
        .stTextArea textarea,
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border: 1px solid #b8c4d2 !important;
            border-radius: 8px !important;
            color: var(--ni-ink) !important;
            min-height: 2.35rem;
        }
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: #64748b !important;
            opacity: 1 !important;
        }
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] svg {
            color: var(--ni-ink) !important;
            fill: var(--ni-ink) !important;
        }
        .stCheckbox label,
        .stCheckbox span,
        .stRadio label,
        .stRadio span {
            color: var(--ni-ink) !important;
        }
        .stButton > button {
            background: #ffffff !important;
            border: 1px solid #9ca3af !important;
            border-radius: 8px !important;
            color: var(--ni-ink) !important;
            font-weight: 700 !important;
        }
        .stButton > button * {
            color: var(--ni-ink) !important;
        }
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {
            background: #ef4444 !important;
            border-color: #ef4444 !important;
            color: #ffffff !important;
        }
        .stButton > button[kind="primary"] *,
        .stButton > button[data-testid="baseButton-primary"] * {
            color: #ffffff !important;
        }
        [data-testid="stExpander"] {
            background: #ffffff !important;
            border: 1px solid var(--ni-line) !important;
            border-radius: 8px !important;
            margin-bottom: 0.6rem !important;
        }
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary * {
            background: #ffffff !important;
            color: var(--ni-ink) !important;
            font-weight: 700 !important;
        }
        [data-testid="stExpanderDetails"] {
            padding-top: 0.65rem !important;
            padding-bottom: 0.75rem !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            background: #ffffff !important;
            border: 1px solid #c3cfdd !important;
            border-radius: 10px !important;
            box-shadow: 0 8px 22px rgba(18, 31, 48, 0.06);
            padding: 12px !important;
        }
        [data-testid="stFileUploaderDropzone"] * {
            color: var(--ni-ink) !important;
        }
        [data-testid="stFileUploaderDropzone"] button {
            background: #111827 !important;
            border-color: #111827 !important;
            color: #ffffff !important;
        }
        [data-testid="stFileUploaderDropzone"] button * {
            color: #ffffff !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            border-bottom: 1px solid var(--ni-line);
            gap: 1rem;
        }
        .stTabs [data-baseweb="tab"] p {
            color: var(--ni-muted) !important;
            font-weight: 760 !important;
        }
        .stTabs [aria-selected="true"] p {
            color: #ef4444 !important;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #ef4444 !important;
        }
        .ni-header {
            background: #ffffff;
            border: 1px solid var(--ni-line);
            border-radius: 10px;
            margin-bottom: 0.75rem;
            padding: 1rem 1.1rem;
        }
        .ni-kicker {
            color: var(--ni-muted);
            font-size: 0.78rem;
            font-weight: 760;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .ni-title {
            color: var(--ni-ink);
            font-size: 1.6rem;
            font-weight: 820;
            letter-spacing: 0;
            line-height: 1.15;
            margin-top: 0.2rem;
        }
        .ni-subtitle {
            color: var(--ni-muted);
            font-size: 0.95rem;
            margin-top: 0.25rem;
        }
        .ni-panel {
            background: var(--ni-panel);
            border: 1px solid var(--ni-line);
            border-radius: 8px;
            padding: 0.85rem 1rem;
            box-shadow: 0 8px 24px rgba(18, 31, 48, 0.05);
        }
        .ni-section-label {
            color: #334155;
            font-size: 0.76rem;
            font-weight: 780;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin: 0.25rem 0 0.45rem;
        }
        .ni-status-row {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.65rem;
            margin: 0.25rem 0 0.85rem;
        }
        .ni-status-item {
            background: #ffffff;
            border: 1px solid var(--ni-line);
            border-radius: 8px;
            padding: 0.65rem 0.75rem;
        }
        .ni-status-item span {
            color: var(--ni-muted);
            display: block;
            font-size: 0.72rem;
            font-weight: 720;
            text-transform: uppercase;
        }
        .ni-status-item strong {
            color: var(--ni-ink);
            display: block;
            font-size: 0.92rem;
            font-weight: 760;
            margin-top: 0.2rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        @media (max-width: 900px) {
            .ni-status-row {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        .ni-sidebar-brand {
            border-bottom: 1px solid var(--ni-line);
            margin-bottom: 0.9rem;
            padding-bottom: 0.9rem;
        }
        .ni-sidebar-title {
            color: var(--ni-ink);
            font-size: 1.05rem;
            font-weight: 830;
            line-height: 1.15;
        }
        .ni-sidebar-subtitle {
            color: var(--ni-muted);
            font-size: 0.78rem;
            margin-top: 0.25rem;
        }
        .ni-command {
            background: #ffffff;
            border: 1px solid var(--ni-line);
            border-radius: 10px;
            box-shadow: none;
            margin: 0.6rem 0 1rem;
            padding: 1rem;
        }
        .ni-command-title {
            color: var(--ni-ink);
            font-size: 1.15rem;
            font-weight: 830;
            margin-bottom: 0.25rem;
        }
        .ni-command-subtitle {
            color: var(--ni-muted);
            font-size: 0.88rem;
            margin-bottom: 0.85rem;
        }
        .ni-command-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.55rem;
        }
        .ni-command-chip {
            background: var(--ni-soft);
            border: 1px solid #dde5ee;
            border-radius: 8px;
            padding: 0.55rem 0.65rem;
        }
        .ni-command-chip span {
            color: var(--ni-muted);
            display: block;
            font-size: 0.68rem;
            font-weight: 760;
            text-transform: uppercase;
        }
        .ni-command-chip strong {
            color: var(--ni-ink);
            display: block;
            font-size: 0.95rem;
            margin-top: 0.16rem;
        }
        .ni-plot-side-title {
            color: var(--ni-ink);
            font-size: 0.95rem;
            font-weight: 780;
            line-height: 1.1;
            margin-top: 0.1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    st.markdown(
        """
        <div class="ni-sidebar-brand">
          <div class="ni-sidebar-title">Neuro Ingest</div>
          <div class="ni-sidebar-subtitle">TDT / IHS normalization workbench</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header(*, title: str, subtitle: str, kicker: str = "Neuro Ingest") -> None:
    st.markdown(
        f"""
        <div class="ni-header">
          <div class="ni-kicker">{kicker}</div>
          <div class="ni-title">{title}</div>
          <div class="ni-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_row(items: list[tuple[str, object]]) -> None:
    item_markup = "".join(
        (
            "<div class=\"ni-status-item\">"
            f"<span>{html.escape(str(label))}</span>"
            f"<strong>{html.escape(str(value))}</strong>"
            "</div>"
        )
        for label, value in items
    )
    st.markdown(
        f"<div class=\"ni-status-row\">{item_markup}</div>",
        unsafe_allow_html=True,
    )


def render_command_panel(
    *,
    title: str,
    subtitle: str,
    items: list[tuple[str, object]],
) -> None:
    item_markup = "".join(
        (
            "<div class=\"ni-command-chip\">"
            f"<span>{html.escape(str(label))}</span>"
            f"<strong>{html.escape(str(value))}</strong>"
            "</div>"
        )
        for label, value in items
    )
    st.markdown(
        (
            "<div class=\"ni-command\">"
            f"<div class=\"ni-command-title\">{html.escape(title)}</div>"
            f"<div class=\"ni-command-subtitle\">{html.escape(subtitle)}</div>"
            f"<div class=\"ni-command-grid\">{item_markup}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
