"""リポジトリインターフェース: ドメインオブジェクトの永続化に関する抽象化。"""

from notebooklm_enterprise_experiments_py.domain.repositories.notebook_repository import (  # noqa: E501
    NotebookRepository,
)

__all__ = [
    "NotebookRepository",
]
