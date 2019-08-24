from tweepy import StreamListener
from tweepy import Stream
import logging
from config import create_api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class FavRetweetListener(StreamListener):
    def __init__(self, api=None):
        self.api = api
        self.me = api.me()

    def on_status(self, tweet):
        logger.info(f"Processing tweet id {tweet.id}")
        if tweet.in_reply_to_status_id is not None or \
            tweet.user.id == self.me.id:
            return
        try:
            tweet.retweet()
            #tweet.favorite()
            time.sleep(200)
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
