import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptAvailable, NoTranscriptFound
from googleapiclient.errors import HttpError
from googletrans import Translator
import os


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

# Define the channel IDs
CHANNEL_IDS = [
     
    
    "UCaKod3X1Tn4c7Ci0iUKcvzQ",  # SBS Running Man
    "UC920m3pMPH45qztdhppZhwA"   # youquizontheblock
    
]

# Function to get captions with timestamps for a video
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

# Function to search for specific phrases in the captions
def search_caption_with_context(transcript, query):
    matches = []
    for entry in transcript:
        if query.lower() in entry['text'].lower():
            start_time = entry['start']
            end_time = start_time + entry['duration']
            full_text = entry['text']
            matches.append((start_time, end_time, full_text))
    return matches

# Function to translate text from Korean to English
def translate_text(text):
    try:
        return translator.translate(text, src='ko', dest='en').text
    except Exception as e:
        st.warning(f"Translation failed: {str(e)}")
        return "Translation not available"

# Function to get videos from a specific YouTube channel
@st.cache_data(ttl=3600)
def get_channel_videos(channel_id):
    videos = []
    next_page_token = None
    
    try:
        while len(videos) < 10:  # Limit to 10 videos per channel
            request = youtube.search().list(
                part="id,snippet",
                channelId=channel_id,
                maxResults=10,
                order="viewCount",
                type="video",
                pageToken=next_page_token
            )
            response = request.execute()
            
            videos.extend(response['items'])
            next_page_token = response.get('nextPageToken')
            
            if not next_page_token:
                break
    except HttpError as e:
        logger.error(f"An error occurred while fetching videos for channel {channel_id}: {str(e)}")
        st.error(f"An error occurred while fetching videos. Please try again later.")
        return []
    
    return videos

# Function to search for videos across channels based on a query
@st.cache_data(ttl=3600)
def search_videos(query):
    if not youtube:
        logger.error("YouTube API client is not initialized")
        st.error("YouTube search is currently unavailable. Please try again later.")
        return []

    all_videos = []
    for channel_id in CHANNEL_IDS:
        all_videos.extend(get_channel_videos(channel_id))
    
    # Sort all videos by view count
    all_videos.sort(key=lambda x: int(get_video_details(x['id']['videoId'])['viewCount']), reverse=True)
    
    return all_videos[:50]  # Return top 50 most viewed videos across all channels

# Function to get video details such as view count
@st.cache_data(ttl=86400)
def get_video_details(video_id): #updated HttpError
    try:
        request = youtube.videos().list(
            part="statistics",
            id=video_id
        )
        response = request.execute()
        return response['items'][0]['statistics']
    except HttpError as e:
        if e.resp.status == 403:
            st.error("API quota reached. Please try again later.")
            return None
        else:
            raise e

# Function to format time from seconds to HH:MM:SS
def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# Function to handle the YouTube search and display results
def youtube_search_tab():
    st.header("YouTube Search")
    search_term = st.text_input("Enter a Korean grammar point or phrase:")
    if st.button("Search"):
        if not youtube:
            st.error("YouTube search is currently unavailable. Please try again later.")
            return

        if search_term:
            try:
                results = search_videos(search_term)
                found_videos = 0
                for item in results:
                    if found_videos >= 3:
                        break
                    video_id = item['id']['videoId']
                    title = item['snippet']['title']
                    channel_title = item['snippet']['channelTitle']
                    transcript = get_caption_with_timestamps(video_id)
                    if transcript:
                        matches = search_caption_with_context(transcript, search_term)
                        if matches:
                            video_stats = get_video_details(video_id)
                            view_count = int(video_stats['viewCount'])
                            st.write(f"### {title}")
                            st.write(f"Channel: {channel_title}")
                            
                            # Correct the order and variable usage
                            timestamp, end_time, text = matches[0]  # Only use the first match
                            formatted_time = format_time(timestamp)
                            st.write(f"**[{formatted_time}]** {text}")
                            
                            english_translation = translate_text(text)
                            st.write(f"Translation: {english_translation}")
                            
                            # Embed the video with the correct timestamp
                            st.video(f"https://www.youtube.com/watch?v={video_id}&t={int(timestamp)}s")
                            
                            found_videos += 1
                if found_videos == 0:
                    st.write("No videos with matching captions found. Try a different search term.")
            except Exception as e:
                logger.error(f"Error in YouTube search: {str(e)}")
                st.error(f"An error occurred during the search. Please try again later.")
        else:
            st.write("Please enter a search term.")


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
        youtube_search_tab()






