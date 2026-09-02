import asyncio
import discord
from discord.ext import commands

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(
                description="❌ Not a valid command.",
                color=discord.Color.red()
            )
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await msg.delete()
            return
        raise error

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))