from tweepy import StreamListener
from tweepy import Stream
import logging
from config import create_api
import datetime
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
blocked_people = ["lawrhuns", "fan_banter", "_whatthesport", "bitcoinconnect", "premtrackerapp", "zakariaacehgrup", "e_arsenalnet", "footy90com"]
blocked_words = ["@BudweiserNG", "gay", "lgbt", "fuck", "cunt", "pussy","lesben","dick","LGBT", "RT @e_arsenalnet"]


class FavRetweetListener(StreamListener):
    def __init__(self, api=None):
        self.api = api
        self.me = api.me()

    def on_status(self, tweet):
        logger.info(f"Processing tweet id {tweet.id}")
        if tweet.in_reply_to_status_id is not None or \
            tweet.user.id == self.me.id or (datetime.datetime.now() - tweet.created_at).days > 0.01666666666 or \
            tweet.user.screen_name in blocked_people or [word for word in blocked_words if word in tweet.text]:
            return
        try:
            tweet.retweet()
            tweet.favorite()
            time.sleep(5)
        except Exception as e:
            logger.error("Error on fav and retweet", exc_info=True)
        

    def on_error(self, status):
        logger.error(status)


def main(keywords):
    api = create_api()
    tweets_listener = FavRetweetListener(api)
    stream = Stream(api.auth, tweets_listener)
    stream.filter(track=keywords, languages=["en"])


if __name__ == "__main__":
    main(["#Arsenal", "#COYG"])
