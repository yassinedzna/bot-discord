import discord
from discord.ext import commands
from datetime import datetime, UTC
import asyncio
import os
from flask import Flask
from threading import Thread

# --- نظام البقاء حياً (Keep Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online! 🛡️"

def run():
    # Render يمرر المنفذ تلقائياً عبر متغير PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- إعدادات البوت ---
intents = discord.Intents.default()
intents.members = True 
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
user_last_msg_time = {}

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="أمن السيرفر 🛡️"))
    print(f'✅ البوت يعمل الآن: {bot.user.name}')

# --- نظام الحماية (روابط وسبام) ---
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return

    if "http" in message.content.lower() and not message.author.guild_permissions.manage_messages:
        await message.delete()
        await message.channel.send(f"⚠️ {message.author.mention}، يمنع الروابط!", delete_after=3)
        return

    uid = message.author.id
    now = asyncio.get_event_loop().time()
    if uid in user_last_msg_time and now - user_last_msg_time[uid] < 0.8:
        await message.delete()
        return 
    user_last_msg_time[uid] = now

    await bot.process_commands(message)

# --- أوامر الإدارة ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"✅ تم مسح {amount} رسالة.", delete_after=2)

# --- التشغيل النهائي ---
if __name__ == "__main__":
    keep_alive()
    token = os.getenv('TOKEN')
    if token:
        bot.run(token)
    else:
        print("❌ خطأ: التوكن غير موجود في إعدادات البيئة!")
