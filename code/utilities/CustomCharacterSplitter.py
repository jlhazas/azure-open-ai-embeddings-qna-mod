
from langchain.text_splitter import TextSplitter
from typing import (
    Any,
    Dict,
    Iterable,
    List
)

class CustomCharacterTextSplitter(TextSplitter):
    """Implementation of splitting text that looks at characters."""

    def __init__(self, separator: str = "\n\n", **kwargs: Any) -> None:
        """Create a new TextSplitter."""
        super().__init__(**kwargs)
        self._separator = separator

    def split_text(self, text: str) -> List[str]:
        """Split incoming text and return chunks."""
        # First we naively split the large input into a bunch of smaller ones.
        splits = text.split(self._separator)
        #_separator = "" if self._keep_separator else self._separator
        return splits