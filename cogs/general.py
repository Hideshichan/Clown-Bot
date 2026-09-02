import discord
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        
    @commands.command()
    async def help(self, ctx):
        help_message = (
            "Here are the available commands:\n"
            "`$help` - Displays this help message.\n"
            "`$addrole <user> <role>` - Adds a role to a user (requires appropriate permissions).\n"
            "`$removerole <user> <role>` - Removes a role from a user (requires appropriate permissions).\n"
            "`$reactionrole <emoji> <role>` - Creates a reaction-role embed (requires appropriate permissions).\n"
            "`$reload <extension>` - Reloads a cog (owner only).\n"
            "`$load <extension>` - Loads a cog (owner only).\n"
        )
        embed = discord.Embed(
            title="Help",
            description=help_message,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        
async def setup(bot):
    await bot.add_cog(General(bot))