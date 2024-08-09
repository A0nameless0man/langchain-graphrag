"""Select the entities to be used in the local search."""

import logging

import pandas as pd
from langchain_core.vectorstores import VectorStore

logger = logging.getLogger(__name__)


class EntitiesSelector:
    def __init__(self, vector_store: VectorStore, top_k: int):
        self._vector_store = vector_store
        self._top_k = top_k

    def run(self, query: str, df_entities: pd.DataFrame) -> pd.DataFrame:
        """Select the entities to be used in the local search."""
        df_entities = df_entities[
            ["id", "title", "text_unit_ids", "description", "degree"]
        ]

        documents_with_scores = (
            self._vector_store.similarity_search_with_relevance_scores(
                query,
                self._top_k,
            )
        )

        # Relying on metadata to get the entity_ids
        # These returned entities are ranked by similarity
        entity_ids_with_scores = pd.DataFrame.from_records(
            [
                dict(id=doc.metadata["entity_id"], score=score)
                for doc, score in documents_with_scores
            ]
        )

        # Filter the entities dataframe to only include the selected entities
        selected_entities = df_entities[
            df_entities["id"].isin(entity_ids_with_scores["id"])
        ]

        selected_entities = (
            selected_entities.merge(entity_ids_with_scores, on="id")
            .sort_values(by="score", ascending=False)
            .reset_index(drop=True)
        )

        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.debug(
                f"\n\t ==Selected entities==\n {selected_entities[[ 'title', 'degree', 'score']]}"
            )

        return selected_entities