import streamlit as st
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptAvailable, NoTranscriptFound
from datetime import datetime

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state
if 'available_transcripts' not in st.session_state:
    st.session_state.available_transcripts = []
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = []
if 'current_video_id' not in st.session_state:
    st.session_state.current_video_id = ""

st.markdown("""
<style>
    .title {
        text-align: center;
    }
    .youtube-link {
        color: #FF0000;
        text-decoration: none;
        font-weight: bold;
    }
    .youtube-link:hover {
        text-decoration: underline;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #155724 !important;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #0c5460 !important;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #856404 !important;
    }
    
    @media (prefers-color-scheme: dark) {
        .info-box {
            background-color: #1a4851 !important;
            border: 1px solid #3c7a89 !important;
            color: #b8e6f0 !important;
        }
        .warning-box {
            background-color: #4a3f1a !important;
            border: 1px solid #8a7635 !important;
            color: #f5e79e !important;
        }
        .success-box {
            background-color: #1a3d1a !important;
            border: 1px solid #4a7c59 !important;
            color: #b8e6c1 !important;
        }
    }
    
    .info-box *, .warning-box *, .success-box * {
        color: inherit !important;
    }
    
    .stTextInput > div > div > input {
        border-color: #ced4da !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #80bdff !important;
        box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25) !important;
    }
    .stTextInput > div > div > input:hover {
        border-color: #80bdff !important;
    }
</style>""", unsafe_allow_html=True)

# Utility functions
def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    try:
        if 'v=' in url:
            return url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            return url.split('youtu.be/')[1].split('?')[0]
        return url
    except:
        return url

def format_time(seconds):
    """Format time from seconds to HH:MM:SS"""
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# Function to extract transcript (any language, no translation)
def extract_transcript(video_id, selected_transcripts):
    """Extract transcript in original language - no translation"""
    
    transcript_data = []
    
    try:
        for selected_index in selected_transcripts:
            selected = st.session_state.available_transcripts[selected_index]
            
            st.info(f"📥 Extracting {selected['language_name']} transcript...")
            
            # Extract the selected transcript with retry logic
            transcript = None
            
            # Try multiple methods to fetch the transcript
            try:
                transcript = selected['transcript'].fetch()
            except Exception as e:
                if "no element found" in str(e).lower():
                    st.warning(f"⚠️ First attempt failed for {selected['language_name']}, trying alternative method...")
                    
                    # Method 2: Try translating to English first, then back (sometimes works)
                    try:
                        if selected['lang'] != 'en':
                            st.info("🔄 Trying to get transcript via English translation...")
                            translated = selected['transcript'].translate('en')
                            transcript = translated.fetch()
                            st.success("✅ Successfully extracted via English translation route")
                        else:
                            raise e
                    except Exception as e2:
                        st.error(f"❌ Could not extract {selected['language_name']} transcript: {str(e)}")
                        continue
            
            if not transcript:
                continue
            
            # Process the transcript
            for i, entry in enumerate(transcript):
                start_time = entry['start']
                duration = entry.get('duration', 0)
                end_time = start_time + duration
                text = entry['text'].strip()
                
                transcript_entry = {
                    'video_id': video_id,
                    'start_time_seconds': start_time,
                    'end_time_seconds': end_time,
                    'start_time': round(start_time, 1),
                    'end_time': round(end_time, 1),
                    'timestamp': format_time(start_time),
                    'end_timestamp': format_time(end_time),
                    'duration': round(duration, 1),
                    'text': text,
                    'youtube_link': f"https://www.youtube.com/watch?v={video_id}&t={int(start_time)}",
                    'language': selected['lang'],
                    'language_name': selected['language_name'],
                    'caption_type': 'Auto-generated' if selected['is_generated'] else 'Manual',
                    'segment_number': i + 1
                }
                transcript_data.append(transcript_entry)
        
        return transcript_data
        
    except Exception as e:
        st.error(f"❌ Error extracting transcript: {str(e)}")
        return []

