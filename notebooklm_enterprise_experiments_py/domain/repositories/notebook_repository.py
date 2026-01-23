"""NotebookRepositoryインターフェース。"""

from abc import ABC, abstractmethod

from notebooklm_enterprise_experiments_py.domain.entities.notebook import Notebook
from notebooklm_enterprise_experiments_py.domain.value_objects.answer import Answer
from notebooklm_enterprise_experiments_py.domain.value_objects.notebook_id import (
    NotebookId,
)
from notebooklm_enterprise_experiments_py.domain.value_objects.query import Query


class NotebookRepository(ABC):
    """Notebookリポジトリのインターフェース。"""

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError
