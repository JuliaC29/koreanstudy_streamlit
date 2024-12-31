import streamlit as st


st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic&display=swap');
    </style>
    
    <h1 style='text-align: center; font-size: 34px; margin-bottom: 20px; font-family: "Nanum Gothic", sans-serif; color: #0066ff;'>
        새해 복 많이 받으세요!🐍
    </h1>
    <div style='text-align: center; font-size: 22px; margin-bottom: 20px; font-family: "Nanum Gothic", sans-serif; '>
        2025년 새해에도 늘 건강하시고 뜻하시는 모든 일 이루시길 바랍니다.
    </div>
    """, 
    unsafe_allow_html=True
)


# List of video links with timestamps
videos = [ 
    {"link": "b3E4UoGNz8c?si=082lR3gMj6SOuq0t", "start": 1229, "end": 1232},
    {"link": "JdU-QezqYTM?si=UTjaMVF8TSNrs59J", "start": 1591, "end": 1594},  
    
]


    
# for video in videos:

#     st.markdown(f'''
#         <iframe 
#             width="700" 
#             height="400" 
#             src="https://www.youtube.com/embed/{video['link']}&start={video['start']}&end={video['end']}&autoplay=0" 
#             frameborder="0" 
#             allowfullscreen
#         >
#         </iframe>
#     ''', unsafe_allow_html=True)

    

for video in videos:
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
                src="https://www.youtube.com/embed/{video['link']}?start={video['start']}&end={video['end']}&autoplay=0" 
                frameborder="0" 
                allowfullscreen>
            </iframe>
        </div>
    """, unsafe_allow_html=True)


















    












