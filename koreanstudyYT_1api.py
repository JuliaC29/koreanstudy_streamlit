import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptAvailable, NoTranscriptFound
from googleapiclient.errors import HttpError
from googletrans import Translator


# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom CSS to center the title and style the audio buttons
st.markdown("""
<style>
    .title {
        text-align: center;
    }
    .stAudio {
        display: inline-block;
        width: 30px !important;
        height: 30px !important;
        margin-left: 10px;
    }
    .stAudio > div {
        height: 30px !important;
    }
    .stAudio audio {
        height: 30px !important;
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

# Quizlet
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

# Load API key from Streamlit secrets into environment variable
#import os
#os.environ['youtube_api'] = st.secrets['youtube_api']

# Initialize YouTube API client
try:
    API_KEY = st.secrets['youtube_api']
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    logger.info("YouTube API client initialized successfully")
    #st.write("YouTube API client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing YouTube API client: {str(e)}")
    st.error("Error initializing YouTube API. Please check your API key configuration.")
    #st.write(f"Error initializing YouTube API client: {str(e)}")
    youtube = None

translator = Translator()


# Define the channel IDs
CHANNEL_IDS = [
     
    "UCAmia3u27mHY-Y6c-lwakAQ",  # Pororo
    "UCaKod3X1Tn4c7Ci0iUKcvzQ",  # SBS Running Man
    
]


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
            start = max(0, i - 1)
            end = min(len(transcript), i + 2)
            context = transcript[start:end]
            full_text = ' '.join(item['text'] for item in context)
            start_time = context[0]['start']
            matches.append((start_time, full_text))
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
        while len(videos) < 50:  # Limit to 50 videos per channel
            request = youtube.search().list(
                part="id,snippet",
                channelId=channel_id,
                maxResults=50,
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

def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

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
                            timestamp, text = matches[0]  # Only use the first match
                            formatted_time = format_time(timestamp)
                            st.video(f"https://www.youtube.com/watch?v={video_id}&t={int(timestamp)}s")
                            st.write(f"**[{formatted_time}]** {text}")
                            english_translation = translate_text(text)
                            st.write(f"Translation: {english_translation}")
                            found_videos += 1
                if found_videos == 0:
                    st.write("No videos with matching captions found. Try a different search term.")
            except Exception as e:
                logger.error(f"Error in YouTube search: {str(e)}")
                st.error("An error occurred during the search. Please try again later.")
        else:
            st.write("Please enter a search term.")


# Streamlit app
# Centered title
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






