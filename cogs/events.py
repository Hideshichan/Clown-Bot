import discord
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        
        
    @commands.command()
    async def createevent(self, ctx, title: str, description: str):
        """Creates a new event"""
        await ctx.send(f"Event created: {title}\nDescription: {description}")
        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    async def submit(self, ctx, user: discord.User, *args):
        """Allows users to submit text or images for events"""
        if len(args) == 0 or not ctx.message.attachments:
            await ctx.send("Please attach your text or image submission")
        else:
            await ctx.send("Thank you for your submission!\nAttempting to save it now...")
            # save attachment with name discord user name, if text save in submissions.json with user:submission
            attachment = ctx.message.attachments[0]
            try:
                await attachment.save(f"./event_stuff/submissions/{user.name}_{attachment.filename}")
            except Exception as e:
                await ctx.send(f"❌ Error saving image submission: {e}\nIf this is incorrect please contact me.")