import praw
import sys
import os
from groq import Groq

from dotenv import load_dotenv
load_dotenv

key_from_env = os.environ.get("GROQ_API_KEY") 
print(f"DEBUG: Key status as seen by Python: {'PRESENT' if key_from_env else 'MISSING'}")
try:
    groq_client = Groq()
    print("✅ Groq Client initialized successfully.")
except Exception as e:
    groq_client = None
    print(f"❌ ERROR: Groq client failed to initialize. Ensure GROQ_API_KEY is set in your environment variables.")

def initialize_reddit(site_name="autobot"):
    """Initializes the PRAW Reddit instance using the [bot1] profile in praw.ini."""
    try:
        reddit = praw.Reddit(site_name=site_name)
        
        if reddit.read_only:
            print(f"PRAW initialized in read-only mode for profile: {site_name}.")
        else:
            print(f"✅ PRAW successfully authenticated as: u/{reddit.user.me()} for profile: {site_name}")
        
        return reddit
    
    except Exception as e:
        print(f"❌ ERROR: Could not initialize PRAW with site_name '{site_name}'.")
        print("ACTION REQUIRED: Check your credentials and the formatting in your praw.ini file.")
        print(f"Details: {e}")
        return None


def fetch_and_combine_reviews(reddit_instance, subreddit_name, search_term, post_limit=4, comment_limit=5):
    """
    Fetches the top X posts and top Y comments from each, combining all text 
    into a single string for summarization input.
    """
    if not reddit_instance:
        return ""

    print(f"\nSearching r/{subreddit_name} for the top {post_limit} posts about: '{search_term}'...")
    
    combined_summary_input = "" 
    total_comments_collected = 0
    post_count = 0

    for submission in reddit_instance.subreddit(subreddit_name).search(
        query=search_term,
        sort='relevance',
        limit=post_limit 
    ):
        if submission.is_self and submission.selftext and len(submission.selftext) > 100:
            post_count += 1
            
            combined_summary_input += f"\n\n--- POST {post_count}: {submission.title.upper()} ---\n"
            
            combined_summary_input += submission.selftext 
            
            submission.comments.replace_more(limit=0) 
            collected_comments = []
            
            for comment in submission.comments.list():
                if comment.score >= 5 and len(comment.body) > 50:
                    collected_comments.append(comment.body)
                    total_comments_collected += 1
                    
                if len(collected_comments) >= comment_limit:
                    break
            
            if collected_comments:
                 combined_summary_input += "\n\n--- TOP COMMENTS ---\n"
                 combined_summary_input += "\n".join(collected_comments)
            
            print(f"  -> Processed Post {post_count}: '{submission.title}' with {len(collected_comments)} quality comments.")

    print(f"\n--- DATA COLLECTION COMPLETE ---")
    print(f"Total Posts Processed: {post_count}")
    print(f"Total Comments Collected: {total_comments_collected}")
    
    return combined_summary_input

# The run_summarizer function must access the global groq_client variable
def run_summarizer(input_text):
    """
    Uses the Groq API to generate an abstractive summary from the combined review text.
    """
    
    # --- ❌ ERROR REMOVED: Deleted the hardcoded key line ---
    # The client created in the main body (groq_client) is now used directly.

    if groq_client is None: # Check if the client initialized globally failed
        return "ERROR: Groq client not initialized. Cannot summarize."
    
    if not input_text:
        return "ERROR: No input text was provided for summarization."

    print("\n--- SUMMARIZATION MODULE ACTIVATED (via Groq) ---")

    system_prompt = (
        "You are an expert book reviewer. Analyze the following collection of Reddit posts and comments "
        "about a single book. Generate a concise, objective summary (2 paragraphs maximum) that highlights "
        "the main themes, the most common praise (Pros), and the most frequent criticisms (Cons) mentioned by readers. "
        "Do not include any introductory or concluding sentences outside of the main summary."
    )
    
    try:
        # ✅ FIX: Use the global groq_client object initialized at the start of the script.
        chat_completion = groq_client.chat.completions.create( 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ],
        
            model="llama-3.1-8b-instant", 
            temperature=0.2 
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        return f"ERROR during Groq API call: {e}"

# NOTE: You MUST ensure you set your GROQ_API_KEY environment variable 
# correctly in your terminal before running this script again!
if __name__ == "__main__":
    
 
    reddit = initialize_reddit()

    if reddit:
       
        TARGET_BOOK = '"A Little Life"'  
        TARGET_SUBREDDIT = "books+literature" 

        final_review_text = fetch_and_combine_reviews(
            reddit,
            TARGET_SUBREDDIT,
            TARGET_BOOK,
            post_limit=2,    
            comment_limit=2
        )

        if final_review_text:
            
            final_summary = run_summarizer(final_review_text)

            print("\n" + "=" * 60)
            print("🚀 FINAL BOOK REVIEW SUMMARY")
            print(f"Source: r/{TARGET_SUBREDDIT} | Book: {TARGET_BOOK}")
            print("-" * 60)
            print(final_summary)
            print("=" * 60)
            
        else:
            print(f"\n❌ Final output failure: Could not find enough data to summarize.")