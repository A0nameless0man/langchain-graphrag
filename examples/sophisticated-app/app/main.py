import logging

import hydra
from dotenv import load_dotenv
from langchain.embeddings.cache import CacheBackedEmbeddings
from langchain_community.storage import SQLStore
from langchain_core.vectorstores import VectorStore
from omegaconf import OmegaConf


def run_indexer(
    cfg,  # noqa: ANN001
    entities_vector_store: VectorStore,
    relationships_vector_store: VectorStore,
    text_units_vector_store: VectorStore,
):
    indexer = hydra.utils.instantiate(
        cfg.indexer,
        entities_table_generator={"entities_vector_store": entities_vector_store},
        relationships_table_generator={
            "relationships_vector_store": relationships_vector_store
        },
        text_units_table_generator={"vector_store": text_units_vector_store},
    )
    indexer.run()


@hydra.main(version_base="1.3", config_path="./configs", config_name="app.yaml")
def main(cfg):  # noqa: ANN001
    # some how seeing httpx INFO LEVEL for requests
    # disabling it here for now.
    # TODO: should be able to do it via hydra config
    for logger_name in ["httpx", "gensim"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)

    load_dotenv()

    print(OmegaConf.to_yaml(cfg))

    underlying_embedding_model = hydra.utils.instantiate(cfg.extra.embedding_model)

    # HACK: to create the table for embedding store
    embedding_db_path = cfg.paths.sqllite_embedding_cache_dir + "/embedding.db"
    store = SQLStore(
        namespace=underlying_embedding_model.model,
        db_url=embedding_db_path,
    )
    store.create_schema()

    cached_embedding_model = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings=underlying_embedding_model,
        document_embedding_cache=store,
    )

    entities_vector_store = hydra.utils.instantiate(
        cfg.extra.entities_vector_store,
        embedding_function=cached_embedding_model,
    )

    relationships_vector_store = hydra.utils.instantiate(
        cfg.extra.relationships_vector_store,
        embedding_function=cached_embedding_model,
    )

    text_units_vector_store = hydra.utils.instantiate(
        cfg.extra.text_units_vector_store,
        embedding_function=cached_embedding_model,
    )

    if cfg.task_name == "indexing":
        run_indexer(
            cfg,
            entities_vector_store,
            relationships_vector_store,
            text_units_vector_store,
        )
    else:
        print("in Querying mode")
        raise NotImplementedError("Querying mode is not implemented yet")


if __name__ == "__main__":
    main()
