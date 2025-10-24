# patient/app/i18n.py
from __future__ import annotations
import streamlit as st
from functools import lru_cache
from typing import Iterable, Optional

# Try Google Cloud Translate (v2 client is the most practical for apps)
try:
    from google.cloud import translate_v2 as translate
    _HAS_GC = True
except Exception:
    _HAS_GC = False


# ---- Languages you want to offer -------------------------------------------------
LANGUAGES = {
    "en": "English",
    "zh": "Chinese (Simplified)",
    "ms": "Malay",
    "ta": "Tamil",
    "hi": "Hindi",
    "id": "Indonesian",
    "th": "Thai",
    "vi": "Vietnamese",
    "ko": "Korean",
    "ja": "Japanese",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ar": "Arabic",
}


# ---- Internal helpers ------------------------------------------------------------
def _client():
    if not _HAS_GC:
        return None
    return translate.Client()  # credentials picked up from env var if present


@lru_cache(maxsize=1)
def _has_valid_client() -> bool:
    """Ping Google once to verify credentials; cache the result."""
    if not _HAS_GC:
        return False
    try:
        c = _client()
        _ = c.translate("ok", target_language="en")
        return True
    except Exception:
        return False


@lru_cache(maxsize=4096)
def _translate_cached(text: str, target: str, source: Optional[str]) -> str:
    """Cached translate call. On any failure, return the original text."""
    if not text or target == "en":
        return text
    if not _has_valid_client():
        return text
    try:
        c = _client()
        result = c.translate(text, target_language=target, source_language=source)
        if isinstance(result, list) and result:
            result = result[0]
        return (result or {}).get("translatedText", text)
    except Exception:
        return text


# ---- Public API ------------------------------------------------------------------
def current_lang() -> str:
    return st.session_state.get("i18n_lang", "en")


def set_lang(code: str):
    st.session_state["i18n_lang"] = code


def _(text: str, *, source: Optional[str] = None) -> str:
    """Translate a single UI string."""
    return _translate_cached(text, current_lang(), source)


def translate_series(values: Iterable[str], *, source: Optional[str] = None) -> list[str]:
    """Translate an iterable of strings (e.g., DataFrame column)."""
    lang = current_lang()
    return [_translate_cached(str(v), lang, source) for v in values]


def i18n_controls(sidebar: bool = True) -> str:
    """Sidebar language selector (kept for convenience)."""
    mount = st.sidebar if sidebar else st
    with mount:
        mount.caption("Language")
        keys = list(LANGUAGES.keys())
        cur = current_lang()
        idx = keys.index(cur) if cur in keys else 0
        code = mount.selectbox(
            "Interface language",
            options=keys,
            index=idx,
            format_func=lambda k: f"{LANGUAGES[k]} ({k})",
        )
    set_lang(code)
    return code


def show_status_badge():
    """Small caption showing translation status."""
    lang = current_lang()
    if lang == "en":
        return
    if _has_valid_client():
        st.caption(f"🌐 Auto-translating UI to **{LANGUAGES.get(lang, lang)}**")
    else:
        st.caption(
            "🌐 Translation requested but Google Cloud credentials were not detected. "
            "Showing original language for now."
        )


# ---- Top-right language bar ------------------------------------------------------
def _lang_index(code: str) -> int:
    keys = list(LANGUAGES.keys())
    return keys.index(code) if code in keys else 0


def language_bar() -> str:
    """Render a compact language selector aligned to the top-right."""
    bar = st.container()
    with bar:
        a, b, c = st.columns([6, 3, 2])  # right-align in column 'c'
        with c:
            keys = list(LANGUAGES.keys())
            idx = _lang_index(current_lang())
            sel = st.selectbox(
                "🌐 Language",
                options=keys,
                index=idx,
                format_func=lambda k: f"{LANGUAGES[k]} ({k})",
                label_visibility="collapsed",
                key="i18n_lang_select",
            )
            set_lang(sel)
    return current_lang()
