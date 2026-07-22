"""Retweet & Like bot.

On each run it searches recent tweets for your hashtag, filters out anything
you don't want (old tweets, replies, your own tweets, blocked users, blocked
words) and retweets + likes the rest.

The bot is written to stay on the right side of Twitter's automation rules:
 - it acts only on a small, capped number of tweets per run (MAX_ACTIONS_PER_RUN)
 - it pauses between actions (ACTION_DELAY_SECONDS) instead of firing in bursts
 - it honours API rate limits (wait_on_rate_limit) and never retweets replies,
   its own tweets, or content from your blocklist.

Designed to run on a schedule via GitHub Actions — see .github/workflows/bot.yml.
"""

import datetime
import json
import logging
import os
import time
from pathlib import Path

import tweepy

from config import create_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# What to search for. Override with the SEARCH_QUERY environment variable.
SEARCH_QUERY = os.environ.get("SEARCH_QUERY", "#your_hashtag")

# Only act on tweets newer than this many minutes (0 = no age limit).
MAX_AGE_MINUTES = int(os.environ.get("MAX_AGE_MINUTES", "0"))

# How many recent tweets to look at per run (Twitter allows 10–100).
MAX_RESULTS = int(os.environ.get("MAX_RESULTS", "50"))

# Hard cap on how many tweets we'll retweet+like in a single run. Keeping this
# low is the single most important guard against looking like a spam bot.
MAX_ACTIONS_PER_RUN = int(os.environ.get("MAX_ACTIONS_PER_RUN", "10"))

# Seconds to wait between each retweet/like so we don't act in a burst.
ACTION_DELAY_SECONDS = int(os.environ.get("ACTION_DELAY_SECONDS", "10"))


def load_blocklist():
    """Load blocked users and words from blocklist.json (easy to edit)."""
    path = Path(__file__).with_name("blocklist.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning("blocklist.json missing or invalid — no blocks applied")
        return set(), set()

    users = {u.lower() for u in data.get("blocked_users", [])}
    words = {w.lower() for w in data.get("blocked_words", [])}
    return users, words


class Bot:
    def __init__(self, client, blocked_users, blocked_words):
        self.client = client
        self.blocked_users = blocked_users
        self.blocked_words = blocked_words
        self.me_id = client.get_me().data.id

    def contains_blocked_word(self, text):
        lowered = text.lower()
        return any(word in lowered for word in self.blocked_words)

    def is_old(self, tweet):
        if MAX_AGE_MINUTES <= 0:
            return False
        now = datetime.datetime.now(datetime.timezone.utc)
        age_minutes = (now - tweet.created_at).total_seconds() / 60
        return age_minutes > MAX_AGE_MINUTES

    def is_reply(self, tweet):
        return tweet.in_reply_to_user_id is not None

    def i_tweeted(self, tweet):
        return tweet.author_id == self.me_id

    def tweeted_by_blocked_user(self, username):
        return username.lower() in self.blocked_users

    def should_skip(self, tweet, username):
        return (
            self.contains_blocked_word(tweet.text)
            or self.is_old(tweet)
            or self.is_reply(tweet)
            or self.i_tweeted(tweet)
            or self.tweeted_by_blocked_user(username)
        )

    def fetch_tweets(self):
        response = self.client.search_recent_tweets(
            query=f"{SEARCH_QUERY} -is:retweet lang:en",
            max_results=MAX_RESULTS,
            tweet_fields=["created_at", "author_id", "in_reply_to_user_id"],
            expansions=["author_id"],
            user_fields=["username"],
        )
        tweets = response.data or []
        users = {u.id: u.username for u in (response.includes or {}).get("users", [])}
        return tweets, users

    def act_on(self, tweet, username):
        """Retweet and like a single tweet. Returns True if it counted as an action."""
        try:
            self.client.retweet(tweet.id)
            self.client.like(tweet.id)
            logger.info("Retweeted & liked %s by @%s", tweet.id, username)
            return True
        except tweepy.errors.Forbidden as e:
            # Twitter returns 403 when we've already retweeted/liked this tweet.
            logger.info("Skipping %s (already actioned): %s", tweet.id, e)
        except tweepy.errors.TooManyRequests:
            # Rate limited — stop this run cleanly rather than hammering the API.
            logger.warning("Hit rate limit — stopping this run")
            raise
        except Exception:
            logger.error("Error on retweet/like for %s", tweet.id, exc_info=True)
        return False

    def run(self):
        tweets, users = self.fetch_tweets()
        logger.info("Found %d tweets for %r", len(tweets), SEARCH_QUERY)

        acted = 0
        for tweet in tweets:
            if acted >= MAX_ACTIONS_PER_RUN:
                logger.info("Reached MAX_ACTIONS_PER_RUN (%d)", MAX_ACTIONS_PER_RUN)
                break

            username = users.get(tweet.author_id, "")
            if self.should_skip(tweet, username):
                continue

            try:
                if self.act_on(tweet, username):
                    acted += 1
                    time.sleep(ACTION_DELAY_SECONDS)
            except tweepy.errors.TooManyRequests:
                break

        logger.info("Done — actioned %d tweet(s)", acted)


def main():
    blocked_users, blocked_words = load_blocklist()
    client = create_client()
    Bot(client, blocked_users, blocked_words).run()


if __name__ == "__main__":
    main()
