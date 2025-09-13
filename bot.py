import praw

import time

reddit = praw.Reddit(
    client_id="MrRBg1SXCzBh-jlnsX6mMg",
    client_secret="JXKBj-v6tibcJ6rY4EPttWPBPIczog",
    user_agent="htn-reddit-scraper"
)

subreddit = reddit.subreddit("uofc+UCalgary+UofCalgary+Calgary")  # combine subs just in case

# Perform a search
for post in subreddit.search("cpsc 355", sort="new", limit=2):
    post.comments.replace_more(limit=0)  # fetch all comments (removes "load more")

    print(f"📌 Title: {post.title}")
    print(f"🔗 {post.url}")
    print(f"💬 Comments ({len(post.comments)} total):\n")

    for comment in post.comments:
        print(f"👤 {comment.author}:")
        print(f"{comment.body}\n")
        print(f"⬆️ Score: {comment.score}\n")

        print("—" * 50)

        

    time.sleep(1)  # wait 1 second between posts