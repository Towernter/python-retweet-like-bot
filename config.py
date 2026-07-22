"""Twitter API client setup.

Reads credentials from environment variables (loaded from a local .env file
when running locally, or from GitHub Actions secrets when deployed).
"""

import logging
import os

import tweepy
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def create_client():
    """Create and verify a Twitter API v2 client.

    Retweeting and liking are user actions, so we authenticate with OAuth 1.0a
    user context (consumer keys + access tokens) rather than app-only auth.
    """
    client = tweepy.Client(
        consumer_key=os.environ["CONSUMER_KEY"],
        consumer_secret=os.environ["CONSUMER_SECRET"],
        access_token=os.environ["ACCESS_TOKEN"],
        access_token_secret=os.environ["ACCESS_TOKEN_SECRET"],
        wait_on_rate_limit=True,
    )

    # Fail fast if the credentials are wrong.
    try:
        me = client.get_me()
    except Exception:
        logger.error("Error creating client — check your credentials", exc_info=True)
        raise

    logger.info("Client created for @%s", me.data.username)
    return client
