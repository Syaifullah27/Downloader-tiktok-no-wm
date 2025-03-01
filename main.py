import requests
import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from config import TELEGRAM_BOT_TOKEN, RAPIDAPI_KEY

# Konfigurasi RapidAPI
RAPIDAPI_HOST = "tiktok-video-no-watermark2.p.rapidapi.com"
API_URL = "https://tiktok-video-no-watermark2.p.rapidapi.com/"

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Halo! Kirimkan link video TikTok dan saya akan mengambil data video tanpa watermark beserta informasi sisa penggunaan API."
    )

def get_video_info_rapidapi(tiktok_url: str) -> (dict, dict):
    """
    Menghubungi API RapidAPI untuk mengambil data video TikTok tanpa watermark.
    Selain data video, fungsi ini juga mengekstrak informasi penggunaan (rate limit) dari header respons.
    
    Returns:
      tuple: (data JSON, usage_info dictionary)
    """
    querystring = {"url": tiktok_url, "hd": "1"}  # 'hd' opsional untuk mendapatkan video HD
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    try:
        response = requests.get(API_URL, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()  # Pastikan status code 200
        data = response.json()
        
        # Ekstrak informasi rate limit dari header respons
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
                summary = f"*ID*: {video_data.get('aweme_id')}\n"
                summary += f"*Title*: {video_data.get('title')}\n"
                summary += f"*HD Play URL*: {video_data.get('hdplay')}\n"
                summary += format_usage_info(usage_info)
                update.message.reply_text("Data berhasil diambil:\n" + summary, parse_mode='Markdown')
            else:
                update.message.reply_text("API mengembalikan error:\n" + str(data))
        else:
            update.message.reply_text("Terjadi kesalahan saat menghubungi API RapidAPI.")
    else:
        update.message.reply_text("Silakan kirim link video TikTok untuk mengambil data.")

def check_limit(update: Update, context: CallbackContext):
    """
    Handler untuk perintah /limit. Fungsi ini memanggil API dengan URL dummy
    untuk mendapatkan informasi penggunaan API dan mengembalikannya ke pengguna.
    """
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

    # Handler untuk perintah /start
    dp.add_handler(CommandHandler("start", start))
    # Handler untuk perintah /limit untuk mengecek sisa penggunaan API
    dp.add_handler(CommandHandler("limit", check_limit))
    # Handler untuk pesan teks yang mengandung link TikTok
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("Bot berjalan...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
