from tweepy import StreamListener
from tweepy import Stream
import logging
from config import create_api
import datetime
import time


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
blocked_people = ["user1", "user...n"] #enter users you want to block from retweeting their tweets here
blocked_words = ["word1", "word...n"] #enter words you want to block here


class FavRetweetListener(StreamListener):
    def __init__(self, api=None):
        self.api = api
        self.me = api.me()

    def contains_hate_words(self, tweet):
        for word in blocked_words:
            if word in tweet:
                return True
            else:
                return False
            
    #Check if the tweet is old //you can adjust the time
    def is_old(self, tweet):
        if (datetime.datetime.now() - tweet.created_at).days > 0.016666667:
            return True
        else:
            return False
    
    #check if a tweet is a reply you can remove this method if you want to retweet replies
    def is_reply(self, tweet):
        if tweet.in_reply_to_status_id is not None:
            return True
        else:
            return False
    
    #Avoid retweeting your own tweets
    def i_tweeted(self, tweet):
        if tweet.user.id == self.me.id:
            return True
        else:
            return False
    
    #check if the tweet is from a blocked user
    def tweeted_by_blocked_user(self, tweet):
        if tweet.user.screen_name in blocked_people:
            return True
        else:
            return False

    #this method handles all the tweeting    
    def on_status(self, tweet):
        logger.info(f"Processing tweet id {tweet.id}")

        if self.contains_hate_words(tweet.text) or self.is_old(tweet) or self.is_reply(tweet) or \
            self.i_tweeted(tweet) or self.tweeted_by_blocked_user(tweet):
            return

        else:
            try:
                tweet.retweet()
                tweet.favorite()
                time.sleep(5)
            except Exception as e:
                logger.error("Error on fav and retweet", exc_info=True)

    def on_error(self, status):
        logger.error(status)

#our main function
def main(keywords):
    api = create_api()
    tweets_listener = FavRetweetListener(api)
    stream = Stream(api.auth, tweets_listener)
    stream.filter(track=keywords, languages=["en"])

if __name__ == "__main__":
    main(["#your_harsh_tag"])
