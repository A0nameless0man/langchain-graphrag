import networkx as nx
from langchain_core.language_models import BaseLLM
from langchain_core.output_parsers.base import BaseOutputParser

from langchain_graphrag.types.graphs.community import Community
from langchain_graphrag.types.prompts import PromptBuilder

from .utils import CommunityReportResult


class CommunityReportGenerator:
    def __init__(
        self,
        prompt_builder: PromptBuilder,
        llm: BaseLLM,
        output_parser: BaseOutputParser,
    ):
        prompt = prompt_builder.build()
        self._chain = prompt | llm | output_parser
        self._prompt_builder = prompt_builder

    def invoke(self, community: Community, graph: nx.Graph) -> CommunityReportResult:
        chain_input = self._prompt_builder.prepare_chain_input(
            community=community,
            graph=graph,
        )

        return self._chain.invoke(input=chain_input)