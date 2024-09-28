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

# Function to search for multiple occurrences of the query in the captions and provide full sentences
def search_caption_with_context(transcript, query):
    matches = []
    for i, entry in enumerate(transcript):
        if query.lower() in entry['text'].lower():
            # Collect the surrounding context to form a full sentence
            start = max(0, i - 1)  # Include the previous sentence if available
            end = min(len(transcript), i + 1)  # Include the next sentence if available
            context = transcript[start:end]
            full_sentence = ' '.join([item['text'] for item in context])
            start_time = context[0]['start']
            matches.append((start_time, full_sentence))
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

# Function to display video segments with multiple timestamps using HTML iframe
def display_video_segments(video_id, matches):
    for start_time, text in matches:
        formatted_time = format_time(start_time)
        english_translation = translate_text(text)
        st.write(f"**[{formatted_time}]** {text}")
        st.write(f"Translation: {english_translation}")
        
        # Embed the video using the HTML iframe method starting at the matched timestamp
        embed_youtube_video(video_id, int(start_time))

# Function to format time from seconds to HH:MM:SS
def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# Main function to call the YouTube search tab
def youtube_search_tab():
    st.header("YouTube Caption Search")
    youtube_link = st.text_input("Enter YouTube link:")
    search_term = st.text_input("Enter a Korean grammar point or phrase:")

    if st.button("Search"):
        if not youtube:
            st.error("YouTube API client is not initialized.")
            return

        if youtube_link and search_term:
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


# Streamlit app
# Centered title
st.markdown("<h1 class='title'>한국어 YouTube Caption Search</h1>", unsafe_allow_html=True)
tab1= st.tabs(["Youtube Caption Search"])

with tab1[0]:
    # Main function to call the YouTube search tab
        youtube_search_tab()













