"""Notebookエンティティ。"""

from dataclasses import dataclass, field

from notebooklm_enterprise_experiments_py.domain.value_objects.notebook_id import (
    NotebookId,
)


@dataclass
class Notebook:
    """Notebook（ノートブック）を表すエンティティ。"""

    notebook_id: NotebookId
    display_name: str
    sources: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """値の検証を行う。"""
        if not isinstance(self.display_name, str):
            raise ValueError("display_nameは文字列である必要があります。")
        if not self.display_name:
            raise ValueError("display_nameは空文字列にできません。")
        if not isinstance(self.sources, list):
            raise ValueError("sourcesはリストである必要があります。")
        for source in self.sources:
            if not isinstance(source, str):
                raise ValueError("sourcesの要素は文字列である必要があります。")

    def add_source(self, source_uri: str) -> None:
        """ソースURIを追加する。

        Args:
            source_uri: 追加するソースURI
        """
        if not isinstance(source_uri, str):
            raise ValueError("source_uriは文字列である必要があります。")
        if source_uri not in self.sources:
            self.sources.append(source_uri)
