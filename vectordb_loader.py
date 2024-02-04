from multiprocessing import Pool
import os
import requests
from openai import OpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import DeepLake
import time
from langchain.document_loaders import OnlinePDFLoader
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter, Language
from urllib.parse import urljoin, urlparse, urldefrag
from llama_index import download_loader
from bs4 import BeautifulSoup
from langchain.text_splitter import HTMLHeaderTextSplitter
from dataclasses import *
from typing import List
from dataclasses_json import dataclass_json

@dataclass
class IngestDocumentationRequest:
  VectorDBUrl: str
  DocumentationUrl: str

@dataclass_json
@dataclass
class IngestDocumentationResponse:
  Texts: List[any]
  Error: Exception


def ingest_code(ingestCodeRequest: IngestCodeRequest) -> IngestCodeResponse:
  """
    Ingeting code and adding it to the vector db
  """
  pass


def ingest_pdf(ingestDocumentationRequest: IngestDocumentationRequest) -> IngestDocumentationResponse:
  """
    This function is directly responsible for ingesting PDFs and PDFs only
  """
  loader = OnlinePDFLoader(ingestDocumentationRequest.DocumentationUrl)
  data = loader.load()
  data = data[0].page_content

  # Chunk the data and add it to the vector db
  text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=20,
    length_function=len,
    is_separator_regex=False,
  )

  texts = text_splitter.create_documents([data], [{"path": ingestDocumentationRequest.DocumentationUrl, "source": ingestDocumentationRequest.DocumentationUrl} for i in range(len(data))])
  print("Document " + str(ingestDocumentationRequest.DocumentationUrl) + " length: " + str(len(texts)))
  return IngestDocumentationResponse(
    Texts=texts,
    Error=None,
  )


def ingest_web_url(ingestDocumentationRequest: IngestDocumentationRequest) -> IngestDocumentationResponse:
  """
    This function is responsible for taking a URL, finding all suburls and creating a list of documents from that data.
  """

  def get_subpages_recursive_same_prefix(url, base_prefix, visited=set()):
    valid_urls = []

    try:
      if url in visited:
        return valid_urls
      response = requests.get(url)
      response.raise_for_status()  # Check if the request was successful
      html_content = response.text
      soup = BeautifulSoup(html_content, 'html.parser')
      links = soup.find_all('a')
      subpages = [link.get('href') for link in links if link.get('href') is not None]
      base_url = urlparse(url).scheme + '://' + urlparse(url).netloc
      subpages = [urljoin(base_url, subpage) for subpage in subpages]
      subpages = [subpage for subpage in subpages if subpage.startswith(base_prefix)]
      valid_urls.append(url)
      visited.add(url)
      for subpage in subpages:
        subpage_no_fragment = urldefrag(subpage).url
        valid_urls.extend(get_subpages_recursive_same_prefix(subpage_no_fragment, base_prefix, visited))

    except Exception as e:
      print("Failed to ingest documentation with error: " + str(e))
      return IngestDocumentationResponse(
        Texts=[],
        Error=str(e),
      )
    return valid_urls

  url = ingestDocumentationRequest.DocumentationUrl
  base_prefix = ingestDocumentationRequest.DocumentationUrl
  all_valid_urls = get_subpages_recursive_same_prefix(url, base_prefix)

  print("Documentation subpages: " + str(all_valid_urls))

  SimpleWebPageReader = download_loader("SimpleWebPageReader")
  loader = SimpleWebPageReader()
  documents = loader.load_data(urls=all_valid_urls)
  headers_to_split_on = [
      ("h1", "Header 1"),
      ("h2", "Header 2"),
      ("h3", "Header 3"),
      ("h4", "Header 4"),
      ("h5", "Header 5"),
      ("h6", "Header 6"),
  ]

  texts = []
  for doc in documents:
    html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    html_header_splits = html_splitter.split_text(doc.text)
    print(html_header_splits)
    texts.extend(html_header_splits)

  return IngestDocumentationResponse(
    Texts=texts,
    Error=None,
  )


def ingest_documentation_ctrl(ingestDocumentationRequest: IngestDocumentationRequest) -> IngestDocumentationResponse:
  """
    This is responsible for taking in PDFs, documentation URLs, and more in order to add the chunked up documentation to the corresponding vector db and use that for the final overall Q&A
  """
  # Determine the type of URL - pdf or weblink
  if "pdf" in ingestDocumentationRequest.DocumentationUrl:
    print("Ingesting PDF: " + str(ingestDocumentationRequest.DocumentationUrl))
    ingestDocumentationResponse = ingest_pdf(ingestDocumentationRequest)
    if ingestDocumentationResponse.Error != None:
      print("Failed to ingest pdf documentation with error: " + str(ingestDocumentationResponse.Error))
  else:
    print("Ingesting webpage: " + str(ingestDocumentationRequest.DocumentationUrl))
    ingestDocumentationResponse = ingest_web_url(ingestDocumentationRequest)
    if ingestDocumentationResponse.Error != None:
      print("Failed to ingest website documentation with error: " + str(ingestDocumentationResponse.Error))

  texts = ingestDocumentationResponse.Texts
  embeddings = OpenAIEmbeddings(disallowed_special=())
  db = DeepLake(dataset_path=ingestDocumentationRequest.VectorDBUrl,
        embedding_function=embeddings,
        token=os.environ['ACTIVELOOP_TOKEN'],
        read_only=False,
        num_workers=12,
        runtime = {"tensor_db": True})

  # Do this in chunks to avoid hitting the ratelimit immediately
  for i in range(0, len(texts), 4000):
    print("Added "+ str(i) + " docs to vectordb")
    db.add_documents(texts[i:i+4000])
    time.sleep(.01)

  # If the dataset is still empty after ingestion, return an error
  print("Vector db len: " + str(db.vectorstore.dataset.num_samples))
  if db.vectorstore.dataset.num_samples <= 0:
    return IngestDocumentationResponse(
      Texts=[],
      Error="Vector database is empty"
    )
  return IngestDocumentationResponse(
    Texts=[],
    Error=None,
  )



