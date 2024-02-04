import os
import sys
import io
import openai
import pandas as pd
import time
from github_trending import pull_trending_github_repos 
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from llama_index.llms.openai import OpenAI
from llama_index.agent import OpenAIAgent
from llama_index.tools.tool_spec.base import BaseToolSpec
from llama_index.tools.query_engine import QueryEngineTool
from arxiv_loader import get_latest_arxiv_papers
from util import get_api_key

GPT_MODEL_NAME = 'gpt-4-0613'


class EntelligenceTools(BaseToolSpec):
    spec_functions = [
        "suggest_relevant_papers",
        "add_trending_paper",
        "get_trending_github_repos",
    ]

    def suggest_relevant_papers(self, kw_list: List[str]) -> List[Dict[str, str]]:
        """Given a list of keywords, searches arxiv to find latest papers which
        are relevant to any keyword in the list.
        """
        return get_latest_arxiv_papers(kw_list)

    def get_trending_github_repos(self) -> List[Dict[str,str]]:
        """Finds trending repositories on Github in the area of AI and machine learning."""
        return pull_trending_github_repos()

    def add_trending_paper(self, paper_url: str) -> bool:
        """Parse the pdf content of a provided paper URL into a hosted chroma DB.
        If succesful, returns True else False
        """
        try:
            add_to_chroma(paper_url)
            return True
        except Exception as e:
            return False


@get_api_key()
def create_agent(api_key: Dict[str, str]):
    openai.api_key = api_key['OPENAI']
    tool_spec = EntelligenceTools()
    llm = OpenAI(temperature=0, model=GPT_MODEL_NAME)
    return OpenAIAgent.from_tools(tool_spec.to_tool_list(), llm=llm, verbose=True)



if __name__ == '__main__':
    agent = create_agent()
    print(agent.chat(sys.argv[1]))

