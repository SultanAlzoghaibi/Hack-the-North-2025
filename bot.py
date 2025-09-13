import praw
import time
import datetime
from typing import List, Dict, Tuple
import math

reddit = praw.Reddit(
    client_id="MrRBg1SXCzBh-jlnsX6mMg",
    client_secret="JXKBj-v6tibcJ6rY4EPttWPBPIczog",
    user_agent="htn-reddit-scraper"
)

def calculate_recency_score(comment_timestamp: int, decay_factor: float = 0.1) -> float:

    current_time = time.time()
    age_in_days = (current_time - comment_timestamp) / (24 * 60 * 60)
    
    recency_score = math.exp(-decay_factor * age_in_days)
    return min(recency_score, 1.0)  

def calculate_length_score(comment_body: str, 
                         optimal_length: int = 200, 
                         min_length: int = 20) -> float:

    length = len(comment_body.strip())
    
    if length < min_length:
        return 0.1
    
    if length <= optimal_length:
        # Linear increase up to optimal length
        length_score = length / optimal_length
    else:
        # Gradual decrease for overly long comments
        excess = length - optimal_length
        length_score = max(0.5, 1.0 - (excess / (optimal_length * 2)))
    
    return min(length_score, 1.0)

def normalize_vote_score(score: int, max_score: int = 100) -> float:

    if score < 0:
        return 0.05  # Give negative comments very low but non-zero score
    
    # Logarithmic scaling for positive scores to handle wide range
    if score == 0:
        return 0.3  # Neutral baseline
    
    normalized = math.log(score + 1) / math.log(max_score + 1)
    return min(normalized, 1.0)

def calculate_composite_score(comment, 
                            vote_weight: float = 0.25,
                            recency_weight: float = 0.25, 
                            length_weight: float = 0.5) -> Dict:

    total_weight = vote_weight + recency_weight + length_weight
    vote_weight /= total_weight
    recency_weight /= total_weight
    length_weight /= total_weight
    
    # Calculate individual scores
    vote_score = normalize_vote_score(comment.score)
    recency_score = calculate_recency_score(comment.created_utc)
    length_score = calculate_length_score(comment.body)
    
    # Calculate composite score
    composite = (vote_score * vote_weight + 
                recency_score * recency_weight + 
                length_score * length_weight)
    
    return {
        'vote_score': vote_score,
        'recency_score': recency_score,
        'length_score': length_score,
        'composite_score': composite,
        'raw_vote_score': comment.score,
        'comment_age_days': (time.time() - comment.created_utc) / (24 * 60 * 60),
        'comment_length': len(comment.body.strip())
    }

def format_comment_with_scores(comment, scores: Dict) -> str:
    """Format comment display with all scoring information"""
    age_days = scores['comment_age_days']
    age_str = f"{age_days:.1f} days ago" if age_days >= 1 else f"{age_days*24:.1f} hours ago"
    
    output = []
    output.append(f"👤 {comment.author}:")
    output.append(f"{comment.body}\n")
    
    # Score breakdown
    output.append("📊 SCORES:")
    output.append(f"  🎯 Composite: {scores['composite_score']:.3f}")
    output.append(f"  ⬆️ Votes: {scores['vote_score']:.3f} (raw: {scores['raw_vote_score']})")
    output.append(f"  🕒 Recency: {scores['recency_score']:.3f} ({age_str})")
    output.append(f"  📝 Length: {scores['length_score']:.3f} ({scores['comment_length']} chars)")
    
    return "\n".join(output)

