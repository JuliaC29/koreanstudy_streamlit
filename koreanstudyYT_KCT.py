import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptAvailable, NoTranscriptFound
from googleapiclient.errors import HttpError
from googletrans import Translator
import re
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta


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

# Load CSV data for Quizlet
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

# Function to search for multiple occurrences of the query in the captions and provide full sentences
def search_caption_with_context(transcript, query):
    matches = []
    for i, entry in enumerate(transcript):
        if query.lower() in entry['text'].lower():
            # Collect the surrounding context to form a full sentence
            start = i
            end = min(len(transcript), i + 3)  # Include the next sentence if available
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



# Streamlit app setup with tabs for different sections
st.markdown("<h1 class='title'>한국어 단어와 문법</h1>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4, tab5= st.tabs(["Vocabulary", "Grammar", "Korean Conversation Table", "Books", "Reading Practice"])

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



with tab4:

    # Define the correct Google Sheets scopes

    SCOPE = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]


    # Load Google service account credentials from Streamlit secrets
    credentials_dict = st.secrets["google_service_account"]
    credentials = Credentials.from_service_account_info(credentials_dict, scopes=SCOPE)

    # Authorize the client
    client = gspread.authorize(credentials)


    # Google Sheet ID (get it from the URL of your Google Sheet)
    spreadsheet_id = '1uUZAt-s-P6fBza2sbwEuAn63I10bCZQbi5hHQuKZP30'
    sheet_name = 'F24'  # Update with your Google Sheet tab name

    # Open the Google Sheet
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

    # Read data from Google Sheets into a DataFrame
    data = sheet.get_all_records()
    reservation_data = pd.DataFrame(data)

    # Ensure the DataFrame has the correct columns if it's empty
    if reservation_data.empty:
        reservation_data = pd.DataFrame(columns=["Book", "Reserved By", "Day"])

    # Sample Streamlit UI for reservations
    # Center the text and change the font size
    st.markdown(
    """
    <h2 style="text-align: center; font-size: 28px;">
        Book Reservations
    </h2>
    """,
    unsafe_allow_html=True
)


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

    # Select a book from the list
    selected_book = st.selectbox("Select a book:", books)
    
    # Add the "Day" selection field
    selected_day = st.selectbox("Select a day:", ["9/23/M", "10/8/T", "11/14/TH"])
    
    reserver_name = st.text_input("Enter your name:")

    # Reserve button
    if st.button("Reserve"):
        if reserver_name:
            # Add the new reservation to the DataFrame
            new_reservation = pd.DataFrame({"Book": [selected_book], "Reserved By": [reserver_name], "Day": [selected_day]})
            reservation_data = pd.concat([reservation_data, new_reservation], ignore_index=True)
            
            # Update Google Sheet with new data
            sheet.update([reservation_data.columns.values.tolist()] + reservation_data.values.tolist())
            st.success(f"Reserved {selected_book} for {reserver_name}")
        else:
            st.error("Please enter your name")

    # Display current reservations
    st.write("Current Reservations:")
    st.dataframe(reservation_data)


