"""Answer値オブジェクト。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Citation:
    """引用情報を表す値オブジェクト。"""

    source_title: str
    content: str

    def __post_init__(self) -> None:
        """値の検証を行う。"""
        if not isinstance(self.source_title, str):
            raise ValueError("source_titleは文字列である必要があります。")
        if not isinstance(self.content, str):
            raise ValueError("contentは文字列である必要があります。")


@dataclass(frozen=True)
class Answer:
    """回答を表す値オブジェクト。"""

    answer_text: str
    citations: tuple[Citation, ...] = ()

    def __post_init__(self) -> None:
        """値の検証を行う。"""
        if not isinstance(self.answer_text, str):
            raise ValueError("answer_textは文字列である必要があります。")
        if not isinstance(self.citations, tuple):
            raise ValueError("citationsはタプルである必要があります。")
        for citation in self.citations:
            if not isinstance(citation, Citation):
                raise ValueError("citationsの要素はCitationである必要があります。")

    def __str__(self) -> str:
        """文字列表現を返す。"""
        return self.answer_text
