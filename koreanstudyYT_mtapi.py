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
def search_videos(query, channel_id):  # Added selected_channel_id parameter
    if not youtube:
        logger.error("YouTube API client is not initialized")
        st.error("YouTube search is currently unavailable. Please try again later.")
        return []

    all_videos = get_channel_videos(channel_id)  # Only search in selected channel
    
    # Sort all videos by view count
    all_videos.sort(key=lambda x: int(get_video_details(x['id']['videoId'])['viewCount']), reverse=True)
    
    return all_videos[:1]


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
    
    <style>
    .video-container {{
        position: relative;
        width: 100%;
        padding-bottom: 56.25%;
        margin-bottom: 20px;
    }}
    .video-container iframe {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }}
    </style>
    <div class="video-container">
        <iframe 
            src="{youtube_url}" 
            frameborder="0" 
            allowfullscreen>
        </iframe>
    </div>
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
    # API Key section
    access_type = st.radio("Choose access method:", ["Enter Access Code", "Use your API Key"])
    
    if access_type == "Enter Access Code":
        access_code = st.text_input("Enter access code", type="password", help="Contact instructor for code")
        if access_code:
            try:
                user_api_key = st.secrets.api_codes[access_code]
            except:
                st.error("Invalid access code.")
                st.stop()
    else:
        user_api_key = st.text_input("Enter Your YouTube API Key", type="password", 
                                    help="Get API key from Google Cloud Console")
        if st.button("How to get an API Key"):
            st.markdown("""
            1. Go to [Google Cloud Console](https://console.cloud.google.com/)
            2. Create a new project or select an existing one
            3. Enable the YouTube Data API v3
            4. Go to Credentials
            5. Click Create Credentials > API Key
            6. Copy the API key and paste it above
            """)
            
        if user_api_key:
            try:
                # Test API key validity
                youtube = build('youtube', 'v3', developerKey=user_api_key)
                test = youtube.videos().list(part="snippet", id="dQw4w9WgXcQ").execute()
            except:
                st.error("Invalid API key.")
                st.stop()
        else:
            st.warning("Please enter an API key.")
            st.stop()


        if not user_api_key:
            st.warning("Please enter your API key to continue.")
            st.stop()


    # try:
    try:
        youtube = build('youtube', 'v3', developerKey=user_api_key)
        logger.info("YouTube API initialized successfully")
    except Exception as e:
        #st.error("Invalid API key. Please check and try again.")
        st.stop()


    # Search methods
    search_method = st.radio(
        "Choose search method:",
        ["Search by Video Link", "Search by Channel"]
    )

    search_term = st.text_input("Enter a Korean grammar point or phrase:", key="search_term_tab2")

    if search_method == "Search by Channel":
        channel_options = {
            "youquizontheblock": "UC920m3pMPH45qztdhppZhwA",
            "SBS Running Man": "UCaKod3X1Tn4c7Ci0iUKcvzQ",
            "DdeunDdeun": "UCDNvRZRgvkBTUkQzFoT_8rA",  
    
        }
        selected_channel = st.selectbox("Select Channel", options=list(channel_options.keys()))

        if st.button("Search in Channel", key="channel_search"):
            if youtube and search_term:
                try:
                    channel_id = channel_options[selected_channel]
                    results = search_videos(search_term, channel_id)
                    
                    for item in results:
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
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
            else:
                st.error("Please enter a search term and ensure API key is valid")

    else:
        youtube_link = st.text_input("Enter YouTube link:", key="video_link_tab2")
        
        if st.button("Search in Video", key="video_search"):
            if youtube and youtube_link and search_term:
                try:
                    video_id = youtube_link.split('v=')[1]
                    transcript = get_caption_with_timestamps(video_id)
                    if transcript:
                        matches = search_caption_with_context(transcript, search_term)
                        if matches:
                            st.write(f"### Matches found for '{search_term}' in the video:")
                            display_video_segments(video_id, matches)
                        else:
                            st.write("No matching captions found.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
            else:
                st.write("Please enter both a YouTube link and a search term.")


