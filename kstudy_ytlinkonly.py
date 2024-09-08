import streamlit as st
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptAvailable, NoTranscriptFound
from googleapiclient.errors import HttpError
from googletrans import Translator
import re



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
    
</style>
""", unsafe_allow_html=True)





# Load API key from Streamlit secrets and initialize YouTube API client
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
    st.header("YouTube Caption Search by Link")
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


# Streamlit app
# Centered title
st.markdown("<h1 class='title'>한국어 YouTube Caption Search</h1>", unsafe_allow_html=True)
tab1= st.tabs(["Youtube Caption Search"])

with tab1[0]:
    # Main function to call the YouTube search tab
        youtube_search_by_link()