# Function to save transcript to CSV with multiple format options
def save_transcript_options(transcript_data, video_title="Unknown"):
    """Provide multiple download options for transcript data"""
    if not transcript_data:
        st.warning("No transcript data to save.")
        return None
    
    st.markdown("### 📥 Download Options")

    
    # Create different format options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Full format with all columns
        df = pd.DataFrame(transcript_data)
        full_columns = [
            'video_id',
            'timestamp',
            'end_timestamp', 
            'start_time',
            'end_time',
            'duration',
            'text',
            'youtube_link',
            'language',
            'language_name',
            'caption_type',
            'segment_number'
        ]
        
        df_ordered = df.reindex(columns=[col for col in full_columns if col in df.columns])
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_title_clean = video_title.replace(' ', '_')[:50]
        
        # Include all languages in filename if multiple
        languages = list(set([item['language'] for item in transcript_data]))
        language_str = "_".join(languages) if len(languages) <= 3 else f"{len(languages)}languages"
        
        filename = f"full_transcript_{language_str}_{video_title_clean}_{timestamp}.csv"
        
        # Create download button for browser download
        csv_data = df_ordered.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📋 Download Full Details",
            data=csv_data.encode('utf-8-sig'),
            file_name=filename,
            mime="text/csv",
            key="download_full_csv",
            help="Complete transcript with all columns"
        )
    
    with col2:
        # Simple format - perfect for analysis
        simple_data = []
        for item in transcript_data:
            simple_data.append({
                'timestamp': item['timestamp'],
                'language': item['language_name'],
                'text': item['text'],
                'youtube_link': item['youtube_link'],
                'video_id': item['video_id']
            })
        
        df_simple = pd.DataFrame(simple_data)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_title_clean = video_title.replace(' ', '_')[:50]
        
        languages = list(set([item['language'] for item in transcript_data]))
        language_str = "_".join(languages) if len(languages) <= 3 else f"{len(languages)}languages"
        
        filename = f"simple_transcript_{language_str}_{video_title_clean}_{timestamp}.csv"
        
        # Create download button for browser download
        csv_data = df_simple.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="🎯 Download Simple Format",
            data=csv_data.encode('utf-8-sig'),
            file_name=filename,
            mime="text/csv",
            key="download_simple_csv",
            help="Basic format: timestamp, language, text, link"
        )
    
    with col3:
        # Timeline format - minimal for analysis
        timeline_data = []
        for item in transcript_data:
            timeline_data.append({
                'time': item['timestamp'],
                'language': item['language_name'],
                'text': item['text']
            })
        
        df_timeline = pd.DataFrame(timeline_data)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_title_clean = video_title.replace(' ', '_')[:50]
        
        languages = list(set([item['language'] for item in transcript_data]))
        language_str = "_".join(languages) if len(languages) <= 3 else f"{len(languages)}languages"
        
        filename = f"timeline_{language_str}_{video_title_clean}_{timestamp}.csv"
        
        # Create download button for browser download
        csv_data = df_timeline.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="⏱️ Download Timeline Only",
            data=csv_data.encode('utf-8-sig'),
            file_name=filename,
            mime="text/csv",
            key="download_timeline_csv",
            help="Just timestamps, language, and text"
        )

