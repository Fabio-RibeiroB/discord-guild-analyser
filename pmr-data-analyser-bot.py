import discord
import logging
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import csv

logger = logging.getLogger("my_bot")
logger.setLevel(logging.INFO)

# Create a handler to log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
# Create a formatter for the log messages
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Add the formatter to the console handler
console_handler.setFormatter(formatter)

# Add the console handler to the logger
logger.addHandler(console_handler)
logger.info("Loading variables...")

load_dotenv()

intents = discord.Intents.all()
intents.messages = True

client = commands.Bot(command_prefix="$", intents=intents)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

async def get_recent_messages_from_all_channels(guild, limit, oldest_first=True):
    """Get messages from all channels going back by the amount specified by limit"""
    all_messages = []

    for channel in guild.text_channels:
        # Skip private channels
        if not isinstance(channel, discord.TextChannel) or not channel.permissions_for(guild.me).read_messages:
            continue

        messages_list = await get_recent_messages(channel, limit)
        all_messages.extend(messages_list)

    return all_messages

async def get_recent_messages(channel, limit):
    """Get the channel's messages going back by the amount specified by limit"""
    message_list = []
    async for message in channel.history(limit=limit, oldest_first=True):
        if not message.author.bot:
            message_list.append(message)

    return message_list
@client.command()
async def messages_per_week(ctx, scope='channel', channel: discord.TextChannel=None, limit=None):
    """
    Analyze messages per week in the specified scope (channel or server).

    Parameters:
        - scope (str): 'channel' (default) or 'server'
        - channel (discord.TextChannel): Optional channel for analysis. Defaults to the current channel.
        - limit (int): Number of messages to consider (default is None, meaning all messages).
    """
    logger.info("Starting analysis..")
    if limit is not None:
        limit = int(limit)

    if channel is None:
        channel = ctx.channel

    if scope.lower() == 'channel':
        messages_list = await get_recent_messages(channel, limit)
    elif scope.lower() == 'server':
        messages_list = await get_recent_messages_from_all_channels(ctx.guild, limit)
    else:
        await ctx.send("Invalid scope. Please use 'channel' or 'server'.")
        return

    # Calculate messages per week
    messages_per_week = {}
    current_datetime = discord.utils.utcnow()

    for message in messages_list:
        weeks_ago = (current_datetime - message.created_at).days // 7

        if weeks_ago not in messages_per_week:
            messages_per_week[weeks_ago] = []

        messages_per_week[weeks_ago].append(message.created_at)

    # Sort the results by weeks ago
    sorted_messages = sorted(messages_per_week.items(), key=lambda x: x[0])

    # Write data to CSV
    csv_file_path = 'messages_per_week.csv'
    with open(csv_file_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Weeks Ago', 'Week Start', 'Week End', 'Messages Per Week'])

        for weeks_ago, dates in sorted_messages:
            start_of_week = (current_datetime - timedelta(weeks=weeks_ago, days=current_datetime.weekday())).date()
            end_of_week = start_of_week + timedelta(days=6)
            if end_of_week >= current_datetime.date():
                end_of_week = current_datetime.date()
            csv_writer.writerow([weeks_ago, start_of_week, end_of_week, len(dates)])

    # Send the CSV file
    await ctx.send(file=discord.File(csv_file_path))

client.run(os.getenv("DISCORD_TOKEN"))

