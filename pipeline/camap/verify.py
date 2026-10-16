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


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\[])|\n+")


def find_sentence(text, names_a, names_b):
    """First sentence of `text` mentioning one name of each actor (case-insensitive, whole words)."""
    def pattern(names):
        alts = sorted({re.escape(n) for n in names if n}, key=len, reverse=True)
        return re.compile(r"(?<![\w-])(?:" + "|".join(alts) + r")(?![\w-])", re.I) if alts else None

    pa, pb = pattern(names_a), pattern(names_b)
    if not pa or not pb:
        return ""
    for s in _SENTENCE_SPLIT.split(text):
        s = s.strip()
        if pa.search(s) and pb.search(s):
            return s
    return ""
