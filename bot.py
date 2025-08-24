import os
import time
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv
from database import AsyncUserDatabase

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
XP_COOLDOWN = int(os.getenv('XP_COOLDOWN'))
XP_PER_MESSAGE = int(os.getenv('XP_PER_MESSAGE'))
COINS_PER_MESSAGE = float(os.getenv('COINS_PER_MESSAGE'))
COINS_PER_LEVEL = int(os.getenv('COINS_PER_LEVEL'))
REWARD_LEVEL_MILESTONES = int(os.getenv('REWARD_LEVEL_MILESTONES'))

db = AsyncUserDatabase()

intents = discord.Intents.default()
# Determines whether bot can read messages (necessary for commands)
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Process messages being sent
async def handle_user_activity(message):
    """Handle XP gain, coin gain, level up"""
    user = await db.get_user(message.author.id)
    current_time = int(time.time())
    
    # Check if cooldown is done - exit if no
    if current_time - user['last_message_time'] < XP_COOLDOWN:
        return

    # Gain XP and coins
    leveled_up = await db.update_user_xp(message.author.id, XP_PER_MESSAGE)
    await db.update_user_coins(message.author.id, COINS_PER_MESSAGE)

    # Update last message time
    await db.update_last_message_time(message.author.id, current_time, message.author.name)
        
    # Get updated user data
    updated_user = await db.get_user(message.author.id)
    print(f"After: Level {updated_user['level']}, XP {updated_user['xp']}, Coins {updated_user['coins']}")
    
    # Handle level up rewards and announcement
    if leveled_up:
        await handle_level_up(message, updated_user)

async def handle_level_up(message, user_data):
    """Handle level up rewards / announcements"""
    new_level = user_data['level']

    # Give coins
    await db.update_user_coins(message.author.id, COINS_PER_LEVEL)

    # Send level up message
    await message.channel.send(
        f"User {message.author.mention} leveled up to level {new_level}! "
        f"You earned {COINS_PER_LEVEL} coins!"
    )

    # Future: Rewards for milestones
    if new_level % REWARD_LEVEL_MILESTONES == 0:
        await message.channel.send(f"Milestone reached! Coming soon - special rewards")
    
    print(f"Level up rewards given to {message.author}")


# Loading in
@bot.event
async def on_ready():
    await db.init_database()
    print(f'{bot.user} has connected to Discord')

# Handle message sent by user
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Handle user activity
    await handle_user_activity(message)
    
    # Process bot commands
    await bot.process_commands(message)

# Check coin balance
@bot.command()
async def balance(ctx):
    """Check your coin balance"""
    user = await db.get_user(ctx.author.id)
    await ctx.send(f"{ctx.author.mention}, you have **{user['coins']:.1f}** coins!")

# Check profile
@bot.command()
async def profile(ctx):
    """Check your profile"""
    user = await db.get_user(ctx.author.id)
    await ctx.send(
        f"**{ctx.author.mention}'s Profile**\n"
        f"Level: {user['level']}\n"
        f"XP: {user['xp']}\n"
        f"Coins: {user['coins']:.1f}"
    )

# Check shop
@bot.command()
async def shop(ctx, category=None):
    """View the shop items"""
    items = await db.get_shop_items(category)
    
    if not items:
        await ctx.send("Shop is empty!")
        return
    
    # Group by category
    categories = {}
    for item in items:
        cat = item['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    shop_text = "🛒 **SHOP** 🛒\n\n"
    
    for cat_name, cat_items in categories.items():
        shop_text += f"**{cat_name.upper()}**\n"
        for item in cat_items:
            emoji = "🎨" if item['category'] == "cosmetic" else "⚡" if item['category'] == "utility" else "🍀"
            shop_text += f"{emoji} `ID: {item['id']}` **{item['name']}** - {item['price']} coins\n"
            shop_text += f"   _{item['description']}_\n"
            if item['min_level'] > 1:
                shop_text += f"   _Requires level {item['min_level']}_\n"
            shop_text += "\n"
    
    shop_text += "Use `!buy <item_id>` to purchase!"
    await ctx.send(shop_text)

@bot.command()
async def buy(ctx, item_id: int):
    """Purchase an item from the shop"""
    result = await db.purchase_item(ctx.author.id, item_id)
    
    if result["success"]:
        await ctx.send(f"✅ {result['message']}\n💰 Coins remaining: {result['coins_remaining']}")
    else:
        await ctx.send(f"❌ {result['message']}")

@bot.command()
async def inventory(ctx):
    """Check your inventory"""
    items = await db.get_user_inventory(ctx.author.id)
    
    if not items:
        await ctx.send("Your inventory is empty!")
        return
    
    inv_text = f"🎒 **{ctx.author.mention}'s Inventory**\n\n"
    for item_name, description, quantity, effect_type, effect_value in items:
        inv_text += f"• **{item_name}** x{quantity}\n"
        inv_text += f"  _{description}_\n\n"
    
    await ctx.send(inv_text)

bot.run(BOT_TOKEN)