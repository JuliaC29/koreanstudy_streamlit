import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptAvailable, NoTranscriptFound
from googleapiclient.errors import HttpError
from googletrans import Translator
import re
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
tab1, tab2, tab3, tab4= st.tabs(["Vocabulary", "Grammar", "Korean Conversation Table", "Books"])

with tab1:
    lesson = st.selectbox("Select a lesson", lesson_list)
    if lesson:
        link, lesson_code = get_lesson_link(lesson)
        if link and lesson_code:
            st.markdown("Click: " f"[{lesson_code}]({link})", unsafe_allow_html=True)
  
with tab2:
        youtube_search_by_link()


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

    /* Center the header */
        .header {
            text-align: center;
            font-size: 22px
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
    st.markdown("""<div class="header">Fall 2024</div>""", unsafe_allow_html=True)

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
        "<span class='dot-icon'>🔵</span> September 23 (M)": "5:15 PM - 6:45 PM",
        "<span class='dot-icon'>🟢</span> October 8 (T)": "5:15 PM - 6:45 PM",
        "<span class='dot-icon'>🔴</span> October 29 (T), K-Movie Night": "5 PM - 7 PM",
        "<span class='dot-icon'>🟡</span> November 14 (TH)": "5:15 PM - 6:45 PM"
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


# Define file path for reservations CSV in the 'data' folder
csv_file_path = os.path.join("data", "reservations.csv")

# Check if the CSV file exists, if not create an empty DataFrame
if os.path.exists(csv_file_path):
    reservation_data = pd.read_csv(csv_file_path)
else:
    reservation_data = pd.DataFrame(columns=["Book", "Reserved By", "Day"])

# Ensure when saving the file, it's saved in the same location:
reservation_data.to_csv(csv_file_path, index=False)


with tab4:


    # Create a list of books
    books = [
       

        "호랑이와 곶감 – The Tiger and the Persimmon",
        "빨간 부채 파란 부채 – The Red Fan and the Blue Fan",
        "열두 띠 이야기 – The Story of the Twelve Zodiac Animals",
        "방귀 시합 – The Fart Contest",
        "단군 이야기 – The Story of Dangun",
        "재주 많은 오형제 – The Five Brothers with Many Talents",
        "무엇이든 될 수 있어 – You Can Be Anything",
        "모두의 장난감 – Everyone's Toy",
        "아빠의 마음 날씨 – The Weather of Dad's Heart",
        "함께하는 저녁 시간 – Shared Evening Time",
        "달라도 괜찮아 – It's Okay to Be Different"

    ]

    # Create three different conversation table days
    days = ["9/23/M", "10/8/T", "11/14/TH"]

    
    # Filepath for reservations CSV
    reservation_file = 'reservations.csv'

    # Load existing reservations from CSV if it exists
    if os.path.exists(reservation_file):
        reservation_data = pd.read_csv(reservation_file)
    else:
        # Create an empty DataFrame if the file does not exist
        reservation_data = pd.DataFrame(columns=["Book", "Reserved By", "Day"])

  
    # Select a book from the list
    selected_book = st.selectbox("Select a book", books)

    # Select a conversation day
    selected_day = st.selectbox("Select a day", days)

    # Enter the name of the person reserving the book
    reserver_name = st.text_input("Enter your name to reserve this book:")

    # Reserve button
    if st.button("Reserve"):
        # Check if the book is already reserved for the selected day
        existing_reservation = reservation_data[
            (reservation_data["Book"] == selected_book) &
            (reservation_data["Day"] == selected_day)
        ]
        
        if not existing_reservation.empty:
            st.error(f"Sorry, {selected_book} is already reserved for {selected_day}.")
        else:
            # Add the reservation to the DataFrame
            new_reservation = pd.DataFrame({
                "Book": [selected_book],
                "Reserved By": [reserver_name],
                "Day": [selected_day]
            })
            reservation_data = pd.concat([reservation_data, new_reservation], ignore_index=True)
            
            # Save the updated reservations to the CSV file
            reservation_data.to_csv(reservation_file, index=False)
            
            st.success(f"You have reserved {selected_book} for {selected_day}.")
 
    # Display the DataFrame (CSV file)
    if not reservation_data.empty:
        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
        st.dataframe(reservation_data)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.write("No books have been reserved yet.")
