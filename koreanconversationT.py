import streamlit as st
import pandas as pd
import datetime
import os


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

# Define file path for reservations CSV in the 'data' folder
csv_file_path = os.path.join("data", "reservations.csv")

# Check if the CSV file exists, if not create an empty DataFrame
if os.path.exists(csv_file_path):
    reservation_data = pd.read_csv(csv_file_path)
else:
    reservation_data = pd.DataFrame(columns=["Book", "Reserved By", "Day"])

# Your existing code for working with the CSV file...
# Ensure when saving the file, it's saved in the same location:
reservation_data.to_csv(csv_file_path, index=False)


# Title 
st.markdown('<h1 class="title">Korean Conversation Table</h1>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Schedule", "Books"])

with tab1:


    # Introduction
    st.markdown("""<div class="header">Fall 2024</div>""", unsafe_allow_html=True)
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

with tab2:


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

    # Display the list of books and reservation form
    #st.title("Korean Conversation Table - Book Reservations")

    #st.write("**Choose a book to reserve and enter your name:**")
    

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
