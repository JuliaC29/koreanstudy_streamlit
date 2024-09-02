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
    
    return all_videos[:5]  # Return top 5 most viewed videos across all channels

# Function to get video details such as view count
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
tab1, tab2, tab3 = st.tabs(["Vocabulary", "Grammar", "Korean Conversation Table"])

with tab1:
    lesson = st.selectbox("Select a lesson", lesson_list)
    if lesson:
        link, lesson_code = get_lesson_link(lesson)
        if link and lesson_code:
            st.markdown("Click: " f"[{lesson_code}]({link})", unsafe_allow_html=True)
  
with tab2:
        youtube_search_tab()


# Tab 3: Korean Conversation Table
with tab3:
    # Custom CSS for styling
    st.markdown(
        """
        <style>
        /* Center the title */
        .title {
            text-align: center;
        }

        /* Increase the font size of the subheader content and add spacing */
        .subheader-content {
            font-size: 20px;
            text-align: justify;
            margin-bottom: 20px;
        }

        /* Add space between subheaders and their content */
        .stMarkdown h2 {
            margin-top: 30px;
        }

        /* Add space between content blocks */
        .content-block {
            margin-bottom: 30px;
        }

        /* Adjust this value to make the dots smaller or larger */
        .dot-icon {
            font-size: 10px;  
        }
    
        </style>
        """,
        unsafe_allow_html=True
    )

    # Title 
    st.markdown('<h1 class="title">Korean Conversation Table</h1>', unsafe_allow_html=True)


    # Introduction
    st.markdown("""
    <div class="subheader-content">
    Welcome to our Korean Conversation Table! Whether you're a beginner or advanced learner, 
    everyone is welcome to join and practice Korean in a relaxed and friendly environment. 
    Join us and improve your Korean skills while making new friends!
    </div>
    """, unsafe_allow_html=True)

    # Location, Time, and Dates
    st.subheader("📍 Location")
    location_url = "https://languagecommons.as.virginia.edu/spaces/language-commons"
    st.markdown(f'<div class="subheader-content"><a href="{location_url}">Language Commons, New Cabell Hall 298</a></div>', unsafe_allow_html=True)

    st.subheader("🕒 Time and Dates")
    dates = {
        "<span class='dot-icon'>🔵</span> September 23, 2024": "5:15 PM - 6:45 PM",
        "<span class='dot-icon'>🟢</span> October 8, 2024": "5:15 PM - 6:45 PM",
        "<span class='dot-icon'>🔴</span> October 29, 2024": "5:15 PM - 6:45 PM",
        "<span class='dot-icon'>🟡</span> November 14, 2024": "5:15 PM - 6:45 PM"
    }

    for date, time in dates.items():
        st.markdown(f'<div class="subheader-content"><strong>{date}:</strong> {time}</div>', unsafe_allow_html=True)


    # Information
    st.markdown("### 🎉 Join Us and Have Fun!")
    st.markdown("""
    <div class="subheader-content">
    Feel free to bring anything you want to practice, any questions, or books you have. 
    If not, don't worry—we'll prepare some fun and easy Korean books so you can read with your friends and help each other out!
    </div>
    """, unsafe_allow_html=True)

    # Contact Information (without exposing email)
    st.subheader("📧 Have Any Questions?")
    st.write("If you have any questions, feel free to reach out!")

    # Email button
    contact_url = "https://forms.gle/H3fNCb7whLJxpkbt5"
    st.markdown(f'<a href="{contact_url}" style="font-size:16px; padding:10px; background-color:#ffcc00; border-radius:5px; color:black; text-decoration:none;">Click Here to Email Us!</a>', unsafe_allow_html=True)



