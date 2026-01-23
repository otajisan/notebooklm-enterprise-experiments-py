"""NotebookService: ノートブック関連のユースケースを実装する。"""

from notebooklm_enterprise_experiments_py.application.dto.notebook_dto import (
    AddSourcesRequest,
    AskRequest,
    AskResponse,
    CitationDto,
    CreateNotebookRequest,
    CreateNotebookResponse,
)
from notebooklm_enterprise_experiments_py.domain.repositories import (
    NotebookRepository,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.notebook_id import (
    NotebookId,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.query import Query


class NotebookService:
    """ノートブック関連のユースケースを実装するサービス。"""

    def __init__(self, repository: NotebookRepository) -> None:
        """NotebookServiceを初期化する。

        Args:
            repository: NotebookRepository
        """
        self.repository = repository

    def create_notebook(
        self,
        request: CreateNotebookRequest,
    ) -> CreateNotebookResponse:
        """ノートブックを作成する。

        Args:
            request: ノートブック作成リクエスト

        Returns:
            ノートブック作成レスポンス
        """
        notebook_id = NotebookId(request.notebook_id)
        notebook = self.repository.create(
            notebook_id=notebook_id,
            display_name=request.display_name,
        )

        return CreateNotebookResponse(
            notebook_id=str(notebook.notebook_id),
            display_name=notebook.display_name,
        )

    def add_sources(
        self,
        request: AddSourcesRequest,
    ) -> None:
        """ノートブックにソースを追加する。

        Args:
            request: ソース追加リクエスト
        """
        notebook_id = NotebookId(request.notebook_id)
        self.repository.add_sources(
            notebook_id=notebook_id,
            source_uris=request.source_uris,
        )

    def ask(
        self,
        request: AskRequest,
    ) -> AskResponse:
        """ノートブックに質問する。

        Args:
            request: 質問リクエスト

        Returns:
            質問レスポンス
        """
        notebook_id = NotebookId(request.notebook_id)
        query = Query(request.query)

        answer = self.repository.ask(
            notebook_id=notebook_id,
            query=query,
        )

        return AskResponse(
            answer_text=answer.answer_text,
            citations=[
                CitationDto(
                    source_title=citation.source_title,
                    content=citation.content,
                )
                for citation in answer.citations
            ],
        )
