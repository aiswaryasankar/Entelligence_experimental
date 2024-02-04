from fastapi.responses import StreamingResponse, Response
from openai import OpenAI
from pydantic import BaseModel
import typing
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import DeepLake
from deeplake.core.vectorstore import VectorStore
from github import Auth
from langchain.chains import LLMChain
from langchain.prompts.prompt import PromptTemplate
from langsmith import Client
from datetime import datetime
from git import Repo
from urllib.parse import urlparse
from fastapi.responses import FileResponse
from fastapi import HTTPException
from typing import List, Optional, Any
from github_trending import *


# Agent functions
class DomainAgentRequest(BaseModel):
    githubURL: str
    question: str

class SuggestTrendingReposRequest(BaseModel):
    question: str

class AddTrendingRepoRequest(BaseModel):
    question: str
    repoName: Optional[str] = ""

class AnswerQuestionAcrossReposRequest(BaseModel):
    question: str
    repoName: Optional[str] = ""

class ProConCodeAnalysisRequest(BaseModel):
    question: str
    repoNames: Optional[List[str]] = typing.Any

class SuggestRelevantPapersRequest(BaseModel):
    question: str

class AddTrendingPaperRequest(BaseModel):
    question: str
    repoName: Optional[str] = ""


def domain_agent(domainAgentRequest: DomainAgentRequest):
    """
        Routing logic for all tools supported by the domain agent.
    """
    messages = [
        {"role": "system", "content": "You are a principal software engineer answering questions about a particular codebase. Always use a tool."},
        {"role": "user", "content": domainAgentRequest.question}
    ]

    formatted_history = [{'role': role, 'content': content} for item in domainAgentRequest.history for role, content in zip(['user', 'system'], item)]
    formatted_history.extend(messages)
    print("Function calling context: " + str(formatted_history))

    client = OpenAI()
    def run_conversation():

        tools = [
          {
            "type": "function",
            "function": {
                "name": "suggest_trending_repos",
                "description": "Suggest trending repositories relevant to the user's question and category. ",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": ["githubURL", "githubAccessToken"]
                }
            }
          },
            {
                "type": "function",
                "function": {
                    "name": "add_trending_repo",
                    "description": "Add a trending repo that the user has selected to the database.",
                    "parameters": {}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "answer_question_across_repos",
                    "description": "Answer question by pulling data from each of the repositories provided.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": ["githubURL", "githubAccessToken"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "pro_con_code_analysis",
                    "description": "If the question is related to changes made by a specific user, in a specific file or over some date range. ",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": ["githubURL", "githubAccessToken"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "suggest_relevant_papers",
                    "description": "Generate diagram based on GitHub repository information with filepath when the user asks for a filepath overview. Do not use this if the user is just asking a question about a specific file. They must mention filepath overview.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": ["githubURL", "githubAccessToken", "repoName"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_trending_paper",
                    "description": "The word 'summary' MUST be in the question. The word 'summary' or 'summarize' MUST be in the question. Generate summary for an entire GitHub repository. Questions such as 'Summarize this repository'. DO NOT use it to answer specific questions.  Only use it if the user is asking for a summary of the repository.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": ["vectorDBUrl", "repoName"]
                    }
                }
            },
        ]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=formatted_history,
            tools=tools,
            tool_choice="auto",
        )
        response_message = response.choices[0].message
        print("RESPONSE MESSAGE: " + str(response_message))
        tool_calls = response_message.tool_calls
        if tool_calls == None:
            return response.choices[0].message["content"]

        function_request_mapping = {
            "suggest_trending_repos": SuggestTrendingReposRequest(
                question= domainAgentRequest.question,
            ),
            "add_trending_repo": AddTrendingRepoRequest(
                githubUrl= domainAgentRequest.githubURL,
                githubAccessToken= domainAgentRequest.githubAccessToken,
                repoName= domainAgentRequest.repoNames[0],
                question= domainAgentRequest.question
            ),
            "answer_question_across_repos": AnswerQuestionAcrossReposRequest(
                VectorDBUrl= domainAgentRequest.vectorDBUrl,
                RepoName= domainAgentRequest.repoNames[0],
                History= domainAgentRequest.history,
                GithubUrl= domainAgentRequest.githubURL,
                GithubAccessToken= domainAgentRequest.githubAccessToken,
            ),
            "pro_con_code_analysis": ProConCodeAnalysisRequest(
                vectorDBUrl= domainAgentRequest.vectorDBUrl,
                userName= domainAgentRequest.githubUsername,
                githubUserName= domainAgentRequest.githubUsername,
                question= domainAgentRequest.question,
                githubAccessToken= domainAgentRequest.githubAccessToken,
            ),
            "suggest_relevant_papers": SuggestRelevantPapersRequest(
                githubURL= domainAgentRequest.githubURL,
                githubAccessToken= domainAgentRequest.githubAccessToken,
                repoName= domainAgentRequest.repoNames[0],
                question= domainAgentRequest.question,
            ),
            "add_trending_paper": AddTrendingPaperRequest(
                vectorDBUrl= domainAgentRequest.vectorDBUrl,
                repoName= domainAgentRequest.repoNames[0],
                githubUrl=domainAgentRequest.githubURL,
                githubAccessToken=domainAgentRequest.githubAccessToken
            ),
        }

        if tool_calls:
            available_functions = {
                "suggest_trending_repos": suggest_trending_repos,
                "add_trending_repo": add_trending_repo,
                "answer_question_across_repo": answer_question_across_repo,
                "pro_con_code_analysis": pro_con_code_analysis,
                "suggest_relevant_papers": suggest_relevant_papers,
                "add_trending_paper": add_trending_paper,
            }
            messages.append(response_message)

            for tool_call in tool_calls[:1]:
                function_name = tool_call.function.name
                print("FUNCTION NAME: " + str(function_name))
                function_to_call = available_functions[function_name]
                print("FUNCTION TO CALL: " + str(function_to_call))
                function_args = function_request_mapping[function_name]
                print("FUNCTION ARGS: " + str(function_args))

            return function_to_call(function_args)

    return run_conversation()


def suggest_relevant_papers():
    """
      This function needs to call the get_trending_papers and get the response.
    """
    paperList = pull_trending_github_repos()
    return paperList


def suggest_trending_repos():
    """
      Suggest trending repos
    """
    repoList = pull_trending_github_repos()
    return repoList


def add_trending_paper():
    pass


def add_trending_repo():
    pass


def answer_question_across_repo():
    pass


def pro_con_code_analysis():
    pass

