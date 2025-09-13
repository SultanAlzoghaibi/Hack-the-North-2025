from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
import os
import json
from datetime import datetime
import io

import subprocess

dataTest =[
  {
    "source": "reddit",
    "post_id": "ucalg001",
    "subreddit": "UCalgary",
    "title": "CPSC 355 is killing me",
    "comment_id": "cmt001",
    "author": "throwaway123",
    "body": "Assignments take 20+ hours, any tips?",
    "upvotes": 23,
    "course": "CPSC 355",
    "timestamp": "2025-09-01T12:30:00"
  },
  {
    "source": "reddit",
    "post_id": "ucalg002",
    "subreddit": "UCalgary",
    "title": "Best prof for CPSC 457?",
    "comment_id": "cmt002",
    "author": "gradhelper",
    "body": "Definitely take it with Dr. Smith if you can.",
    "upvotes": 12,
    "course": "CPSC 457",
    "timestamp": "2025-09-02T09:10:00"
  },
  {
    "source": "reddit",
    "post_id": "ucalg003",
    "subreddit": "UCalgary",
    "title": "Worth taking CPSC 319?",
    "comment_id": "cmt003",
    "author": "newbie99",
    "body": "Good intro to software engineering, but group projects can be stressful.",
    "upvotes": 7,
    "course": "CPSC 319",
    "timestamp": "2025-09-03T18:45:00"
  },
  {
    "source": "reddit",
    "post_id": "ucalg004",
    "subreddit": "UCalgary",
    "title": "CPSC 231 Midterm",
    "comment_id": "cmt004",
    "author": "examstress",
    "body": "So much recursion, didn’t expect this much difficulty.",
    "upvotes": 5,
    "course": "CPSC 231",
    "timestamp": "2025-09-04T14:20:00"
  },
  {
    "source": "reddit",
    "post_id": "ucalg005",
    "subreddit": "UCalgary",
    "title": "Thoughts on CPSC 481?",
    "comment_id": "cmt005",
    "author": "uxnerd",
    "body": "Really interesting HCI course, not too hard but a lot of design work.",
    "upvotes": 14,
    "course": "CPSC 481",
    "timestamp": "2025-09-05T11:00:00"
  },
  {
    "source": "reddit",
    "professor": "Dr. Eberly",
    "course": "CPSC 351",
    "department": "Computer Science",
    "rating": 2.9,
    "difficulty": 8,
    "would_take_again": "No",
    "comment": "Harsh grader but you learn formal CS skills.",
    "timestamp": "2025-08-29T10:15:00"
  },
  {
    "source": "reddit",
    "professor": "Dr. Woelfel",
    "course": "CPSC 351",
    "department": "Computer Science",
    "rating": 4.1,
    "difficulty": 5,
    "would_take_again": "Yes",
    "comment": "Challenging but fair, exams were reasonable.",
    "timestamp": "2025-08-28T16:40:00"
  },
  {
    "source": "reddit",
    "professor": "Dr. Lee",
    "course": "CPSC 457",
    "department": "Computer Science",
    "rating": 4.5,
    "difficulty": 6,
    "would_take_again": "Yes",
    "comment": "Explains OS concepts clearly, labs are tough but fair.",
    "timestamp": "2025-08-26T09:00:00"
  },
  {
    "source": "reddit",
    "professor": "Dr. Wong",
    "course": "CPSC 355",
    "department": "Computer Science",
    "rating": 3.7,
    "difficulty": 7,
    "would_take_again": "Maybe",
    "comment": "Lots of assembly coding, rewarding but stressful.",
    "timestamp": "2025-08-25T13:20:00"
  },
  {
    "source": "reddit",
    "professor": "Dr. Patel",
    "course": "CPSC 231",
    "department": "Computer Science",
    "rating": 4.8,
    "difficulty": 4,
    "would_take_again": "Yes",
    "comment": "Very supportive for beginners, great intro course prof.",
    "timestamp": "2025-08-24T15:10:00"
  }


]

load_dotenv()

# uses DATABRICKS_HOST + DATABRICKS_TOKEN env vars
w = WorkspaceClient()




# Save JSON
filename = "reddit_batch_to_databricks.json"

with open(filename, "w") as f:
    json.dump(dataTest, f, indent=2)

# Upload by passing local filename
target_path = f"/Volumes/workspace/default/reddit/{filename}"
#w.dbfs.upload(target_path, filename)

print(f"✅ Uploaded {filename} to Databricks DBFS (/tmp)")

with open(filename, "rb") as file:
  file_bytes = file.read()
  binary_data = io.BytesIO(file_bytes)
  w.files.upload(target_path, binary_data, overwrite = True)



