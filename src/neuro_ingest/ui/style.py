from __future__ import annotations

import html

import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ni-ink: #17202e;
            --ni-ink-soft: #334155;
            --ni-muted: #667085;
            --ni-faint: #8a97a8;
            --ni-line: #cfd8e3;
            --ni-line-strong: #aebccc;
            --ni-page: #f3f6fa;
            --ni-panel: #ffffff;
            --ni-soft: #f8fafc;
            --ni-accent: #ef4444;
            --ni-accent-dark: #c92f2f;
            --ni-teal: #0f766e;
            --ni-indigo: #364fc7;
            --ni-shadow: 0 10px 26px rgba(29, 41, 57, 0.08);
        }

        html,
        body,
        [data-testid="stAppViewContainer"] {
            background: var(--ni-page) !important;
            color: var(--ni-ink) !important;
        }
        .block-container {
            max-width: 1540px;
            padding: 1.05rem 1.65rem 1.75rem;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 0.72rem;
        }
        div[data-testid="column"] div[data-testid="stVerticalBlock"] {
            gap: 0.42rem;
        }

        [data-testid="stSidebar"] {
            background: #fbfcfe !important;
            border-right: 1px solid var(--ni-line);
            box-shadow: 8px 0 26px rgba(29, 41, 57, 0.05);
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0.62rem;
        }

        [data-testid="stWidgetLabel"] p {
            color: var(--ni-ink) !important;
            font-size: 0.78rem !important;
            font-weight: 720 !important;
            letter-spacing: 0;
        }
        .stCaption,
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] * {
            color: var(--ni-muted) !important;
        }

        .stTextInput input,
        .stDateInput input,
        .stNumberInput input,
        .stTextArea textarea,
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border: 1px solid var(--ni-line-strong) !important;
            border-radius: 7px !important;
            color: var(--ni-ink) !important;
            min-height: 2.25rem;
            box-shadow: 0 1px 0 rgba(17, 24, 39, 0.03);
        }
        .stTextInput input:focus,
        .stDateInput input:focus,
        .stNumberInput input:focus,
        .stTextArea textarea:focus,
        div[data-baseweb="select"] > div:focus-within {
            border-color: var(--ni-teal) !important;
            box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12) !important;
        }
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: #94a3b8 !important;
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
        [data-testid="stRadio"] label {
            padding-right: 0.55rem;
        }

        .stButton > button {
            background: #ffffff !important;
            border: 1px solid var(--ni-line-strong) !important;
            border-radius: 7px !important;
            color: var(--ni-ink) !important;
            font-weight: 760 !important;
            min-height: 2.25rem;
            box-shadow: 0 1px 0 rgba(17, 24, 39, 0.04);
        }
        .stButton > button:hover {
            border-color: var(--ni-teal) !important;
            color: var(--ni-teal) !important;
        }
        .stButton > button *,
        .stButton > button:hover * {
            color: inherit !important;
        }
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {
            background: var(--ni-accent) !important;
            border-color: var(--ni-accent) !important;
            color: #ffffff !important;
            box-shadow: 0 8px 18px rgba(239, 68, 68, 0.22);
        }
        .stButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="baseButton-primary"]:hover {
            background: var(--ni-accent-dark) !important;
            border-color: var(--ni-accent-dark) !important;
            color: #ffffff !important;
        }

        [data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.84) !important;
            border: 1px solid var(--ni-line) !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 10px rgba(29, 41, 57, 0.035);
            margin-bottom: 0.65rem !important;
        }
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary * {
            background: transparent !important;
            color: var(--ni-ink) !important;
            font-weight: 780 !important;
        }
        [data-testid="stExpanderDetails"] {
            border-top: 1px solid #edf1f5;
            padding-top: 0.75rem !important;
            padding-bottom: 0.82rem !important;
        }

        [data-testid="stFileUploaderDropzone"] {
            background: #ffffff !important;
            border: 1px dashed #9fb0c3 !important;
            border-radius: 9px !important;
            box-shadow: var(--ni-shadow);
            padding: 13px !important;
        }
        [data-testid="stFileUploaderDropzone"] * {
            color: var(--ni-ink) !important;
        }
        [data-testid="stFileUploaderDropzone"] button {
            background: var(--ni-ink) !important;
            border-color: var(--ni-ink) !important;
            color: #ffffff !important;
        }
        [data-testid="stFileUploaderDropzone"] button * {
            color: #ffffff !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            border-bottom: 1px solid var(--ni-line-strong);
            gap: 0.2rem;
            margin-top: 0.2rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 7px 7px 0 0;
            height: 2.2rem;
            padding: 0 0.58rem;
        }
        .stTabs [data-baseweb="tab"] p {
            color: var(--ni-muted) !important;
            font-size: 0.84rem !important;
            font-weight: 780 !important;
        }
        .stTabs [aria-selected="true"] {
            background: rgba(255, 255, 255, 0.72);
        }
        .stTabs [aria-selected="true"] p {
            color: var(--ni-accent) !important;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: var(--ni-accent) !important;
            height: 2px;
        }

        .stAlert {
            border-radius: 8px !important;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--ni-line);
            border-radius: 8px;
            overflow: hidden;
        }

        .ni-header {
            align-items: center;
            background: #ffffff;
            border: 1px solid var(--ni-line);
            border-left: 4px solid var(--ni-teal);
            border-radius: 9px;
            box-shadow: var(--ni-shadow);
            display: flex;
            gap: 0.85rem;
            justify-content: space-between;
            margin-bottom: 0.75rem;
            padding: 0.85rem 1rem;
        }
        .ni-header-main {
            align-items: center;
            display: flex;
            gap: 0.8rem;
            min-width: 0;
        }
        .ni-mark {
            align-items: center;
            background: #17202e;
            border-radius: 8px;
            color: #ffffff;
            display: flex;
            flex: 0 0 auto;
            font-size: 0.82rem;
            font-weight: 860;
            height: 2.35rem;
            justify-content: center;
            letter-spacing: 0.04em;
            width: 2.35rem;
        }
        .ni-kicker {
            color: var(--ni-teal);
            font-size: 0.68rem;
            font-weight: 830;
            letter-spacing: 0.1em;
            line-height: 1;
            text-transform: uppercase;
        }
        .ni-title {
            color: var(--ni-ink);
            font-size: 1.35rem;
            font-weight: 850;
            letter-spacing: 0;
            line-height: 1.15;
            margin-top: 0.16rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .ni-subtitle {
            color: var(--ni-muted);
            font-size: 0.86rem;
            margin-top: 0.18rem;
        }
        .ni-header-status {
            color: var(--ni-muted);
            font-size: 0.78rem;
            font-weight: 720;
            text-align: right;
            white-space: nowrap;
        }

        .ni-section-label {
            color: var(--ni-ink-soft);
            font-size: 0.7rem;
            font-weight: 840;
            letter-spacing: 0.11em;
            margin: 0.35rem 0 0.35rem;
            text-transform: uppercase;
        }

        .ni-status-row {
            display: grid;
            gap: 0.55rem;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            margin: 0.1rem 0 0.65rem;
        }
        .ni-status-item {
            background: #ffffff;
            border: 1px solid var(--ni-line);
            border-radius: 8px;
            box-shadow: 0 4px 14px rgba(29, 41, 57, 0.045);
            padding: 0.58rem 0.68rem;
            position: relative;
        }
        .ni-status-item:before {
            background: var(--ni-indigo);
            border-radius: 8px 0 0 8px;
            bottom: 0.5rem;
            content: "";
            left: -1px;
            position: absolute;
            top: 0.5rem;
            width: 3px;
        }
        .ni-status-item span {
            color: var(--ni-faint);
            display: block;
            font-size: 0.66rem;
            font-weight: 820;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .ni-status-item strong {
            color: var(--ni-ink);
            display: block;
            font-size: 0.88rem;
            font-weight: 790;
            margin-top: 0.16rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .ni-sidebar-brand {
            border-bottom: 1px solid var(--ni-line);
            margin-bottom: 0.95rem;
            padding-bottom: 0.95rem;
        }
        .ni-sidebar-brand-row {
            align-items: center;
            display: flex;
            gap: 0.65rem;
        }
        .ni-sidebar-mark {
            align-items: center;
            background: var(--ni-ink);
            border-radius: 8px;
            color: #ffffff;
            display: flex;
            flex: 0 0 auto;
            font-size: 0.74rem;
            font-weight: 850;
            height: 2.05rem;
            justify-content: center;
            letter-spacing: 0.05em;
            width: 2.05rem;
        }
        .ni-sidebar-title {
            color: var(--ni-ink);
            font-size: 1.02rem;
            font-weight: 850;
            line-height: 1.1;
        }
        .ni-sidebar-subtitle {
            color: var(--ni-muted);
            font-size: 0.76rem;
            margin-top: 0.16rem;
        }

        .ni-command {
            background: #ffffff;
            border: 1px solid var(--ni-line);
            border-radius: 9px;
            box-shadow: var(--ni-shadow);
            margin: 0.55rem 0 1rem;
            padding: 0.9rem;
        }
        .ni-command-title {
            color: var(--ni-ink);
            font-size: 1.03rem;
            font-weight: 850;
            margin-bottom: 0.18rem;
        }
        .ni-command-subtitle {
            color: var(--ni-muted);
            font-size: 0.83rem;
            margin-bottom: 0.72rem;
        }
        .ni-command-grid {
            display: grid;
            gap: 0.5rem;
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .ni-command-chip {
            background: var(--ni-soft);
            border: 1px solid #e0e7ef;
            border-radius: 7px;
            padding: 0.5rem 0.58rem;
        }
        .ni-command-chip span {
            color: var(--ni-faint);
            display: block;
            font-size: 0.63rem;
            font-weight: 820;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        .ni-command-chip strong {
            color: var(--ni-ink);
            display: block;
            font-size: 0.9rem;
            margin-top: 0.14rem;
        }
        .ni-plot-side-title {
            border-left: 3px solid var(--ni-teal);
            color: var(--ni-ink);
            font-size: 0.9rem;
            font-weight: 820;
            line-height: 1.1;
            margin: 0.08rem 0 0.1rem;
            padding-left: 0.42rem;
        }

        @media (max-width: 900px) {
            .block-container {
                padding-left: 0.9rem;
                padding-right: 0.9rem;
            }
            .ni-header {
                align-items: flex-start;
                flex-direction: column;
            }
            .ni-title {
                white-space: normal;
            }
            .ni-status-row,
            .ni-command-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    st.markdown(
        """
        <div class="ni-sidebar-brand">
          <div class="ni-sidebar-brand-row">
            <div class="ni-sidebar-mark">NI</div>
            <div>
              <div class="ni-sidebar-title">Neuro Ingest</div>
              <div class="ni-sidebar-subtitle">TDT / IHS normalization</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header(*, title: str, subtitle: str, kicker: str = "Neuro Ingest") -> None:
    st.markdown(
        f"""
        <div class="ni-header">
          <div class="ni-header-main">
            <div class="ni-mark">NI</div>
            <div>
              <div class="ni-kicker">{html.escape(kicker)}</div>
              <div class="ni-title">{html.escape(title)}</div>
              <div class="ni-subtitle">{html.escape(subtitle)}</div>
            </div>
          </div>
          <div class="ni-header-status">ABR ingest and review</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_row(items: list[tuple[str, object]]) -> None:
    item_markup = "".join(
        (
            '<div class="ni-status-item">'
            f"<span>{html.escape(str(label))}</span>"
            f"<strong>{html.escape(str(value))}</strong>"
            "</div>"
        )
        for label, value in items
    )
    st.markdown(
        f'<div class="ni-status-row">{item_markup}</div>',
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
            '<div class="ni-command-chip">'
            f"<span>{html.escape(str(label))}</span>"
            f"<strong>{html.escape(str(value))}</strong>"
            "</div>"
        )
        for label, value in items
    )
    st.markdown(
        (
            '<div class="ni-command">'
            f'<div class="ni-command-title">{html.escape(title)}</div>'
            f'<div class="ni-command-subtitle">{html.escape(subtitle)}</div>'
            f'<div class="ni-command-grid">{item_markup}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )
