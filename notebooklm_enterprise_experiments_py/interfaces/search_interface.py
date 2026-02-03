"""検索サービスのインターフェース定義。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchCitation:
    """検索結果の引用情報を表すデータクラス。"""

    title: str
    url: str


@dataclass(frozen=True)
class SearchResult:
    """検索結果を表すデータクラス。

    Attributes:
        summary: AIによって生成された回答テキスト
        citations: 参照元のタイトルとURLのリスト
    """

    summary: str
    citations: list[SearchCitation]


@dataclass(frozen=True)
class DocumentResult:
    """検索ドキュメントの詳細情報を表すデータクラス。

    Attributes:
        title: ドキュメントのタイトル
        content: ドキュメントの内容（スニペットまたは抽出テキスト）
        url: ドキュメントのURL
    """

    title: str
    content: str
    url: str


@dataclass(frozen=True)
class DocumentSearchResult:
    """ドキュメント検索結果を表すデータクラス。

    Attributes:
        results: 検索結果のドキュメントリスト
    """

    results: list[DocumentResult] = field(default_factory=list)


class ISearchService(ABC):
    """検索サービスのインターフェース。

    Vertex AI Search (Discovery Engine) を使用した検索と回答生成を行う
    サービスの抽象クラス。
    """

    @abstractmethod
    def search_and_answer(self, query: str) -> SearchResult:
        """検索と同時にAIによる要約（回答）を取得する。

        Args:
            query: 検索クエリ（質問テキスト）

        Returns:
            SearchResult: summary（回答テキスト）とcitations（引用元リスト）を含む結果
        """
        raise NotImplementedError
