import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptAvailable, NoTranscriptFound
from googleapiclient.errors import HttpError
from googletrans import Translator
import os
import re


# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom CSS to center the title
st.markdown("""
<style>
    .title {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Load CSV data
@st.cache_data
def load_csv_data():
    try:
        df = pd.read_csv('data/fcstr1.csv')
        lesson_list = df['lesson'].unique().tolist()      
        return df, lesson_list
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        return None, []

df, lesson_list = load_csv_data()

# Function to retrieve Quizlet links for selected lessons
def get_lesson_link(lesson):
    try:
        row = df[df['lesson'] == lesson].iloc[0]
        link = row['link']
        lesson_code = row['lesson_code']
        logger.info(f"Successfully retrieved link for lesson: {lesson}")
        return link, lesson_code
    except Exception as e:
        logger.error(f"Error in get_lesson_link: {e}")
        return None, None


# Load multiple YouTube API keys from Streamlit secrets and initialize the YouTube API client.
# The system attempts to initialize the API using the first available key.
# If a key exceeds its usage quota (HTTP 403 error), it automatically switches to the next key in the list.
# If all keys are exhausted, an exception is raised.

api_keys = [
    st.secrets["youtube_api1"],
    st.secrets["youtube_api2"],
    st.secrets["youtube_api3"]
]
current_key_index = 0

def initialize_youtube_api():
    global current_key_index
    while current_key_index < len(api_keys):
        try:
            api_key = api_keys[current_key_index].strip()
            youtube = build('youtube', 'v3', developerKey=api_key)
            return youtube
        except HttpError as e:
            if e.resp.status == 403:
                current_key_index += 1
                if current_key_index >= len(api_keys):
                    raise Exception("All API keys have reached their usage quota.")
            else:
                raise e

try:
    youtube = initialize_youtube_api()
except Exception as e:
    st.error("Error initializing YouTube API. Please check your API key configuration.")
    youtube = None

# Initialize Google Translator
translator = Translator()

# Function to extract video ID from YouTube link
def extract_video_id(youtube_url):
    match = re.search(r"(?<=v=)[\w-]+|(?<=be/)[\w-]+", youtube_url)
    if match:
        return match.group(0)
    else:
        st.error("Invalid YouTube link")
        return None

# Function to get captions with timestamps for a specific video
@st.cache_data(ttl=86400)
def get_caption_with_timestamps(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
        return transcript
    except (TranscriptsDisabled, NoTranscriptAvailable, NoTranscriptFound):
        return None
    except Exception as e:
        st.warning(f"Captions not available for video {video_id}: {str(e)}")
        return None

# Function to search for a specific phrase in the captions
def search_caption_with_context(transcript, query):
    matches = []
    for entry in transcript:
        if query.lower() in entry['text'].lower():
            start_time = entry['start']
            full_text = entry['text']
            matches.append((start_time, full_text))
    return matches

# Function to translate text from Korean to English
def translate_text(text):
    try:
        return translator.translate(text, src='ko', dest='en').text
    except Exception as e:
        st.warning(f"Translation failed: {str(e)}")
        return "Translation not available"

# Function to format time from seconds to HH:MM:SS
def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# Function to embed YouTube video with HTML iframe starting at a specific timestamp
def embed_youtube_video(video_id, start_time_seconds):
    youtube_url = f"https://www.youtube.com/embed/{video_id}?start={start_time_seconds}"
    video_html = f"""
        <iframe width="700" height="400" src="{youtube_url}" frameborder="0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
    """
    st.markdown(video_html, unsafe_allow_html=True)

# Function to handle the YouTube link and caption search
def youtube_search_by_link():
    st.header("YouTube Caption Search")
    youtube_url = st.text_input("Paste the YouTube link here:")
    search_term = st.text_input("Enter a Korean grammar point or phrase:")
    
    if st.button("Search"):
        if youtube_url:
            video_id = extract_video_id(youtube_url)
            if video_id:
                transcript = get_caption_with_timestamps(video_id)
                if transcript:
                    matches = search_caption_with_context(transcript, search_term)
                    if matches:
                        # Use the first match to show video starting at the correct timestamp
                        timestamp, text = matches[0]
                        formatted_time = format_time(timestamp)
                        st.write(f"**[{formatted_time}]** {text}")
                        
                        english_translation = translate_text(text)
                        st.write(f"Translation: {english_translation}")
                        
                        # Embed the video using an iframe with the correct timestamp
                        embed_youtube_video(video_id, int(timestamp))
                    else:
                        st.write("No matching captions found. Try a different search term.")
                else:
                    st.write("Captions are not available for this video.")
        else:
            st.write("Please provide a valid YouTube link.")


# Streamlit app setup with tabs for different sections
st.markdown("<h1 class='title'>한국어 단어와 문법</h1>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["Vocabulary", "Grammar"])

with tab1:
    lesson = st.selectbox("Select a lesson", lesson_list)
    if lesson:
        link, lesson_code = get_lesson_link(lesson)
        if link and lesson_code:
            st.markdown("Click: " f"[{lesson_code}]({link})", unsafe_allow_html=True)
  
with tab2:
        youtube_search_by_link()






