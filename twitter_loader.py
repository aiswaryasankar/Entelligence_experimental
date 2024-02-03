import util
from typing import Dict, List
from util import get_api_key



@get_api_key()
def get_tweets_data(api_key: Dict[str, str], twitter_handles: List[str]):
    print(api_key)


if __name__ == "__main__":
    print(get_tweets_data(twitter_handles=['musk']))
