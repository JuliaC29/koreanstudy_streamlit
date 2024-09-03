import streamlit as st
import datetime


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
    "<span class='dot-icon'>🔴</span> October 29 (T), K-Move Night": "5:15 PM - 6:45 PM",
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

