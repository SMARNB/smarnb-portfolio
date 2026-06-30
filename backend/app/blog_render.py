"""Server-side markdown rendering for blog posts.

First-party and XSS-safe: ``escape=True`` means any raw HTML in the author's
markdown is escaped to text rather than passed through, so a post can never inject
live HTML or script (defence-in-depth on top of the strict CSP, which already
forbids inline scripts). The rendered HTML is cached in the DB on save, so this
runs once per edit — never on a public read.
"""
import re

import mistune

_md = mistune.create_markdown(
    escape=True,
    plugins=["strikethrough", "table", "url", "task_lists", "footnotes"],
)

_TAG = re.compile(r"<[^>]+>")
_ENTITY = re.compile(r"&[a-z]+;")
_WORD = re.compile(r"\w+")


def render_markdown(text):
    """Markdown source -> safe HTML string."""
    return _md(text or "")


def reading_minutes(text):
    """A rough read-time estimate at ~200 wpm (minimum 1 minute)."""
    return max(1, round(len(_WORD.findall(text or "")) / 200))


def plain_excerpt(md_text, limit=160):
    """A clean plain-text summary derived from the markdown (tags + entities
    stripped, whitespace collapsed, truncated on a word-ish boundary)."""
    txt = _ENTITY.sub(" ", _TAG.sub(" ", render_markdown(md_text)))
    txt = re.sub(r"\s+", " ", txt).strip()
    if len(txt) <= limit:
        return txt
    cut = txt[: limit - 1]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut + "…"
