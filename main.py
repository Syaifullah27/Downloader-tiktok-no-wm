import requests
import datetime
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from config import TELEGRAM_BOT_TOKEN, RAPIDAPI_KEY

# Konfigurasi RapidAPI
RAPIDAPI_HOST = "tiktok-video-no-watermark2.p.rapidapi.com"
API_URL = "https://tiktok-video-no-watermark2.p.rapidapi.com/"

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Halo! Kirimkan link video TikTok dan saya akan mengirim video tanpa watermark, sound, dan nama user-nya."
    )

def download_file(url: str) -> bytes:
    """Mengunduh file (video atau audio) dari URL yang diberikan."""
    try:
        response = requests.get(url, stream=True, timeout=20)
        response.raise_for_status()
        content = response.content
        print(f"Downloaded file from {url}, size: {len(content)} bytes")
        return content
    except Exception as e:
        print("Error saat mendownload file:", e)
        return None

def get_video_info_rapidapi(tiktok_url: str) -> (dict, dict):
    """
    Menghubungi API RapidAPI untuk mengambil data video TikTok tanpa watermark.
    Selain data video, fungsi ini juga mengekstrak informasi penggunaan (rate limit) dari header respons.
    
    Returns:
      tuple: (data JSON, usage_info dictionary)
    """
    querystring = {"url": tiktok_url, "hd": "1"}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    try:
        response = requests.get(API_URL, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Log response API ke terminal jika berhasil
        print("Response API:", data)
        
        remaining = response.headers.get("x-ratelimit-remaining")
        limit = response.headers.get("x-ratelimit-limit")
        reset = response.headers.get("x-ratelimit-reset")
        usage_info = {"limit": limit, "remaining": remaining, "reset": reset}
        return data, usage_info
    except Exception as e:
        print("Error saat menghubungi API RapidAPI:", e)
        return None, None

def format_usage_info(usage_info: dict) -> str:
    """
    Mengonversi informasi penggunaan API ke format string yang mudah dibaca.
    Jika 'reset' berupa UNIX timestamp, akan dikonversi ke waktu lokal.
    """
    if not usage_info:
        return ""
    
    limit = usage_info.get("limit", "N/A")
    remaining = usage_info.get("remaining", "N/A")
    reset_raw = usage_info.get("reset", "N/A")
    
    try:
        reset_time = datetime.datetime.fromtimestamp(int(reset_raw)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        reset_time = reset_raw

    return f"\n*Usage Remaining*: {remaining}/{limit}\n*Resets at*: {reset_time}"

def handle_message(update: Update, context: CallbackContext):
    message_text = update.message.text
    if "tiktok" in message_text.lower():
        update.message.reply_text("Mengambil data dari API RapidAPI, tunggu sebentar...")
        data, usage_info = get_video_info_rapidapi(message_text)
        if data:
            if data.get("code") == 0:
                video_data = data.get("data", {})
                title = video_data.get("title", "Tanpa Judul")
                hdplay_url = video_data.get("hdplay")
                music_url = video_data.get("music")
                author = video_data.get("author", {})
                username = author.get("nickname", "Unknown")
                
                # Download file video dan audio
                video_bytes = download_file(hdplay_url) if hdplay_url else None
                audio_bytes = download_file(music_url) if music_url else None
                
                # Buat caption dengan judul dan nama user
                caption = f"*{title}*\nUser: {username}"
                
                if video_bytes:
                    video_file = InputFile(BytesIO(video_bytes), filename="video.mp4")
                    update.message.reply_video(video=video_file, caption=caption, parse_mode='Markdown')
                else:
                    update.message.reply_text("Gagal mendownload video dari URL.")
                
                if audio_bytes:
                    audio_file = InputFile(BytesIO(audio_bytes), filename="audio.mp3")
                    update.message.reply_audio(audio=audio_file)
                else:
                    update.message.reply_text("Gagal mendownload sound dari video.")
                
                # Opsional: tampilkan info penggunaan API
                usage_text = format_usage_info(usage_info)
                if usage_text:
                    update.message.reply_text("Info API:" + usage_text, parse_mode='Markdown')
            else:
                update.message.reply_text("API mengembalikan error:\n" + str(data))
        else:
            update.message.reply_text("Terjadi kesalahan saat menghubungi API RapidAPI.")
    else:
        update.message.reply_text("Silakan kirim link video TikTok untuk mengambil data.")

def check_limit(update: Update, context: CallbackContext):
    dummy_url = "https://vt.tiktok.com/ZSM5ULmYT/"
    _, usage_info = get_video_info_rapidapi(dummy_url)
    if usage_info:
        info_text = format_usage_info(usage_info)
        update.message.reply_text("Informasi penggunaan API:\n" + info_text, parse_mode='Markdown')
    else:
        update.message.reply_text("Gagal mengambil informasi penggunaan API.")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("limit", check_limit))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("Bot berjalan...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
