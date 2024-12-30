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


# Initialize Google Translator
translator = Translator()

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

def search_caption_with_context(transcript, query):
    matches = []
    for i, entry in enumerate(transcript):
        if query.lower() in entry['text'].lower():
            # Collect the surrounding context to form a full sentence
            start = i  
            end = min(len(transcript), i + 1)  # Include the next sentence if available
            context = transcript[start:end]
            full_sentence = ' '.join([item['text'] for item in context])
            start_time = context[0]['start']
            matches.append((start_time, full_sentence))
    return matches

def translate_text(text):
    try:
        return translator.translate(text, src='ko', dest='en').text
    except Exception as e:
        st.warning(f"Translation failed: {str(e)}")
        return "Translation not available"


@st.cache_data(ttl=3600)
def get_channel_videos(channel_id):
    videos = []
    next_page_token = None
    
    try:
        while len(videos) < 5:  # Limit to 5 videos per channel
            request = youtube.search().list(
                part="id,snippet",
                channelId=channel_id,
                maxResults=5,
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

@st.cache_data(ttl=3600)
def search_videos(query, selected_channel_id):  # Added selected_channel_id parameter
    if not youtube:
        logger.error("YouTube API client is not initialized")
        st.error("YouTube search is currently unavailable. Please try again later.")
        return []

    all_videos = get_channel_videos(selected_channel_id)  # Only search in selected channel
    
    # Sort all videos by view count
    all_videos.sort(key=lambda x: int(get_video_details(x['id']['videoId'])['viewCount']), reverse=True)
    
    return all_videos[:5]


@st.cache_data(ttl=86400)
def get_video_details(video_id):
    try:
        request = youtube.videos().list(
            part="statistics",
            id=video_id
        )
        response = request.execute()
        return response['items'][0]['statistics']
    except HttpError as e:
        st.error(f"An error occurred while fetching details for video {video_id}: {str(e)}")
        return {'viewCount': '0'}


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

# Function to display video segments with multiple timestamps using HTML iframe
def display_video_segments(video_id, matches):
    for start_time, text in matches:
        formatted_time = format_time(start_time)
        english_translation = translate_text(text)
        st.write(f"**[{formatted_time}]** {text}")
        st.write(f"Translation: {english_translation}")
        
        # Embed the video using the HTML iframe method starting at the matched timestamp
        embed_youtube_video(video_id, int(start_time))

# Streamlit app setup with tabs for different sections
st.markdown("<h1 class='title'>한국어 단어와 문법</h1>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["Quizlet", "YouTube"])

with tab1:
    lesson = st.selectbox("Select a lesson", lesson_list)
    if lesson:
        link, lesson_code = get_lesson_link(lesson)
        if link and lesson_code:
            st.markdown("Click: " f"[{lesson_code}]({link})", unsafe_allow_html=True)
  
with tab2:

        # API Key input section
        with st.expander("Use your YouTube API Key"):   
            user_api_key = st.text_input(
                "Enter your YouTube API Key",
                type="password",
                help="Get your API key from Google Cloud Console"
            )
            
            if st.button("How to get an API Key"):
                st.markdown("""
                1. Go to [Google Cloud Console](https://console.cloud.google.com/)
                2. Create a new project or select an existing one
                3. Enable the YouTube Data API v3
                4. Go to Credentials
                5. Click Create Credentials > API Key
                6. Copy the API key and paste it above
                """)

                # Modify the existing API initialization to use user's key if provided
        try:
            API_KEY = user_api_key if user_api_key else st.secrets['youtube_api']
            youtube = build('youtube', 'v3', developerKey=API_KEY)
            logger.info("YouTube API client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing YouTube API client: {str(e)}")
            #st.error("Please enter a valid YouTube API key")  
            youtube = None

        search_method = st.radio(
        "Choose search method:",
        ["Search by Channel", "Search by Video Link"]
        )

        search_term = st.text_input("Enter a Korean grammar point or phrase:")

        if search_method == "Caption Search by Channel":
            channel_options = {
                "SBS Running Man": "UCaKod3X1Tn4c7Ci0iUKcvzQ",
                "youquizontheblock": "UC920m3pMPH45qztdhppZhwA",
            }
            selected_channel = st.selectbox("Select Channel", options=list(channel_options.keys()))
            search_button = st.button("Search in Channel")

            if search_button:
                if not youtube:
                    st.error("YouTube search is currently unavailable. Please try again later.")
                elif search_term:
                    try:
                        channel_id = channel_options[selected_channel]
                        # Pass the selected channel ID to search_videos
                        results = search_videos(search_term, channel_id)
                        found_videos = 0
                        for item in results:
                            if found_videos >= 1:
                                break
                            video_id = item['id']['videoId']
                            title = item['snippet']['title']
                            channel_title = item['snippet']['channelTitle']
                            transcript = get_caption_with_timestamps(video_id)
                            if transcript:
                                matches = search_caption_with_context(transcript, search_term)
                                if matches:
                                    st.write(f"### {title}")
                                    st.write(f"Channel: {channel_title}")
                                    display_video_segments(video_id, matches)
                        
                        if found_videos == 0:
                            st.write("No videos with matching captions found. Try a different search term.")
                    except Exception as e:
                        logger.error(f"Error in YouTube search: {str(e)}")
                        st.error(f"An error occurred during the search. Please try again later.")
                else:
                    st.write("Please enter a search term.")

        else:  # Search by Video Link
            youtube_link = st.text_input("Enter YouTube link:")
            search_button = st.button("Search in Video")

            if search_button:
                if not youtube:
                    st.error("YouTube API client is not initialized.")
                elif youtube_link and search_term:
                    try:
                        video_id = youtube_link.split('v=')[1]
                        transcript = get_caption_with_timestamps(video_id)
                        if transcript:
                            matches = search_caption_with_context(transcript, search_term)
                            if matches:
                                st.write(f"### Matches found for '{search_term}' in the video:")
                                display_video_segments(video_id, matches)
                            else:
                                st.write("No matching captions found. Try a different search term.")
                    except Exception as e:
                        st.error(f"An error occurred during the search: {str(e)}")
                else:
                    st.write("Please enter both a YouTube link and a search term.")


