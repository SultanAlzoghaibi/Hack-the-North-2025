import praw

reddit = praw.Reddit(
    client_id="MrRBg1SXCzBh-jlnsX6mMg",
    client_secret="JXKBj-v6tibcJ6rY4EPttWPBPIczog",
    user_agent="htn-reddit-scraper"
)

subreddit = reddit.subreddit("uofc+UCalgary+UofCalgary+Calgary")  # combine subs just in case

# Perform a search
for post in subreddit.search("cpsc 355", sort="new", limit=5):
    print(f"📌 {post.title}")
    print(f"🔗 {post.url}")
    print(f"⬆️ {post.score} | 💬 {post.num_comments} | 🕒 {post.created_utc}")
    print("---")
    time.sleep(1)