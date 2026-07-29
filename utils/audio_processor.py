import yt_dlp
from pydub import AudioSegment
import os
import shutil
import platform

DOWNLOAD_DIR = 'downloades'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Auto-detect ffmpeg location
_FFMPEG_PATH = shutil.which("ffmpeg")
if not _FFMPEG_PATH and platform.system() == "Windows":
    # Fallback to known winget install path (Windows only)
    _winget_ffmpeg = os.path.expanduser(
        r"~\AppData\Local\Microsoft\WinGet\Packages"
        r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
        r"\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
    )
    if os.path.isfile(_winget_ffmpeg):
        _FFMPEG_PATH = os.path.dirname(_winget_ffmpeg)

# Configure pydub to use the detected ffmpeg
if _FFMPEG_PATH and platform.system() == "Windows":
    _ext = ".exe"
    _ffmpeg_exe = os.path.join(_FFMPEG_PATH, f"ffmpeg{_ext}") if os.path.isdir(_FFMPEG_PATH) else _FFMPEG_PATH
    _ffprobe_exe = os.path.join(_FFMPEG_PATH, f"ffprobe{_ext}") if os.path.isdir(_FFMPEG_PATH) else _FFMPEG_PATH.replace("ffmpeg", "ffprobe")
    if os.path.isfile(_ffmpeg_exe):
        AudioSegment.converter = _ffmpeg_exe
    if os.path.isfile(_ffprobe_exe):
        AudioSegment.ffprobe = _ffprobe_exe

def download_youtube_audio(url :str) ->str:
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }
    if _FFMPEG_PATH:
        ydl_opts["ffmpeg_location"] = _FFMPEG_PATH
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace(".webm", ".wav").replace(".m4a", ".wav")
    return filename



def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000) #16khz
    audio.export(output_path, format="wav")
    return output_path



def chunk_audio(wav_path : str , chunk_minutes : int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000 

    chunks = []

    for i, start in enumerate(range(0,len(audio),chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path , format = "wav")

        chunks.append(chunk_path)
    
    return chunks

def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks


