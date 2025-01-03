import streamlit as st


st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic&display=swap');
    </style>
    
    <h1 style='text-align: center; font-size: 34px; margin-bottom: 0.01px; font-family: "Nanum Gothic", sans-serif; color: #0066ff;'>
    새해 복 많이 받으세요!<span style='font-size: 20px;'>🐍</span>
    </h1>
       
    <div style='text-align: center; font-size: 22px; margin-bottom: 50px; font-family: "Nanum Gothic", sans-serif; '>
    2025년 새해에도 늘 건강하시고 뜻하시는 모든 일 이루시길 바랍니다.
    </div>
            
    <div style='text-align: center; font-size: 16px; margin-bottom: 20px; font-family: "Nanum Gothic", sans-serif; '>
    ⬇️ 새해 축하 영상 보기 ⬇️
    </div>
    """, 
    unsafe_allow_html=True
)


# Function to format time
def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"





# List of video links with timestamps
videos = [ 
    {"link": "JdU-QezqYTM?si=9kag9GDJBWl4gjTu", 
     "start": 3337, 
     "end": 3350,
     'korean_text': '새해 복 많이 받으세요. 이런 걸 정했었어야 되는데. 큰 절 한 번 드려야지. 말이라도 하고',
     'english_text': 'Happy New Year. We should have decided on this kind of thing. We should bow deeply at least once. You could at least say something'
    },
    {"link": "b3E4UoGNz8c?si=082lR3gMj6SOuq0t", 
     "start": 1229, 
     "end": 1232,
     'korean_text': '새해 복 많이 받으세요. 감사합니다.',
     'english_text': 'Happy New Year. Thank you.'
     },
    {"link": "EnnrVnbVK2A?si=BqFHNa7mG-WVsjoA", 
     "start": 43, 
     "end": 62,
     'korean_text': '올해는 푸른 뱀의 해인데요, 을사년에는 소망하시는 바를 전부 이루시는 한 해가 되길 바라겠습니다. 올해는 더 큰 꿈을 가지고 행복을 찾으면서 여러분들 하시는 일 다 잘 되시길 진심으로 바라겠습니다. 새해 복 많이 받으세요.',
     'english_text': 'This year is the year of the green snake, and in the year of Eulsa, I hope you will achieve all that you wish for. I sincerely hope that this year, you will have bigger dreams, find happiness, and succeed in everything you do. Happy New Year.'
     }, 
    #{"link": "l1vnWPpGEVU?si=aAS-iwWRb4E3PT88", "start": 300, "end": 305}, 
    #{"link": "JdU-QezqYTM?si=UTjaMVF8TSNrs59J", "start": 1591, "end": 1594}, 
     
    
]
    

# for video in videos:
#     video_id = video['link']
#     # Add replay button
#     if st.button("🔄 Replay", key=f"replay_{video_id}"):
#         video_url = f"https://www.youtube.com/embed/{video_id}&start={video['start']}&end={video['end']}&autoplay=1"
#     else:
#         video_url = f"https://www.youtube.com/embed/{video_id}&start={video['start']}&end={video['end']}&autoplay=0"


#     st.markdown(f"""
#         <style>
#         .video-container {{
#             position: relative;
#             width: 100%;
#             padding-bottom: 56.25%;
#             margin-bottom: 20px;
#         }}
#         .video-container iframe {{
#             position: absolute;
#             top: 0;
#             left: 0;
#             width: 100%;
#             height: 100%;
#         }}
#         </style>
#         <div class="video-container">
#             <iframe 
#                 src="{video_url}" 
#                 frameborder="0" 
#                 allowfullscreen>
#             </iframe>
#         </div>
#     """, unsafe_allow_html=True)

#     formatted_time = format_time(video['start'])
#     st.write(formatted_time)

#     # Show/Hide text buttons
#     if st.button("Show Korean", key=f"kor_{video['link']}"):
#         st.write(f"**Korean:** {video['korean_text']}")
#     if st.button("Show English", key=f"eng_{video['link']}"):
#         st.write(f"**English:** {video['english_text']}")



for video in videos:
    video_id = video['link']
    
    # Create two columns for timestamp and replay button
    col1, col2 = st.columns([0.3, 1.7])  # Adjust ratio as needed
    with col2:
        formatted_time = format_time(video['start'])
        st.write(formatted_time)
    with col1:
        replay = st.button("🔄 Replay", key=f"replay_{video_id}")
    
    # Set video URL based on replay button
    if replay:
        video_url = f"https://www.youtube.com/embed/{video_id}&start={video['start']}&end={video['end']}&autoplay=1"
    else:
        video_url = f"https://www.youtube.com/embed/{video_id}&start={video['start']}&end={video['end']}&autoplay=0"

    st.markdown(f"""
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
    """, unsafe_allow_html=True)

   # Show/Hide text buttons
    if st.button("Show Korean", key=f"kor_{video['link']}"):
        st.write(f"**Korean:** {video['korean_text']}")
    if st.button("Show English", key=f"eng_{video['link']}"):
        st.write(f"**English:** {video['english_text']}")














    












