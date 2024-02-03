import util
from typing import Dict, List
from util import get_api_key
import tweepy


@get_api_key()
def get_tweets_data(api_key: Dict[str, str], twitter_handles: List[str]):
    client = tweepy.Client(bearer_token=api_key['TWITTER_BEARER_TOKEN'])
    results = []
    for username in twitter_handles:
        user = client.get_user(username=username)
        tweets = client.get_users_tweets(user.data.id, max_results=100)
        response = " "
        for tweet in tweets.data:
            response = response + tweet.text + "\n"
        print(username, response)


if __name__ == "__main__":
    print(get_tweets_data(twitter_handles=['_akhaliq']))
