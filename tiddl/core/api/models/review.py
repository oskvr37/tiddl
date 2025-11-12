import re
import html

from datetime import datetime
from pydantic import BaseModel


class AlbumReview(BaseModel):
    source: str
    lastUpdated: datetime
    text: str
    summary: str

    def normalized_text(self) -> str:
        if not self.text:
            return ""

        # Remove [wimpLink...]...[/wimpLink] including inner content
        cleaned = re.sub(
            r"\[wimpLink[^\]]*\].*?\[/wimpLink\]", "", self.text, flags=re.DOTALL
        )

        # Remove any stray [wimpLink...] or [/wimpLink] tags left behind
        cleaned = re.sub(r"\[/?wimpLink[^\]]*\]", "", cleaned)

        # Decode HTML entities
        cleaned = html.unescape(cleaned)

        # Normalize spaces and newlines
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\s+\n", "\n", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()
