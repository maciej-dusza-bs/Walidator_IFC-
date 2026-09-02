"""Nawigacja kroków i składanie interfejsu aplikacji."""

import streamlit as st


def render_app() -> None:
    """Renderuje główny widok aplikacji."""
    st.set_page_config(page_title="Walidator IFC", layout="wide")
    st.title("Walidator IFC")
    st.info(
        "Witaj w Walidatorze IFC. Aby rozpocząć kontrolę modelu, "
        "prześlij plik IFC w kolejnym kroku workflow."
    )
