# bot.py
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
intents = discord.Intents.default()
# This allows bot to see message content when True - not needed for now
intents.message_content = False

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    print(f'{bot.user}: Message from {message.author}')

# Error handling
if not TOKEN:
    print("Error: BOT_TOKEN not found in environment variables")
    exit(1)

bot.run(TOKEN)