def search_alternating(subreddit_obj, search_term: str, total_posts: int = 10):

    print(f"🔍 Fetching {total_posts//2} new posts and {total_posts//2} best posts...")
    
    try:
        # Fetch new posts
        new_posts = list(subreddit_obj.search(search_term, sort="new", limit=total_posts//2 + 2))
        
        # Fetch best posts (using "top" with time filter instead of "best")
        best_posts = list(subreddit_obj.search(search_term, sort="top", time_filter="year", limit=total_posts//2 + 2))
        
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []
    

    seen_ids = set()
    mixed_posts = []
    
    max_length = max(len(new_posts), len(best_posts))
    
    for i in range(max_length):
        # Add new post if available and not duplicate
        if i < len(new_posts) and new_posts[i].id not in seen_ids:
            mixed_posts.append(("NEW", new_posts[i]))
            seen_ids.add(new_posts[i].id)
        
        # Add best post if available and not duplicate  
        if i < len(best_posts) and best_posts[i].id not in seen_ids:
            mixed_posts.append(("TOP", best_posts[i]))
            seen_ids.add(best_posts[i].id)
        
        # Stop if we have enough posts
        if len(mixed_posts) >= total_posts:
            break
    
    print(f"📋 Created mixed list of {len(mixed_posts)} posts")
    return mixed_posts[:total_posts]


def search_new(subreddit_obj, search_term: str, total_posts: int = 10):
    return list(subreddit_obj.search(search_term, sort="new", limit=total_posts))

def search_top(subreddit_obj, search_term: str, total_posts: int = 10):
    return list(subreddit_obj.search(search_term, sort="top", time_filter="year", limit=total_posts))

def analyze_and_rank_comments(post, top_n: int = 5) -> List[Tuple]:
    """Analyze and rank comments by composite score"""
    comment_scores = []
    
    for comment in post.comments:
        if hasattr(comment, 'body') and comment.body != '[deleted]' and comment.body.strip():
            try:
                scores = calculate_composite_score(comment)
                comment_scores.append((comment, scores))
            except Exception as e:
                print(f"⚠️ Error scoring comment: {e}")
                continue
    
    # Sort by composite score (descending)
    comment_scores.sort(key=lambda x: x[1]['composite_score'], reverse=True)
    
    return comment_scores[:top_n]

def process_mixed_posts(search_term: str, total_posts: int = 6):
    """
    Main function to process mixed posts with comment analysis
    """
    # Create subreddit object
    subreddit = reddit.subreddit("uofc+UCalgary+UofCalgary+Calgary")
    
    print(f"🔍 Searching for '{search_term}' posts with enhanced scoring...\n")
    print("=" * 70)
    
    # Get mixed posts
    mixed_posts = search_alternating(subreddit, search_term, total_posts)
    
    if not mixed_posts:
        print("❌ No posts found!")
        return
    
    print(f"\n🎯 PROCESSING {len(mixed_posts)} MIXED POSTS:\n")
    
    for i, (source_type, post) in enumerate(mixed_posts, 1):
        try:
            print(f"📊 POST {i}/{len(mixed_posts)} - [{source_type}]")
            print(f"📌 Title: {post.title}")
            print(f"🔗 {post.url}")
            
            # Get post age
            post_age = (time.time() - post.created_utc) / (24 * 60 * 60)
            print(f"📅 Post age: {post_age:.1f} days | Score: {post.score} | Comments: {post.num_comments}")
            
            # Load comments
            print("🔄 Loading comments...")
            post.comments.replace_more(limit=0)
            print(f"💬 Loaded {len(post.comments)} comments")
            
            if len(post.comments) == 0:
                print("⚠️ No comments found for this post")
                print("=" * 70)
                continue
            
            # Get top comments by composite score
            top_comments = analyze_and_rank_comments(post, top_n=3)
            
            if top_comments:
                print(f"\n🏆 TOP {len(top_comments)} COMMENTS BY COMPOSITE SCORE:")
                print("-" * 50)
                
                for rank, (comment, scores) in enumerate(top_comments, 1):
                    print(f"\n🥇 RANK #{rank}")
                    print(format_comment_with_scores(comment, scores))
                    print("-" * 40)
            else:
                print("⚠️ No valid comments found for analysis")
            
            print("=" * 70)
            
        except Exception as e:
            print(f"❌ Error processing post {i}: {e}")
            continue
        
        # Rate limiting
        time.sleep(2)

def test_search_only(search_term: str = "cpsc 441"):
    """
    Test function to just check if search is working
    """
    subreddit = reddit.subreddit("uofc+UCalgary+UofCalgary+Calgary")
    
    print(f"🧪 Testing search for '{search_term}'...")
    
    try:
        # Test new posts
        new_posts = list(subreddit.search(search_term, sort="new", limit=3))
        print(f"✅ New posts: {len(new_posts)} found")
        for post in new_posts[:2]:
            print(f"  - {post.title[:60]}...")
        
        # Test top posts
        top_posts = list(subreddit.search(search_term, sort="top", time_filter="year", limit=3))
        print(f"✅ Top posts: {len(top_posts)} found")
        for post in top_posts[:2]:
            print(f"  - {post.title[:60]}...")
            
    except Exception as e:
        print(f"❌ Search test failed: {e}")

# Main execution
if __name__ == "__main__":
    print("🚀 Starting Reddit Scraper with Mixed Search")
    print("=" * 70)


    process_mixed_posts("cpsc 441", total_posts=4)
    
    print("\n🎛️ CUSTOM SCORING EXAMPLES:\n")
    

    scoring_configs = {
        "Recency-focused": {"vote_weight": 0.2, "recency_weight": 0.6, "length_weight": 0.2},
        "Quality-focused": {"vote_weight": 0.7, "recency_weight": 0.1, "length_weight": 0.2},
        "Detailed-focused": {"vote_weight": 0.3, "recency_weight": 0.2, "length_weight": 0.5},
        "Balanced": {"vote_weight": 0.25, "recency_weight": 0.25, "length_weight": 0.5}
    }
    
    for config_name, weights in scoring_configs.items():
        print(f"📊 {config_name} Configuration:")
        print(f"   Votes: {weights['vote_weight']:.1%}, Recency: {weights['recency_weight']:.1%}, Length: {weights['length_weight']:.1%}")