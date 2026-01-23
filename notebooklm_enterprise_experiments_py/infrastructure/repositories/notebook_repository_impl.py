"""NotebookRepositoryの実装。"""

from notebooklm_enterprise_experiments_py.domain.entities.notebook import Notebook
from notebooklm_enterprise_experiments_py.domain.repositories.notebook_repository import (
    NotebookRepository,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.answer import (
    Answer,
    Citation,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.notebook_id import (
    NotebookId,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.query import Query
from notebooklm_enterprise_experiments_py.infrastructure.external.notebooklm_client import (
    NotebookLMClient,
)


class NotebookRepositoryImpl(NotebookRepository):
    """NotebookRepositoryの実装。"""

    def __init__(
        self,
        client: NotebookLMClient,
    ) -> None:
        """NotebookRepositoryImplを初期化する。

        Args:
            client: NotebookLMClient
        """
        self.client = client

    def create(
        self,
        notebook_id: NotebookId,
        display_name: str,
    ) -> Notebook:
        """ノートブックを作成する。

        Args:
            notebook_id: ノートブックID
            display_name: 表示名

        Returns:
            作成されたノートブック
        """
        response = self.client.create_notebook(
            notebook_id=str(notebook_id),
            display_name=display_name,
        )

        return Notebook(
            notebook_id=notebook_id,
            display_name=display_name,
            sources=[],
        )

    def add_sources(
        self,
        notebook_id: NotebookId,
        source_uris: list[str],
    ) -> None:
        """ノートブックにソースを追加する。

        Args:
            notebook_id: ノートブックID
            source_uris: 追加するソースURIのリスト
        """
        self.client.add_sources(
            notebook_id=str(notebook_id),
            source_uris=source_uris,
        )

    def ask(
        self,
        notebook_id: NotebookId,
        query: Query,
    ) -> Answer:
        """ノートブックに質問する。

        Args:
            notebook_id: ノートブックID
            query: クエリ（質問）

        Returns:
            回答
        """
        response = self.client.ask(
            notebook_id=str(notebook_id),
            query_text=str(query),
            include_citations=True,
        )

        # Google Cloud Discovery EngineのAPIレスポンス構造に合わせて処理
        answer = response.answer
        citations = tuple(
            Citation(
                source_title=citation.source_title,
                content=citation.content,
            )
            for citation in answer.citations
        )

        return Answer(
            answer_text=answer.answer_text,
            citations=citations,
        )
