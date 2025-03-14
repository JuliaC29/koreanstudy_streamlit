import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptAvailable, NoTranscriptFound
from googleapiclient.errors import HttpError
from googletrans import Translator
import re
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom CSS
st.markdown("""
<style>
    .title {
        text-align: center;
    }
    .video-container {
        position: relative;
        width: 100%;
        padding-bottom: 56.25%;
        margin-bottom: 20px;
    }
    .video-container iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions
def extract_video_id(url):
    try:
        if 'v=' in url:
            return url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            return url.split('youtu.be/')[1].split('?')[0]
        return url
    except:
        return url

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
        translator = Translator()
        return translator.translate(text, src='ko', dest='en').text
    except Exception as e:
        st.warning(f"Translation failed: {str(e)}")
        return "Translation not available"

@st.cache_data(ttl=3600)
def get_channel_videos(youtube, channel_id):
    try:
        request = youtube.search().list(
            part="id,snippet",
            channelId=channel_id,
            maxResults=50,
            order="viewCount",
            type="video"
        )
        response = request.execute()
        return response['items']
    except HttpError as e:
        logger.error(f"Error fetching videos: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def search_videos(youtube, query, channel_id):
    all_videos = get_channel_videos(youtube, channel_id)
    
    # Sort all videos by view count
    try:
        all_videos.sort(key=lambda x: int(get_video_details(youtube, x['id']['videoId'])['viewCount']), reverse=True)
    except:
        pass
    
    return all_videos[:20]  # Return top 20

@st.cache_data(ttl=86400)
def get_video_details(youtube, video_id):
    try:
        request = youtube.videos().list(
            part="statistics",
            id=video_id
        )
        response = request.execute()
        return response['items'][0]['statistics']
    except Exception as e:
        logger.error(f"Error fetching video details: {str(e)}")
        return {'viewCount': '0'}

def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def embed_youtube_video(video_id, start_time_seconds):
    youtube_url = f"https://www.youtube.com/embed/{video_id}?start={start_time_seconds}"
    video_html = f"""
    <div class="video-container">
        <iframe 
            src="{youtube_url}" 
            frameborder="0" 
            allowfullscreen>
        </iframe>
    </div>
    """  
    st.markdown(video_html, unsafe_allow_html=True)

def display_video_segments(video_id, matches):
    for start_time, text in matches:
        formatted_time = format_time(start_time)
        english_translation = translate_text(text)
        st.write(f"**[{formatted_time}]** {text}")
        st.write(f"Translation: {english_translation}")
        
        # Embed video at the timestamp
        embed_youtube_video(video_id, int(start_time))

# Main App
st.markdown("<h2 class='title'>YouTube Caption Search</h2>", unsafe_allow_html=True)

# API Key handling
api_key = None

access_type = st.radio("Choose access method:", ["Enter Access Code", "Use your API Key"])

if access_type == "Enter Access Code":
    access_code = st.text_input("Enter access code", type="password")
    if access_code:
        try:
            # Try to get from Streamlit secrets
            api_key = st.secrets.api_codes.get(access_code)
            if not api_key:
                st.error("Invalid access code.")
        except:
            st.error("Invalid access code or secret configuration.")
else:
    api_key = st.text_input("Enter Your YouTube API Key", type="password", 
                          help="Get API key from Google Cloud Console")
    
    with st.expander("How to get an API Key"):
        st.markdown("""
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a new project or select an existing one
        3. Enable the YouTube Data API v3
        4. Go to Credentials
        5. Click Create Credentials > API Key
        6. Copy the API key and paste it above
        """)

# Initialize YouTube API client
youtube = None
if api_key:
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        logger.info("YouTube API initialized successfully")
    except Exception as e:
        st.error(f"Error initializing YouTube API: {str(e)}")
        st.stop()
else:
    st.warning("Please enter an API key to continue.")
    st.stop()

# Search options
search_method = st.radio(
    "Choose search method:",
    ["Search by Video Link", "Search by Channel"]
)

search_term = st.text_input("Enter a Korean grammar point or phrase:")

if search_method == "Search by Channel":
    channel_options = {
        "SBS Running Man": "UCaKod3X1Tn4c7Ci0iUKcvzQ",
        "DdeunDdeun": "UCDNvRZRgvkBTUkQzFoT_8rA", 
        "channel fullmoon": "UCQ2O-iftmnlfrBuNsUUTofQ",
    }
    selected_channel = st.selectbox("Select Channel", options=list(channel_options.keys()))

    if st.button("Search in Channel"):
        if youtube and search_term:
            with st.spinner("Searching videos..."):
                try:
                    channel_id = channel_options[selected_channel]
                    results = search_videos(youtube, search_term, channel_id)
                    
                    if not results:
                        st.warning("No videos found in this channel.")
                    
                    found_matches = False
                    for item in results:
                        video_id = item['id']['videoId']
                        title = item['snippet']['title']
                        channel_title = item['snippet']['channelTitle']
                        
                        with st.spinner(f"Analyzing captions for: {title}"):
                            transcript = get_caption_with_timestamps(video_id)
                            
                            if transcript:
                                matches = search_caption_with_context(transcript, search_term)
                                if matches:
                                    found_matches = True
                                    st.write(f"### {title}")
                                    st.write(f"Channel: {channel_title}")
                                    display_video_segments(video_id, matches)
                    
                    if not found_matches:
                        st.warning(f"No matches found for '{search_term}' in any videos from this channel.")
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.error("Please enter a search term and ensure API key is valid")


            

else:
    youtube_link = st.text_input("Enter YouTube link:")
    
    if st.button("Search in Video"):
        if youtube and youtube_link and search_term:
            with st.spinner("Analyzing video captions..."):
                try:
                    video_id = extract_video_id(youtube_link)
                    if not video_id:
                        st.error("Invalid YouTube URL format")
                        st.stop()

                    transcript = get_caption_with_timestamps(video_id)
                    if transcript:
                        matches = search_caption_with_context(transcript, search_term)
                        if matches:
                            st.write(f"### Matches found for '{search_term}' in the video:")
                            display_video_segments(video_id, matches)
                        else:
                            st.warning(f"No matches found for '{search_term}' in the video captions.")
                    else:
                        st.warning("No captions available for this video.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.error("Please enter both a YouTube link and a search term.")