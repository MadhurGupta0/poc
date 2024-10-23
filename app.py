import streamlit as st
import time
import os
from moviepy.editor import VideoFileClip
import asyncio
from efv import process_video

def get_or_create_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

# Function to handle async processing within Streamlit's context
def run_async_processing(input_video_path, output_video_path):
    loop = get_or_create_event_loop()
    result = loop.run_until_complete(process_video(input_video_path, output_video_path))
    return result

# Title of the app
st.title('Video Processing App')

# Upload the video
uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "mov", "avi", "mkv"])

# Process the video if uploaded
if uploaded_file is not None:
    # Save the uploaded video
    input_video_path = os.path.join("temp_input_video.mp4")
    with open(input_video_path, "wb") as f:
        f.write(uploaded_file.read())

    # Display the uploaded video
    st.video(input_video_path)
    output_video_path = "temp_output_video.mp4"
    # Notify user that processing has started
    st.write("Processing the video... Please wait!")
    if st.button('Start Processing'):
        with st.spinner('Processing...'):
            asyncio.run(process_video(input_video_path, output_video_path))

    time.sleep(5)

    st.video(output_video_path)

    # Optionally, provide a download link for the processed video
    with open(output_video_path, "rb") as file:
        btn = st.download_button(label="Download Processed Video", data=file, file_name="processed_video.mp4",
                                 mime="video/mp4")

