import streamlit as st
import sys
import os

# Ensure the project directory is accessible for importing summarizer.py
# This is generally only needed if you run the app from a different directory
sys.path.append(os.path.dirname(__file__)) 

# Import the core functions from your existing script
from main import (
    initialize_reddit, 
    fetch_and_combine_reviews, 
    run_summarizer
)

# --- Configuration ---
# Use st.cache_resource to initialize the heavy clients (PRAW and Groq) only once
@st.cache_resource
def setup_clients():
    """Initialize PRAW client once for the entire app session."""
    # Note: Groq is initialized globally in summarizer.py
    reddit = initialize_reddit(site_name="autobot") 
    return reddit

# --- Application Logic ---
def main():
    st.set_page_config(page_title="Reddit Book Review Summarizer", layout="wide")
    st.title("📚 Reddit Book Review Summarizer")
    st.markdown("Enter a book title below to fetch and summarize community reviews.")

    # Initialize clients securely (happens once)
    reddit_client = setup_clients()
    
    if not reddit_client:
        st.error("🚨 **Initialization Error:** Cannot connect to Reddit. Please ensure your `praw.ini` file is correct and accessible.")
        return

    # User Input Form
    with st.form(key='review_form'):
        book_title = st.text_input(
            "Enter Book Title ", 
            value='"Project Hail Mary"',
            help="The system will fetch a few top reviews for this title."
        )
        
        summarize_button = st.form_submit_button("Get Summary 🚀")

    # --- Processing Logic on Button Click ---
    if summarize_button and book_title:
        
        # Hardcode the low limits here to prevent API overflow
        POST_LIMIT = 2
        COMMENT_LIMIT = 2
        SUBREDDIT_LIST = "books+literature+suggestmeabook"

        with st.spinner(f"Fetching {POST_LIMIT} posts from r/{SUBREDDIT_LIST} and summarizing with Groq..."):
            
            # 1. Fetch Data with hardcoded limits
            combined_text = fetch_and_combine_reviews(
                reddit_client,
                SUBREDDIT_LIST,
                book_title,
                post_limit=POST_LIMIT,
                comment_limit=COMMENT_LIMIT
            )

            if combined_text and 'ERROR' not in combined_text:
                
                # 2. Summarize Data
                summary_result = run_summarizer(combined_text)

                # 3. Display Result
                st.success(f"✨ Summary for: **{book_title.strip('\"')}**")
                
                # Check for Groq errors returned by the summarizer function
                if "ERROR during Groq API call" in summary_result:
                    st.error(summary_result)
                    st.warning("Hint: The combined text still exceeded the API's token limit. The API's rate limits are very strict.")
                else:
                    st.markdown("---")
                    st.info(summary_result)
                    st.markdown("---")
                    
                    # Optional: Show the raw data size (for transparency/debugging)
                    st.subheader("Data Metrics")
                    st.write(f"Posts Analyzed: **{POST_LIMIT}**")
                    st.write(f"Max Comments Analyzed per Post: **{COMMENT_LIMIT}**")
                    st.caption("These low settings were used to comply with the free tier API limits.")
            else:
                st.warning(f"Could not find enough high-quality reviews for **{book_title}** in the target subreddits.")
                
if __name__ == '__main__':
    # Ensure encoding is set if needed
    try:
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass 

    main()