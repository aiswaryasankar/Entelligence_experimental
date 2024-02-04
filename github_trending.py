import requests
import json
import openai
from openai import OpenAI

openai.api_key = ''

url = "https://api.gitterapp.com/repositories"
params = {
    "language": "python",
    "since": "daily"
}

all_descriptions = {}
llm_repo_urls = []

# Determine which of these repo descriptions are LLM based and categorize them into RAG, agent, model, training, prompting, multimodal
def determine_if_llm_and_category(description):

  client = OpenAI(api_key="")
  question = f"Given the following repository description: {description}, categorize if it is a repository related to RAG, agents, model application, models, training, prompting, multimodal or other.  It should only be model if the repository is promoting a new model not if it is using a model for a particular application. If its for an application say 'model application'. The response should be in json such as {{'category': 'RAG'}}, {{'category': 'agents'}}.  It should have 'category' as the key."
  response = client.chat.completions.create(
    model="gpt-3.5-turbo-1106",
    messages=[
        {"role": "system", "content": "You are responsible for categorizing repository descriptions into the most relevant LLM repository type. You are an expert on LLM infra and development."},
        {"role": "user", "content": question},
    ],
    response_format={ "type": "json_object" }
  )
  print("Description: " + str(description) + " category: " + str(response.choices[0].message.content["category"]))
  return {description: response.choices[0].message.content["category"]}


def pull_trending_github_repos():
  try:
      response = requests.get(url, params=params)

      # Check if the request was successful (status code 200)
      if response.status_code == 200:
          # Print the response content
          formatted_response = json.dumps(response.json(), indent=2)
          print(formatted_response)
          print("Num repos: " + str(len(response.json())))
          for repo in response.json():
            all_descriptions[repo["name"]] = repo["description"]

      else:
          print(f"Error: {response.status_code} - {response.text}")

  except Exception as e:
      print(f"An error occurred: {e}")

  formatted_descriptions = json.dumps(all_descriptions, indent=2)
  print(formatted_descriptions)

  all_categories = []
  # Format the response into category and all the repository
  for repoName, description in all_descriptions.items():
    print(repoName)
    all_categories.append(determine_if_llm_and_category(description))

  return all_categories