# Check available captions function
def check_available_captions(video_id):
    """Check what captions are available for a video"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        manual_captions = []
        auto_captions = []
        
        for transcript in transcript_list:
            caption_info = {
                'language': transcript.language,
                'language_code': transcript.language_code,
                'type': 'Auto-generated' if transcript.is_generated else 'Manual'
            }
            
            if transcript.is_generated:
                auto_captions.append(caption_info)
            else:
                manual_captions.append(caption_info)
        
        return manual_captions, auto_captions
    except Exception as e:
        return [], []

# Main Streamlit Interface
def main():
    st.markdown("<h3 class='title'>🎯 YouTube Transcript Extractor</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Extract transcripts with timestamps from YouTube videos (any language)</p>", unsafe_allow_html=True)

    
    # Add info about the tool
    st.markdown("""
    <div class="info-box">
    <strong>📖 What this tool does:</strong><br>
    • Extracts transcripts from YouTube videos in their <strong>original language</strong><br>
    • Downloads as CSV with timestamps for easy analysis<br>

    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="warning-box">
    <strong>📋 Requirements:</strong><br>
    • Video must have captions (manual or auto-generated)<br>
    • Captions must be publicly available (not disabled by uploader)<br>
    </div>
    """, unsafe_allow_html=True)
    
    # Video URL input
    video_url = st.text_input(
        "YouTube Video URL:",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Paste the full YouTube video URL here"
    )
    
    if video_url:
        video_id = extract_video_id(video_url)
        st.info(f"🆔 Video ID: {video_id}")
        
        # Reset session state if video changed
        if st.session_state.current_video_id != video_id:
            st.session_state.current_video_id = video_id
            st.session_state.available_transcripts = []
            st.session_state.extracted_data = []
        
        # Check captions button
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Check Available Captions", key="check_captions"):
                with st.spinner("Checking available captions..."):
                    manual_caps, auto_caps = check_available_captions(video_id)
                    
                    if manual_caps or auto_caps:
                        st.success("✅ Captions found!")
                        
                        # Store available transcripts in session state
                        try:
                            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                            st.session_state.available_transcripts = []
                            
                            for transcript_info in transcript_list:
                                st.session_state.available_transcripts.append({
                                    'lang': transcript_info.language_code,
                                    'language_name': transcript_info.language,
                                    'is_generated': transcript_info.is_generated,
                                    'transcript': transcript_info
                                })
                        except Exception as e:
                            st.error(f"Error getting transcript details: {str(e)}")
                        
                        if manual_caps:
                            st.markdown("**Manual Captions:**")
                            for cap in manual_caps:
                                st.write(f"- {cap['language']} ({cap['language_code']})")
                        
                        if auto_caps:
                            st.markdown("**Auto-generated Captions:**")
                            for cap in auto_caps:
                                st.write(f"- {cap['language']} ({cap['language_code']})")
                        
                        st.info("💡 Manual captions are usually more accurate than auto-generated ones.")
                    else:
                        st.error("❌ No captions found for this video")
        
        # Show transcript selection if captions are available
        if st.session_state.available_transcripts:
            st.markdown("---")
            st.markdown("### 📋 Select Transcripts to Extract")
            
            # Create options for multiselect
            transcript_options = []
            for i, trans in enumerate(st.session_state.available_transcripts):
                type_str = "Auto-generated" if trans['is_generated'] else "Manual"
                option = f"{trans['language_name']} ({trans['lang']}) - {type_str}"
                transcript_options.append(option)
            
            # Multiple selection
            selected_options = st.multiselect(
                "Choose which transcript(s) to extract:",
                options=list(range(len(transcript_options))),
                format_func=lambda x: transcript_options[x],
                default=[0] if transcript_options else [],
                help="You can select multiple languages to extract at once"
            )
            
            if selected_options:
                st.info(f"📝 Selected {len(selected_options)} transcript(s) for extraction")
                
                with col2:
                    if st.button("📥 Extract Selected Transcripts", key="extract_transcript"):
                        if selected_options:
                            with st.spinner("Extracting transcript(s)..."):
                                transcript_data = extract_transcript(video_id, selected_options)
                            
                            if transcript_data:
                                st.session_state.extracted_data = transcript_data
                            else:
                                st.error("❌ Could not extract transcript from this video")
        
        # Show extracted data if available
        if st.session_state.extracted_data:
            st.markdown("---")
            
            # Show success info
            total_duration = max([entry['end_time_seconds'] for entry in st.session_state.extracted_data])
            
            # Group by language for display
            languages = list(set([entry['language_name'] for entry in st.session_state.extracted_data]))
            
            st.markdown(f"""
            <div class="success-box">
            <strong>✅ Successfully extracted {len(st.session_state.extracted_data)} transcript segments!</strong><br>
            Languages: {', '.join(languages)}<br>
            Duration: {format_time(total_duration)}
            </div>
            """, unsafe_allow_html=True)
            
            # Show preview
            st.markdown("**Preview (first 5 segments):**")
            preview_df = pd.DataFrame(st.session_state.extracted_data[:5])[['timestamp', 'language_name', 'text']]
            st.dataframe(preview_df, use_container_width=True)
            
            # Download options
            video_title = f"video_{video_id}"
            save_transcript_options(st.session_state.extracted_data, video_title)
    



if __name__ == "__main__":
    main()







 








