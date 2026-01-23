"""Query値オブジェクト。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Query:
    """クエリ（質問）を表す値オブジェクト。"""

    text: str

    def __post_init__(self) -> None:
        """値の検証を行う。"""
        if not self.text:
            raise ValueError("Queryは空文字列にできません。")
        if not isinstance(self.text, str):
            raise ValueError("Queryは文字列である必要があります。")

    def __str__(self) -> str:
        """文字列表現を返す。"""
        return self.text