with tab5:
    # Define the correct Google Sheets scopes

    SCOPE = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]


    # Load Google service account credentials from Streamlit secrets
    credentials_dict = st.secrets["google_service_account"]
    credentials = Credentials.from_service_account_info(credentials_dict, scopes=SCOPE)

    # Authorize the client
    client = gspread.authorize(credentials)


    # Google Sheet ID (get it from the URL of your Google Sheet)
    spreadsheet_id = '13j_GerwKV2uQWiYHPqMobWI1dHspOkMUcd-6_R8cIPY'
    sheet_name = 'F24'  # Update with your Google Sheet tab name

    # Access the Google Sheet
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

    # Read data from Google Sheets into a DataFrame
    data = sheet.get_all_records()
    reservation_data = pd.DataFrame(data)

    # Ensure the DataFrame has the correct columns if it's empty
    if reservation_data.empty:
        reservation_data = pd.DataFrame(columns=["Name", "Email", "Course", "Role", "Date", "Start Time", "End Time"])

   
    # Center the text and change the font size
    st.markdown(
    """
    <h2 style="text-align: center; font-size: 28px;">
        Submit Your Availability
    </h2>
    """,
    unsafe_allow_html=True
    )

    # Collect form input
    name = st.text_input("Name")
    email = st.text_input("Email")

    # Role selection
    role = st.selectbox("Are you a student or a native speaker?", ["Student", "Native Speaker"])

    # Only show the course dropdown for students
    if role == "Student":
        course = st.selectbox("Select your course:", ["KOR1010", "KOR1060", "KOR2010", "KOR3010"])
    else:
        course = "NA"  # No course needed for native speakers

    available_date = st.date_input("Select available date")
    start_time = st.time_input("Select start time")
    end_time = st.time_input("Select end time")

    # Convert times to strings
    available_date_str = available_date.strftime('%Y-%m-%d')
    start_time_str = start_time.strftime('%H:%M')
    end_time_str = end_time.strftime('%H:%M')

    # Submit availability button
    if st.button("Submit Availability"):
        if name and email:
            # Add the new reservation to the DataFrame
            new_reservation = pd.DataFrame({
                "Name": [name], 
                "Email": [email], 
                "Course": [course],
                "Role": [role], 
                "Date": [available_date_str],  
                "Start Time": [start_time_str], 
                "End Time": [end_time_str]
            })
            reservation_data = pd.concat([reservation_data, new_reservation], ignore_index=True)
            
            # Update Google Sheet with new data
            sheet.update([reservation_data.columns.values.tolist()] + reservation_data.values.tolist())
            
            st.success(f"Availability submitted for {name}!")
        else:
            st.error("Please enter your name and email.")



    # Overlap checking logic with time handling
    def check_overlap(student_start, student_end, speaker_start, speaker_end):
        student_start_dt = datetime.combine(datetime.today(), student_start)
        student_end_dt = datetime.combine(datetime.today(), student_end)
        speaker_start_dt = datetime.combine(datetime.today(), speaker_start)
        speaker_end_dt = datetime.combine(datetime.today(), speaker_end)

        # Handle cases where end time is past midnight
        if student_end_dt < student_start_dt:
            student_end_dt += timedelta(days=1)
        if speaker_end_dt < speaker_start_dt:
            speaker_end_dt += timedelta(days=1)

        return max(student_start_dt, speaker_start_dt) < min(student_end_dt, speaker_end_dt)

    # Check for overlaps between students and native speakers
    students = reservation_data[reservation_data["Role"] == "Student"]
    speakers = reservation_data[reservation_data["Role"] == "Native Speaker"]

    found_overlap = False
    for _, student in students.iterrows():
        student_start = datetime.strptime(student["Start Time"], '%H:%M').time()
        student_end = datetime.strptime(student["End Time"], '%H:%M').time()
        student_date = student["Date"]

        for _, speaker in speakers.iterrows():
            speaker_start = datetime.strptime(speaker["Start Time"], '%H:%M').time()
            speaker_end = datetime.strptime(speaker["End Time"], '%H:%M').time()
            speaker_date = speaker["Date"]

            if student_date == speaker_date and check_overlap(student_start, student_end, speaker_start, speaker_end):
                st.success(f"Overlap found on {student_date} from {student['Start Time']} to {student['End Time']}")
                found_overlap = True

    if not found_overlap:
        st.error("No overlapping availabilities found.")

    # Display current availability in a grid format
    # Center the text and change the font size
    st.markdown(
    """
    <h2 style="text-align: center; font-size: 28px;">
        View Availability
    </h2>
    """,
    unsafe_allow_html=True
    )

    if not reservation_data.empty:
        # Sort the data by Date and then by Start Time
        reservation_data = reservation_data.sort_values(by=['Date', 'Start Time'])

        # Display the availability grid with color coding
        for _, row in reservation_data.iterrows():
            color = "#ADD8E6" if row["Role"] == "Student" else "#90EE90"  # Light blue for students, green for native speakers
            st.markdown(f"""
            <div style='background-color:{color}; padding: 10px; margin: 5px; border-radius: 5px;'>
            <strong>{row['Role']} ({row['Course']})</strong>  <br> {row['Date']} <strong>Time {row['Start Time']}-{row['End Time']}</strong>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.write("No availability submitted yet.")