import discord
from discord.ext import commands
from datetime import datetime, UTC
import asyncio
import os
from flask import Flask
from threading import Thread

# --- نظام الـ Keep Alive لضمان عمل البوت 24/7 على الاستضافة المجانية ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- إعداد الصلاحيات الأساسية ---
intents = discord.Intents.default()
intents.members = True 
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
user_last_msg_time = {}

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="أمن السيرفر 🛡️"))
    print(f'✅ تم تفعيل البوت بنجاح: {bot.user.name}')

# --- 1. نظام الحماية الذكي (Anti-Spam & Anti-Links) ---
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return

    # منع الروابط للأعضاء فقط (يُستثنى من لديهم صلاحية إدارة الرسائل)
    if "http" in message.content.lower() and not message.author.guild_permissions.manage_messages:
        await message.delete()
        await message.channel.send(f"⚠️ {message.author.mention}، يمنع نشر الروابط هنا!", delete_after=3)
        return

    # مكافحة السبام (منع الرسائل السريعة أقل من 0.8 ثانية)
    uid = message.author.id
    now = asyncio.get_event_loop().time()
    if uid in user_last_msg_time and now - user_last_msg_time[uid] < 0.8:
        await message.delete()
        return 
    user_last_msg_time[uid] = now

    await bot.process_commands(message)

# --- 2. نظام الترحيب (Welcome) ---
@bot.event
async def on_member_join(member):
    # يبحث البوت عن قناة باسم "général" للترحيب
    channel = discord.utils.get(member.guild.text_channels, name="général")
    if channel:
        embed = discord.Embed(
            title="✨ انضمام عضو جديد ✨",
            description=f"يا هلا بـ {member.mention} في سيرفرنا!\nنورتنا يا بطل، استمتع بوقتك.",
            color=0x7289da,
            timestamp=datetime.now(UTC)
        )
        embed.set_image(url=member.display_avatar.url)
        embed.add_field(name="🔢 العضو رقم", value=str(len(member.guild.members)), inline=True)
        embed.set_footer(text=f"سيرفر {member.guild.name}")
        await channel.send(embed=embed)

# --- 3. نظام السجلات الكامل (Logs) ---
@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    log_channel = discord.utils.get(message.guild.text_channels, name="logs")
    if log_channel:
        embed = discord.Embed(title="🗑️ رسالة محذوفة", color=discord.Color.red(), timestamp=datetime.now(UTC))
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.add_field(name="الكاتب:", value=message.author.mention, inline=True)
        embed.add_field(name="القناة:", value=message.channel.mention, inline=True)
        embed.add_field(name="المحتوى:", value=message.content or "صورة أو ملف", inline=False)
        await log_channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content: return
    log_channel = discord.utils.get(before.guild.text_channels, name="logs")
    if log_channel:
        embed = discord.Embed(title="📝 رسالة معدلة", color=discord.Color.orange(), timestamp=datetime.now(UTC))
        embed.set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url)
        embed.add_field(name="قبل:", value=before.content[:1024], inline=False)
        embed.add_field(name="بعد:", value=after.content[:1024], inline=False)
        await log_channel.send(embed=embed)

# --- 4. الأوامر الأساسية (Commands) ---

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    """أمر مسح الرسائل"""
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"✅ تم مسح {amount} رسالة.", delete_after=2)

@bot.command()
async def user(ctx, member: discord.Member = None):
    """أمر معلومات العضو"""
    member = member or ctx.author
    embed = discord.Embed(title=f"معلومات {member.display_name}", color=member.color)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="الآيدي", value=member.id, inline=True)
    joined_at = member.joined_at.strftime("%Y/%m/%d") if member.joined_at else "غير متوفر"
    embed.add_field(name="تاريخ الانضمام", value=joined_at, inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def server(ctx):
    """أمر معلومات السيرفر"""
    embed = discord.Embed(title=f"بيانات {ctx.guild.name}", color=discord.Color.blue())
    embed.add_field(name="الأعضاء", value=ctx.guild.member_count)
    embed.add_field(name="المالك", value=ctx.guild.owner.mention)
    await ctx.send(embed=embed)

# --- تشغيل البوت باستخدام TOKEN من المتغيرات البيئية ---
keep_alive()
token = os.getenv('TOKEN')
if token:
    bot.run(token)
else:
    print("❌ خطأ: لم يتم العثور على التوكن (TOKEN) في إعدادات البيئة!")