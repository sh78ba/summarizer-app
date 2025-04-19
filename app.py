
import streamlit as st
from transformers import pipeline
from bertopic import BERTopic
import feedparser
import requests
import random

# -------------------------------
# 1. App Configuration
# -------------------------------
st.set_page_config(page_title="Personalized Summarizer", layout="wide")
st.title("📰 Personalized/News Summarizer")

# -------------------------------
# 2. Load Models
# -------------------------------
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

@st.cache_resource
def load_topic_model():
    return BERTopic(embedding_model="all-MiniLM-L6-v2")

summarizer = load_summarizer()
topic_model = load_topic_model()

# -------------------------------
# 3. Fetch Articles from RSS Feed
# -------------------------------
def fetch_articles(url, user_agent):
    headers = {
        "User-Agent": user_agent
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        feed = feedparser.parse(response.content)

        if feed.bozo:
            st.warning(f"⚠️ Feed parse warning: {feed.bozo_exception}")

        if not feed.entries:
            st.error("❌ No entries found in the RSS feed.")
            return []

        return [{"title": entry.title, "content": entry.summary} for entry in feed.entries[:10]]

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Failed to fetch RSS feed: {e}")
        return []

# -------------------------------
# 4. Sidebar: User Preferences
# -------------------------------
with st.sidebar:
    st.header("Settings")
    user_interests = st.text_input("Your interests (comma-separated)", "AI, Technology, Startups")
    max_length_slider = st.slider("Maximum Summary Length", 50, 300, 150)

# -------------------------------
# 5. Input Tabs: RSS Feed or Custom Text
# -------------------------------
tab1, tab2 = st.tabs(["📡 RSS Feed", "📝 Custom Text"])
articles = []

# Filter articles based on user interests
def filter_articles_by_interests(raw_articles, interests):
    interests = [kw.strip().lower() for kw in interests.split(",")]
    filtered_articles = [
        article for article in raw_articles
        if any(kw in article["title"].lower() or kw in article["content"].lower() for kw in interests)
    ]
    return filtered_articles

# -------------------------------
# 6. Tab 1: RSS Feed
# -------------------------------
with tab1:
    rss_url = st.text_input("Enter RSS Feed URL", "https://auto.hindustantimes.com/rss/latest-news")
    
    # List of User-Agents (internally defined)
    user_agent_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.67 Safari/537.36"
    ]
    
    # Randomly select a User-Agent internally
    user_agent = random.choice(user_agent_list)

    if rss_url:
        raw_articles = fetch_articles(rss_url, user_agent)

        if raw_articles:
            filtered_articles = filter_articles_by_interests(raw_articles, user_interests)
            if filtered_articles:
                st.markdown("### Fetched Articles and Summaries")
                for article in filtered_articles:
                    with st.expander(article["title"]):
                        content_tokens = article["content"].split()
                        truncated_content = " ".join(content_tokens[:1024])
                        optimal_max_len = min(max_length_slider, max(30, len(truncated_content.split()) // 2))
                        summary = summarizer(
                            truncated_content,
                            max_length=optimal_max_len,
                            min_length=optimal_max_len // 2,
                            do_sample=False
                        )
                        st.write(summary[0]["summary_text"])
            else:
                st.warning(f"⚠️ No articles found matching your interests: {user_interests}")
        else:
            st.info("ℹ️ No articles found. Check the feed URL or try a different one.")

# -------------------------------
# 7. Tab 2: Custom Text
# -------------------------------
with tab2:
    input_text = st.text_area("Paste your text here", height=200)
    if input_text:
        input_tokens = input_text.split()
        truncated_input = " ".join(input_tokens[:1024])
        optimal_max_len = min(max_length_slider, max(30, len(truncated_input.split()) // 2))
        summary = summarizer(
            truncated_input,
            max_length=optimal_max_len,
            min_length=optimal_max_len // 2,
            do_sample=False
        )
        st.subheader("Summary")
        st.write(summary[0]["summary_text"])

