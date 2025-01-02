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


# List of video links with timestamps
videos = [ 
    {"link": "JdU-QezqYTM?si=9kag9GDJBWl4gjTu", "start": 3337, "end": 3350},
    {"link": "b3E4UoGNz8c?si=082lR3gMj6SOuq0t", "start": 1229, "end": 1232},
    {"link": "EnnrVnbVK2A?si=BqFHNa7mG-WVsjoA", "start": 43, "end": 62}, 
 
    
]
    

for video in videos:
    video_id = video['link']
    # Add replay button
    if st.button("🔄 Replay", key=f"replay_{video_id}"):
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


















    












