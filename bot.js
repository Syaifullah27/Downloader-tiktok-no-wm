require('dotenv').config();
const { Telegraf } = require('telegraf');
const axios = require('axios');

const bot = new Telegraf(process.env.TELEGRAM_BOT_TOKEN);
const RAPID_API_HOST = 'tiktok-video-downloader-api.p.rapidapi.com';
const RAPID_API_KEY = process.env.RAPIDAPI_KEY || 'e3c9aaf249msh9d7514dbcb20064p15b928jsn5590edf36d1e';
const API_URL = `https://${RAPID_API_HOST}/media`;

// Fungsi untuk resolve URL pendek menjadi URL lengkap
async function resolveUrl(shortUrl) {
  try {
    // Lakukan request GET dan biarkan axios mengikuti redirect
    const response = await axios.get(shortUrl, { maxRedirects: 5 });
    // Jika request berhasil tanpa error, ambil URL final dari properti response.request.res.responseUrl
    const finalUrl = response.request.res.responseUrl;
    return finalUrl || shortUrl;
  } catch (error) {
    // Jika terjadi error redirect, coba periksa header 'location'
    if (error.response && error.response.headers && error.response.headers.location) {
      return error.response.headers.location;
    }
    console.error("Error resolving URL:", error.message);
    return shortUrl;
  }
}

bot.start((ctx) => {
  const welcomeMessage =
    '🤖 Selamat datang di TikTok Downloader Bot!\n\n' +
    'Cara penggunaan:\n' +
    '1. Kirim link video TikTok (misalnya, link pendek atau link lengkap).\n' +
    '2. Bot akan melakukan resolve link dan langsung mengunduh video tanpa watermark.\n\n' +
    'Silakan kirim link video TikTok sekarang!';
  ctx.reply(welcomeMessage);
});

bot.hears(/tiktok\.com/, async (ctx) => {
  let url = ctx.message.text.trim();
  
  // Coba resolve URL jika merupakan URL pendek
  try {
    const resolvedUrl = await resolveUrl(url);
    url = resolvedUrl;
    console.log(`Resolved URL: ${url}`);
  } catch (err) {
    console.error("Error during URL resolution:", err.message);
  }
  
  try {
    // Meminta data video dari RapidAPI dengan URL yang sudah di-resolve
    const response = await axios.get(API_URL, {
      params: { videoUrl: url },
      headers: {
        'x-rapidapi-key': RAPID_API_KEY,
        'x-rapidapi-host': RAPID_API_HOST
      }
    });
    const data = response.data;
    if (!data || data.error) {
      return ctx.reply("⚠ Video tidak tersedia. Pastikan link benar.");
    }
    
    // Ambil data preview video
    const videoDescription = data.description || 'Tidak diketahui';
    const videoUsername = data.username || 'Tidak diketahui';
    const videoCover = data.cover || '';
    const captionPreview = `🎬 *Deskripsi:* ${videoDescription}\n👤 *Username:* ${videoUsername}\n\nSedang mengunduh video...`;
    
    // Kirim preview berupa gambar cover
    await ctx.replyWithPhoto(videoCover, { caption: captionPreview, parse_mode: 'Markdown' });
    
    // Mendapatkan URL download video
    const downloadUrl = data.downloadUrl;
    if (!downloadUrl) {
      return ctx.reply("⚠ Gagal mendapatkan URL download. Coba lagi nanti.");
    }
    
    // Mengunduh video sebagai buffer
    const videoResponse = await axios.get(downloadUrl, { responseType: 'arraybuffer' });
    const videoBuffer = Buffer.from(videoResponse.data, 'binary');
    await ctx.replyWithVideo({ source: videoBuffer }, { caption: "📤 Video tanpa watermark berhasil diunduh!" });
  } catch (error) {
    console.error(error.response ? error.response.data : error.message);
    ctx.reply("⚠ Terjadi kesalahan, silakan coba lagi nanti.");
  }
});

bot.launch();
console.log("Bot sudah berjalan...");

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
