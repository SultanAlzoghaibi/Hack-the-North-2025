import praw

reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_SECRET",
    user_agent="htn-reddit-scraper"
)

for post in reddit.subreddit("hackathon").hot(limit=5):
    print(post.title)