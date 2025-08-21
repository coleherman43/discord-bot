import os
import time
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv
from database import AsyncUserDatabase

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
XP_COOLDOWN = int(os.getenv('XP_COOLDOWN'))
XP_GAIN = int(os.getenv('XP_PER_MESSAGE'))
db = AsyncUserDatabase()

intents = discord.Intents.default()
# Change this later to True to read message contents
intents.message_content = False

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    await db.init_database()
    print(f'{bot.user} has connected to Discord')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    user = await db.get_user(message.author.id)
    current_time = int(time.time())
    if current_time - user['last_message_time'] >= XP_COOLDOWN:
        print(f"Before: Level {user['level']}, XP {user['xp']}")
        
        # Gain XP
        leveled_up = await db.update_user_xp(message.author.id, XP_GAIN)
        
        # Get updated user data for debug
        updated_user = await db.get_user(message.author.id)
        print(f"After: Level {updated_user['level']}, XP {updated_user['xp']}")
        print(f"Leveled up: {leveled_up}")
        
        await db.update_last_message_time(message.author.id, current_time, message.author.name)
        
        if leveled_up:
            await message.channel.send(f"Yay! {message.author.mention} leveled up to level {updated_user['level']}!")
    
    await bot.process_commands(message)

bot.run(TOKEN)