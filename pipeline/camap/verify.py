"""Verbatim sentence verification against cached texts."""
import re
import unicodedata

_TRANSLATE = str.maketrans({
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-",
    " ": " ",
})


def normalize(text):
    text = unicodedata.normalize("NFKC", text).translate(_TRANSLATE)
    return re.sub(r"\s+", " ", text).strip()


def sentence_in(sentence, text):
    return bool(sentence) and normalize(sentence) in normalize(text)
