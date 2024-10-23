from moviepy.audio.io.AudioFileClip import AudioFileClip
from pydub import AudioSegment
from moviepy.editor import VideoFileClip,vfx
import assemblyai as aai
import requests
import asyncio
import edge_tts
duration = [0]
def extract_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    duration[0] = video.duration
    audio.write_audiofile(audio_path)
    return audio_path

def transcribe_audio(audio_path):

    aai.settings.api_key = "13068adb0969434a96da7e85627f31f3"
    FILE_URL = audio_path
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(FILE_URL)
    if transcript.status == aai.TranscriptStatus.error:
        print(transcript.error)

    return transcript.text

def correct_transcription(transcription):

    azure_openai_key = '22ec84421ec24230a3638d1b51e3a7dc'
    azure_openai_endpoint=" https://internshala.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": azure_openai_key
    }
    max_duration_seconds = duration[0]
    data = {
        "messages": [{"role": "user",
                     "content": f"Please correct the following transcription for grammatical errors, "
                f"remove filler words (like 'um' and 'ah'), but keep the length of the corrected "
                f"text as close as possible to the original. The final corrected text should match "
                f"the original length and must fit within {max_duration_seconds} seconds when spoken.\n\n"
                f"The length of the corrected transcription (in number of characters or words) should "
                f"be almost the same as the original transcription.\n\n"
                f"Transcription: {transcription}\n\n"
                f"Return only the corrected transcription without changing its meaning, "
                f"and make sure it matches the original length closely."}],
        "max_tokens": 100
    }

    response = requests.post(azure_openai_endpoint, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()

        return result["choices"][0]["message"]["content"].strip()
    else:
        print(f"Failed to connect or retrieve response: {response.status_code} - {response.text}")
    corrected_transcription = response['choices'][0]['message']['content']
    return corrected_transcription

async def text_to_speech(text, output_audio_path):
    video = VideoFileClip("input_video.mp4")
    estimated_duration = len(text.split()) / 150 * 60
    print((video.duration / estimated_duration), estimated_duration, video.duration)
    n = video.duration // 60
    extra = ((video.duration - estimated_duration) / n) if n != 0 else (video.duration - estimated_duration)
    print(extra, "dshf")
    rate = "+0%"
    if extra > 0 and extra <= 5:
        rate = "-10%"
    elif extra > 5 and extra <= 10:
        rate = "-20%"
    elif extra > 10 and extra <= 20:
        rate = "-40%"
    elif extra > 20 and extra <= 30:
        rate = "-50%"
    elif extra > 30 and extra <= 40:
        silence = AudioSegment.silent(duration=3000)
        communicate = edge_tts.Communicate(text, "en-CA-ClaraNeural", rate="-50%")
        await communicate.save(output_audio_path)
        audio = silence + AudioSegment.from_file(output_audio_path) + silence
        audio.export(output_audio_path, format="wav")
        return
    elif estimated_duration * 2.5 < video.duration:
        silence = AudioSegment.silent(duration=1000 * (video.duration / estimated_duration))
        audio = silence
        if text.endswith("."):
            text = text[:-1]
        text = text.split(".")

        for i in text:

            await edge_tts.Communicate(i, "en-CA-ClaraNeural", rate="-50%").save("temp.wav")
            audio += silence + AudioSegment.from_file("temp.wav")

        audio += silence
        audio.export(output_audio_path, format="wav")
        return
    else:
        rate = "+0%"
    communicate = edge_tts.Communicate(text, "en-CA-ClaraNeural", rate=rate)
    await communicate.save(output_audio_path)

async def text_to_speech2(text, output_audio_path):
    video = VideoFileClip("input_video.mp4")
    estimated_duration = len(text.split()) / 150 * 60
    print((video.duration / estimated_duration), estimated_duration, video.duration)
    n = video.duration // 60
    extra = ((  estimated_duration-video.duration) / n) if n != 0 else (video.duration - estimated_duration)
    print(extra, "dshf")
    rate = "+0%"
    if extra > 0 and extra <= 5:
        rate = "+10%"
    elif extra > 5 and extra <= 10:
        rate = "+20%"
    elif extra > 10 and extra <= 20:
        rate = "+40%"
    elif extra > 20 and extra <= 30:
        rate = "+50%"
    elif extra > 30 and extra <= 40:
        rate="+60%"
    elif extra > 40 and extra <= 50:
        rate = "+70%"
    else:
        rate = "+80%"

    await edge_tts.Communicate(text, "en-CA-ClaraNeural", rate=rate).save(output_audio_path)

def adjust_audio_speed(audio_clip, target_duration):
        original_duration = audio_clip.duration
        speed_factor = original_duration / target_duration
        return audio_clip.fx(vfx.speedx, speed_factor)

def replace_audio_in_video(video_path, new_audio_path, output_video_path):
        video = VideoFileClip(video_path)
        new_audio = AudioFileClip(new_audio_path)

        video_duration = video.duration
        audio_duration = new_audio.duration

        n=video.duration/60
        print(n)



        if audio_duration > video_duration:
            new_audio = new_audio.set_duration(video.duration)
            final_video = video.set_audio(new_audio)
        else:
            final_video = video.set_audio(new_audio)

        final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

async def process_video(video_path, output_video_path):
    audio_path = "temp_audio.wav"
    corrected_audio_path = "corrected_audio.wav"
    extract_audio(video_path, audio_path)


    transcription = transcribe_audio(audio_path)
    print("Transcription:", transcription)


    corrected_transcription = correct_transcription(transcription)
    print("Corrected Transcription:", corrected_transcription)
    speech_time=len(corrected_transcription.split())/150.0*60
    if speech_time<=duration[0]:
     await text_to_speech(corrected_transcription, corrected_audio_path)
    else:
        await text_to_speech2(corrected_transcription, corrected_audio_path)
    voice = AudioFileClip(corrected_audio_path)
    print("done saving", voice.duration,duration[0])

    replace_audio_in_video(video_path, corrected_audio_path, output_video_path)

    return output_video_path

# Example usage

