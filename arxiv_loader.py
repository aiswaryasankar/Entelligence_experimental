import util
from typing import Dict, List
from util import get_api_key
import arxiv



def get_latest_arxiv_papers():
    results = []    
    arxiv_search = arxiv.Search(
            query='ti:GPT OR ti:LLM OR ti:Agent',
            id_list=[],
            max_results=100,
            sort_by=arxiv.SortCriterion.SubmittedDate)
    for result in arxiv_search.results():
        results.append({
            "author": result.authors,
            "title": result.title,
            "summary": result.summary,
            "URL": result.entry_id,
            "pdfLink": result.entry_id.replace('abs', 'pdf') + '.pdf',
            })
    return results


if __name__ == "__main__":
    print(get_latest_arxiv_papers())

