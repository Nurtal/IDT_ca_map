"""Verbatim sentence verification against cached texts."""
import re
import unicodedata
from functools import lru_cache

_TRANSLATE = str.maketrans({
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-",
    " ": " ",
})


# PubTator transliterates Greek letters in gene and protein names (IKKepsilon, IFNbeta) while
# databases and publishers keep the letter. Without this, "IKKε" never matches its own source.
_GREEK = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon", "ζ": "zeta",
    "η": "eta", "θ": "theta", "ι": "iota", "κ": "kappa", "λ": "lambda", "μ": "mu",
    "ν": "nu", "ξ": "xi", "ο": "omicron", "π": "pi", "ρ": "rho", "σ": "sigma", "ς": "sigma",
    "τ": "tau", "υ": "upsilon", "φ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega",
    "µ": "mu",  # the micro sign, which is a different code point from the letter
}


@lru_cache(maxsize=512)
def normalize(text):
    text = unicodedata.normalize("NFKC", text).translate(_TRANSLATE)
    for letter, name in _GREEK.items():
        text = text.replace(letter, name)
    return re.sub(r"\s+", " ", text).strip()


@lru_cache(maxsize=512)
def despaced(text):
    """`normalize` collapses runs of whitespace; this drops them entirely.

    A database excerpt sometimes loses a word boundary where a line ended in the source
    ("incancer cells" for "in cancer cells" in SIGNOR-264025). Comparing both sides without
    any whitespace forgives exactly that, and nothing else: every character of the quote,
    in order, must still be in the text, so an invented or altered sentence still fails.
    """
    return re.sub(r"\s+", "", normalize(text))


def sentence_in(sentence, text):
    if not sentence:
        return False
    return normalize(sentence) in normalize(text) or despaced(sentence) in despaced(text)


# a sentence boundary with whitespace, a paragraph break, or — as database excerpts come —
# a full stop glued straight onto the next capitalised word
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\[])|\n+|(?<=[.!?])(?=[A-Z][a-z])")


def passages(quote):
    """A database excerpt may join several passages of the paper with "|"."""
    return [p.strip() for p in (quote or "").split("|") if p.strip()]


def quote_in(quote, text):
    """True when every sentence of the quote appears verbatim in `text`.

    Contiguity is not required, and the deciding reason is SIGNOR: its excerpts join passages
    from different parts of a paper, sometimes with "|", sometimes with nothing at all. Demanding
    one contiguous match called a faithful quote non-verbatim. Requiring *every* sentence to be
    present keeps the check strong — an invented sentence still fails — and only forgives the
    database's editing. A trailing full stop is forgiven too: PubTator strips the one after a
    title, and a quote of the title carries it.
    """
    parts = [s for p in passages(quote) for s in _SENTENCE_SPLIT.split(p)]
    # three words is enough to be a claim; below that it is a fragment a split left behind
    # ("4h).", "(Fig."), which no source contains as written
    parts = [s.strip().rstrip(".;:,") for s in parts if len(s.split()) >= 3] or passages(quote)
    return bool(parts) and all(sentence_in(p, text) for p in parts)


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
