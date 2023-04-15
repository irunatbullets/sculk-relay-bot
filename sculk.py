import discord
from discord.ext import commands
import asyncio
import os
import json
import time

bot_token = os.environ.get("BOT_TOKEN")

with open('config.json', 'r') as f:
    config = json.load(f)

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

allowed_roles = config['roles']
mc_server_channel_ids = config['channels']['mc_servers']
staff_channel_id = config['channels']['staff']

startup_time = int(time.time())

async def run_command(ctx, mc_user: str, command: str, reason: str = None):
    success = []  # Keep track of whether each channel's ban was successful
    failed_channel_mentions = [] # Keep track of the mentions of failed channels

    for channel_id in mc_server_channel_ids:
        channel = bot.get_channel(channel_id)

        if reason and command != 'pardon':
            await channel.send(f'!console {command} {mc_user} {reason}')
        else:
            await channel.send(f'!console {command} {mc_user}')
        try:
            def check(message):
                return ('nothing changed' in message.content.lower() or ('banned' in message.content.lower() and mc_user.lower()))
            await bot.wait_for('message', check=check, timeout=1.0)
            success.append(True)
        except asyncio.TimeoutError:
            failed_channel_mentions.append(channel.mention)
            success.append(False)

    # Check if all bans were successful
    # Check if all commands were successful
    if all(success):
        message = f'Successfully {command}ed `{mc_user}` in all channels'
    elif any(success):
        message = f'Failed to {command} `{mc_user}` in channel(s) {", ".join(failed_channel_mentions)}, but {command}ed in other channels'
    else:
        message = f'Failed to {command} `{mc_user}` in any channels'

    if reason:
        message += f' for `{reason}`.'
    else:
        message += f'.'

    await ctx.send(message)

# Define a function to ban a user in multiple channels
async def ban_user(ctx, mc_user: str, reason: str):
    await run_command(ctx, mc_user, 'ban', reason)

# Define a function to pardon a user in multiple channels
async def pardon_user(ctx, mc_user: str):
    await run_command(ctx, mc_user, 'pardon')

# Define a command to ban a user
@bot.command()
@commands.has_any_role(*allowed_roles)
@commands.check(lambda ctx: ctx.channel.id == staff_channel_id)
async def console(ctx, action: str = None, mc_user: str = None, *, reason: str = None):
    if not action:
        # Display help message
        await ctx.send('Available commands are `ban` and `pardon`. Usage is `!console ban username reason` or `!console pardon username`.')
        return
    if action == 'ban':
        if mc_user and reason:
            await ban_user(ctx, mc_user, reason)
        else:
            await ctx.send('Invalid arguments. Usage is `!console ban username reason`')
    elif action == 'pardon':
        if mc_user:
            await pardon_user(ctx, mc_user)
        else:
            await ctx.send('Invalid arguments. Usage is `!console pardon username`')
    else:
        await ctx.send('Available commands are `ban` and `pardon`. Usage is `!console ban username reason` or `!console pardon username`.')

@bot.command()
@commands.has_any_role(*allowed_roles)
@commands.check(lambda ctx: ctx.channel.id == staff_channel_id)
async def uptime(ctx):
    await ctx.send(f'I\'ve been running since <t:{startup_time}:R>')

bot.run(bot_token)
