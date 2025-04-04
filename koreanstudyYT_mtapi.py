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

# Load CSV data for YouTube
@st.cache_data
def load_grammar_csv_data():
    try:
        df = pd.read_csv('data/fcstr2.csv')  # Your YouTube CSV file
        lesson_list = df['lesson'].unique().tolist()

        return df, lesson_list
    except Exception as e:
        st.error(f"Error loading grammar CSV file: {e}")
        return None, []

df_grammar, lesson_list_grammar = load_grammar_csv_data()


# YouTube
def get_grammar_videos(lesson):
    try:
        videos_data = df_grammar[df_grammar['lesson'] == lesson]
        grammar_points = []
        videos_list = []
        
        
        for index, row in videos_data.iterrows():
            grammar_points.append(row['grammar_point'])
            #videos_list.append((row['youtube_link'], row['timestamp']))
            videos_list.append((row['youtube_link'], row['timestamp'], row['end']))
           

        return list(set(grammar_points)), videos_list
    except Exception as e:
        logger.error(f"Error getting videos: {e}")
        return [], []


def extract_video_id(url):
    try:
        if 'v=' in url:
            return url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            return url.split('youtu.be/')[1]
        return url
    except:
        return url

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
    try:
        request = youtube.search().list(
            part="id,snippet",
            channelId=channel_id,
            maxResults=50,  # Get maximum results per request
            order="viewCount",
            type="video"
        )
        response = request.execute()
        return response['items']  # Return all items
    except HttpError as e:
        logger.error(f"Error fetching videos: {str(e)}")
        return []



@st.cache_data(ttl=3600)
def search_videos(query, channel_id):
    if not youtube:
        logger.error("YouTube API client is not initialized")
        st.error("YouTube search is currently unavailable. Please try again later.")
        return []

    all_videos = get_channel_videos(channel_id)  # Get all videos
    
    # Sort all videos by view count
    all_videos.sort(key=lambda x: int(get_video_details(x['id']['videoId'])['viewCount']), reverse=True)
    
    return all_videos[:5]  # Return top 5 here


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
tab1, tab2, tab3, tab4 = st.tabs(["Quizlet", "Video Examples", "YouTube Search", "NEW"])

with tab1:
    lesson = st.selectbox("Select a lesson", lesson_list)
    if lesson:
        link, lesson_code = get_lesson_link(lesson)
        if link and lesson_code:
            st.markdown("Click: " f"[{lesson_code}]({link})", unsafe_allow_html=True)
  

# Selected Youtube Clips
with tab2:
   # Access code check at the start of tab2
    passcode = st.text_input("Enter passcode", type="password", key="video_examples_passcode")
    if not passcode:
        st.warning("Please enter a passcode to view content")
    elif passcode not in st.secrets["passcode"]:
        st.error("Invalid passcode")
    else:    

        lesson = st.selectbox("Select lesson", lesson_list_grammar)

        if lesson:
            lesson_data = df_grammar[df_grammar['lesson'] == lesson]
            grammar_points = lesson_data['grammar_point'].unique().tolist()
            


            if grammar_points:
                selected_grammar = st.selectbox("Select grammar point", grammar_points)
                if selected_grammar:
                    videos = lesson_data[lesson_data['grammar_point'] == selected_grammar]
                    if pd.isna(videos['youtube_link'].iloc[0]) or videos['youtube_link'].iloc[0] == "COMING_SOON":
                        st.info("Video examples for this grammar point will be added soon!")
                    else:

                        for _, video in videos.iterrows():
                            video_id = extract_video_id(video['youtube_link'])
                            clean_video_id = video_id.split('?')[0].split('&')[0]
                            
                            video_url = f"https://www.youtube.com/embed/{video_id}&start={int(video['timestamp'])}&end={int(video['end'])}&loop=1"
                            youtube_full_url = f"https://www.youtube.com/watch?v={video_id}&t={int(video['timestamp'])}s"

                            # Create two columns for replay button and timestamp
                            col1, col2 = st.columns([0.12, 1.8])  # Adjust ratio as needed
                            with col1:
                                if st.button("🔄", key=f"replay_{clean_video_id}_{video['timestamp']}"):
                                    video_url = f"https://www.youtube.com/embed/{video_id}&start={int(video['timestamp'])}&end={int(video['end'])}&autoplay=1"
                            with col2:
                                st.markdown(f"<div style='padding-top: 5px;'>{video['time_format']}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div style='padding-top: 5px;'><a href='{youtube_full_url}' target='_blank'>Watch on YouTube</a></div>", unsafe_allow_html=True)
                            
                            # Video container
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
                                    src="{video_url}" 
                                    frameborder="0" 
                                    allowfullscreen>
                                </iframe>
                            </div>
                            """          
                            
                            st.markdown(video_html, unsafe_allow_html=True)
                            
                            # Show/Hide text buttons with cleaned ID
                            if st.button("Show Korean", key=f"kor_{clean_video_id}_{video['timestamp']}"):
                                st.write(f"**Korean:** {video['korean_text']}")
                            if st.button("Show English", key=f"eng_{clean_video_id}_{video['timestamp']}"):
                                st.write(f"**English:** {video['english_text']}")


with tab3:
    st.markdown("""
    <h2 style='text-align: center; font-size: 24px; margin-bottom: 5px;'>
        YouTube Caption Search
    </h2>
    """, 
    unsafe_allow_html=True
    )
    # API Key section
    access_type = st.radio("Choose access method:", ["Enter Access Code", "Use your API Key"])
    
    if access_type == "Enter Access Code":
        access_code = st.text_input("Enter access code", type="password", key="youtube_search_access") #help="Contact instructor for code")
        if access_code:
            try:
                user_api_key = st.secrets.api_codes[access_code]
            except:
                st.error("Invalid access code.")
                st.stop()
    else:
        user_api_key = st.text_input("Enter Your YouTube API Key", type="password", 
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
            
            "SBS Running Man": "UCaKod3X1Tn4c7Ci0iUKcvzQ",
            "DdeunDdeun": "UCDNvRZRgvkBTUkQzFoT_8rA", 
            "channel fullmoon" : "UCQ2O-iftmnlfrBuNsUUTofQ",
             
    
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
                    # Handle different YouTube URL formats
                    if 'youtu.be/' in youtube_link:
                        video_id = youtube_link.split('youtu.be/')[1].split('?')[0]
                    elif 'v=' in youtube_link:
                        video_id = youtube_link.split('v=')[1].split('&')[0]
                    else:
                        st.error("Invalid YouTube URL format")
                        st.stop()

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

# New Website Link
with tab4:
    'My Korean Study: https://mykoreanstudy.netlify.app/'