import os
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
guild_reactions = True

bot = commands.Bot(command_prefix="$", intents=intents)
bot.remove_command("help")  # Remove the default help command to use a custom one

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    
@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    try:
        await bot.reload_extension(f'cogs.{extension}')
        await ctx.send(f'✅ Reloaded `{extension}`')
    except Exception as e:
        await ctx.send(f'❌ Error reloading `{extension}`: {e}')
        
@bot.command()
@commands.is_owner()
async def load(ctx, extension):
    try:
        await bot.load_extension(f'cogs.{extension}')
        await ctx.send(f'✅ Loaded `{extension}`')
    except Exception as e:
        await ctx.send(f'❌ Error loading `{extension}`: {e}')

async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    token = os.getenv('BOT_TOKEN')
    if not token:
        raise SystemExit("BOT_TOKEN is not set — check your .env file")

    async with bot:
        await load_extensions()
        await bot.start(token)

asyncio.run(main())