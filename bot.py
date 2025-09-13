import praw
import time
import json
from demoCourseList import DemoDataSetCourses

reddit = praw.Reddit(
    client_id="MrRBg1SXCzBh-jlnsX6mMg",
    client_secret="JXKBj-v6tibcJ6rY4EPttWPBPIczog",
    user_agent="htn-reddit-scraper"
)

subreddit = reddit.subreddit("uofc+UCalgary+UofCalgary+Calgary")  # combine subs just in case

all_courses_data = []

for courseObj in DemoDataSetCourses:
    course_data = {
        "courseName": courseObj["code"],
        "officialDesc": courseObj["description"],
        "redditData": []
    }
    courseSearch = f"{courseObj['code']}"
    
    
    for post in subreddit.search(courseSearch, sort="best", limit=2):
        post.comments.replace_more(limit=0)  # fetch all comments (removes "load more")

        post_data = {
            "title": post.title,
            "url": post.url,
            "comments": []
        }

        for comment in post.comments:
            comment_data = {
                "author": str(comment.author),
                "body": comment.body,
                "score": comment.score
            }
            post_data["comments"].append(comment_data)

        course_data["redditData"].append(post_data)

        time.sleep(1)  # wait 1 second between posts

    all_courses_data.append(course_data)

    print(f"✅ Saved {course_data['courseName']} to courseRedditData.json")
    
print(json.dumps(all_courses_data, indent=4))

with open("courseRedditData.json", "w") as outfile:
    json.dump(all_courses_data, outfile, indent=4)