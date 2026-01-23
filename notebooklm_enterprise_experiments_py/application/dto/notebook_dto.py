"""Notebook関連のDTO。"""

from dataclasses import dataclass


@dataclass
class CreateNotebookRequest:
    """ノートブック作成リクエストDTO。"""

    notebook_id: str
    display_name: str


@dataclass
class CreateNotebookResponse:
    """ノートブック作成レスポンスDTO。"""

    notebook_id: str
    display_name: str


@dataclass
class AddSourcesRequest:
    """ソース追加リクエストDTO。"""

    notebook_id: str
    source_uris: list[str]


@dataclass
class AskRequest:
    """質問リクエストDTO。"""

    notebook_id: str
    query: str


@dataclass
class CitationDto:
    """引用情報DTO。"""

    source_title: str
    content: str


@dataclass
class AskResponse:
    """質問レスポンスDTO。"""

    answer_text: str
    citations: list[CitationDto]
