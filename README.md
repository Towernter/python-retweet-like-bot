# Retweet & Like Bot

A small Twitter/X bot that automatically retweets and likes tweets for the hashtags you care about — running for free on a schedule via **GitHub Actions**, no server to babysit.

On every run the bot:

1. Searches recent tweets for your hashtag
2. Filters out anything you don't want — old tweets, replies, your own tweets, blocked users, and blocked words
3. Retweets and likes what's left, gently and within Twitter's limits

```
2026-07-22 12:00:01 INFO Client created for @yourhandle
2026-07-22 12:00:02 INFO Found 43 tweets for '#python'
2026-07-22 12:00:07 INFO Retweeted & liked 1948… by @somedev
2026-07-22 12:00:19 INFO Retweeted & liked 1948… by @anotherdev
2026-07-22 12:01:10 INFO Done — actioned 8 tweet(s)
```

---

## Playing nice with Twitter

Aggressive bots get suspended. This one is deliberately conservative:

- **Capped actions per run** — `MAX_ACTIONS_PER_RUN` (default 10) limits how much it does each time.
- **Spaced out** — it waits `ACTION_DELAY_SECONDS` (default 10s) between actions instead of firing in a burst.
- **Rate-limit aware** — it respects the API's rate limits and stops cleanly if it hits one.
- **No replies, no self-retweets** — it skips replies and your own tweets by default.
- **Runs every 2 hours**, not every minute.

You can tune all of these (see the table below) but the defaults are chosen to keep your account safe. Please also follow the [Twitter Automation Rules](https://help.twitter.com/en/rules-and-policies/twitter-automation).

---

## Project structure

```
python-retweet-like-bot/
├── .github/
│   └── workflows/
│       └── bot.yml         # GitHub Actions — runs the bot on a schedule
├── config.py               # Creates & verifies the Twitter API client
├── mybot.py                # Entry point — searches, filters, retweets & likes
├── blocklist.json          # Users and words to skip (edit this, no code needed)
├── requirements.txt        # Python dependencies
├── .env.example            # Template for your credentials
├── .gitignore
└── .env                    # Your credentials (never committed)
```

---

## Requirements

You need a **Twitter/X developer account** with an app that has **Read and Write** permissions, and API v2 access that allows tweet search (`search_recent_tweets`). Create one at [developer.twitter.com](https://developer.twitter.com). From your app you'll need four values:

- API Key (`CONSUMER_KEY`)
- API Secret (`CONSUMER_SECRET`)
- Access Token (`ACCESS_TOKEN`)
- Access Token Secret (`ACCESS_TOKEN_SECRET`)

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/Towernter/python-retweet-like-bot.git
cd python-retweet-like-bot
python -m venv venv
```

Activate it:

```bash
# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your credentials

Copy the template and fill it in:

```bash
cp .env.example .env
```

```
CONSUMER_KEY=your_api_key
CONSUMER_SECRET=your_api_secret
ACCESS_TOKEN=your_access_token
ACCESS_TOKEN_SECRET=your_access_token_secret
SEARCH_QUERY=#python
```

### 4. Choose who and what to skip

Edit **`blocklist.json`** — no code changes needed:

```json
{
  "blocked_users": ["spammer1", "annoyingaccount"],
  "blocked_words": ["crypto", "giveaway"]
}
```

Any tweet from a blocked user, or whose text contains a blocked word, is skipped.

### 5. Run it locally

```bash
python mybot.py
```

---

## Deploy on GitHub Actions

The included workflow (`.github/workflows/bot.yml`) runs the bot every 2 hours for free.

1. Push this repo to GitHub.
2. Go to **Settings → Secrets and variables → Actions** and add your four credentials as **repository secrets**:
   `CONSUMER_KEY`, `CONSUMER_SECRET`, `ACCESS_TOKEN`, `ACCESS_TOKEN_SECRET`.
3. On the same page, under the **Variables** tab, add a variable named `SEARCH_QUERY` with your hashtag (e.g. `#python`).
4. Open the **Actions** tab — the bot runs automatically on schedule, or hit **Run workflow** to trigger it manually.

To change how often it runs, edit the `cron` line in `bot.yml`.

---

## Configuration reference

| Variable | Where | Default | What it does |
|---|---|---|---|
| `CONSUMER_KEY` / `CONSUMER_SECRET` | secret | — | Your app's API key/secret |
| `ACCESS_TOKEN` / `ACCESS_TOKEN_SECRET` | secret | — | Your access token/secret |
| `SEARCH_QUERY` | variable / `.env` | `#your_hashtag` | What to search for |
| `MAX_RESULTS` | `.env` | `50` | How many recent tweets to scan per run (10–100) |
| `MAX_ACTIONS_PER_RUN` | `.env` | `10` | Max retweets+likes per run |
| `ACTION_DELAY_SECONDS` | `.env` | `10` | Pause between actions |
| `MAX_AGE_MINUTES` | `.env` | `0` | Ignore tweets older than this (0 = no limit) |

---

*Previously deployed on Heroku as a streaming worker. Now modernised to Tweepy v2 and GitHub Actions.*
