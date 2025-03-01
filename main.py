# main.py
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
from config import TELEGRAM_BOT_TOKEN

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Halo! Kirimkan link video TikTok dan saya akan mendownload video tanpa watermark untukmu.")

def download_video_no_watermark(tiktok_url: str):
    """
    Fungsi untuk mendownload video tanpa watermark.
    Menggunakan API gratis dari Tikwm untuk mendapatkan link video tanpa watermark.
    """
    api_url = f"https://tikwm.com/api/?url={tiktok_url}"
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Pastikan API merespon dengan benar, misalnya dengan kode 0
            if data.get("code") == 0:
                video_url = data.get("data", {}).get("nowatermark")
                if video_url:
                    video_response = requests.get(video_url, stream=True, timeout=20)
                    if video_response.status_code == 200:
                        return video_response.content
        return None
    except Exception as e:
        print("Error saat mendownload video:", e)
        return None

def handle_message(update: Update, context: CallbackContext):
    message_text = update.message.text
    # Cek apakah pesan mengandung kata "tiktok"
    if "tiktok" in message_text.lower():
        update.message.reply_text("Sedang mendownload video, tunggu sebentar...")
        video_bytes = download_video_no_watermark(message_text)
        if video_bytes:
            update.message.reply_video(video=video_bytes, caption="Berikut video TikTok tanpa watermark.")
        else:
            update.message.reply_text("Maaf, terjadi kesalahan saat mendownload video. Pastikan link valid dan coba lagi.")
    else:
        update.message.reply_text("Silakan kirim link video TikTok untuk mendownload video.")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("Bot sedang berjalan...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
