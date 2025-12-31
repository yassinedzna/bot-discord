import discord
from discord.ext import commands
from datetime import datetime, UTC
import asyncio
import os
from flask import Flask
from threading import Thread

# --- نظام البقاء حياً (Keep Alive) لضمان استمرار البوت 24/7 ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online and Secure! 🛡️"

def run():
    # Render يطلب تشغيل الويب على المنفذ 10000 أو 8080 بشكل افتراضي
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- إعدادات البوت الأساسية ---
intents = discord.Intents.default()
intents.members = True 
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
user_last_msg_time = {}

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="أمن السيرفر 🛡️"))
    print(f'✅ تم تفعيل البوت بنجاح: {bot.user.name}')

# --- 1. نظام الحماية الذكي (روابط وسبام) ---
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return

    # منع الروابط لغير الإداريين
    if "http" in message.content.lower() and not message.author.guild_permissions.manage_messages:
        await message.delete()
        await message.channel.send(f"⚠️ {message.author.mention}، يمنع نشر الروابط!", delete_after=3)
        return

    # مكافحة السبام (منع الرسائل السريعة)
    uid = message.author.id
    now = asyncio.get_event_loop().time()
    if uid in user_last_msg_time and now - user_last_msg_time[uid] < 0.8:
        await message.delete()
        return 
    user_last_msg_time[uid] = now

    await bot.process_commands(message)

# --- 2. نظام الترحيب والسجلات ---
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="général")
    if channel:
        embed = discord.Embed(title="✨ عضو جديد ✨", description=f"مرحباً {member.mention}!", color=0x7289da)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    log_channel = discord.utils.get(message.guild.text_channels, name="logs")
    if log_channel:
        embed = discord.Embed(title="🗑️ رسالة محذوفة", color=discord.Color.red(), timestamp=datetime.now(UTC))
        embed.add_field(name="الكاتب:", value=message.author.mention)
        embed.add_field(name="المحتوى:", value=message.content or "صورة/ملف")
        await log_channel.send(embed=embed)

# --- 3. أوامر الإدارة ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"✅ تم مسح {amount} رسالة.", delete_after=2)

# --- تشغيل البوت ---
if __name__ == "__main__":
    keep_alive() # تشغيل خادم الويب
    token = os.getenv('TOKEN') # جلب التوكن من إعدادات Render
    if token:
        bot.run(token)
    else:
        print("❌ خطأ: التوكن غير موجود في Environment Variables")
