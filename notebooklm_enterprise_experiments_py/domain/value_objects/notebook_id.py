"""Notebook ID値オブジェクト。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NotebookId:
    """Notebook IDを表す値オブジェクト。"""

    value: str

    def __post_init__(self) -> None:
        """値の検証を行う。"""
        if not self.value:
            raise ValueError("NotebookIdは空文字列にできません。")
        if not isinstance(self.value, str):
            raise ValueError("NotebookIdは文字列である必要があります。")

    def __str__(self) -> str:
        """文字列表現を返す。"""
        return self.value
