import json
import os
import discord
from discord.ext import commands

DATA_FILE = os.environ.get(
    "REACTION_ROLES_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "reaction_roles.json"),
)
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
DEBUG_CHANNEL_ID = int(os.getenv("DEBUG_CHANNEL_ID", 0)) or None


class roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reaction_roles = self._load_data()
        self.debug_mode = False

    def _load_data(self):
        if not os.path.exists(DATA_FILE):
            return {}
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return {int(msg_id): mapping for msg_id, mapping in raw.items()}
        except (json.JSONDecodeError, ValueError) as e:
            return {}

    def _save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.reaction_roles, f, indent=2)

    async def _debug_reaction(self, payload, message):
        if self.debug_mode == False:
            return
        if DEBUG_CHANNEL_ID is None:
            return
        channel = self.bot.get_channel(DEBUG_CHANNEL_ID)
        if channel is None:
            return
        try:
            await channel.send(f"DEBUG: {message}")
        except Exception:
            pass

    def _get_role_id_for_emoji(self, message_id, emoji):
        reaction_map = self.reaction_roles.get(message_id)
        if reaction_map is None:
            return None

        emoji_key = str(emoji)
        candidates = {emoji_key}

        if getattr(emoji, "id", None) is not None and getattr(emoji, "name", None):
            candidates.add(f"<:{emoji.name}:{emoji.id}>")
            candidates.add(f"<a:{emoji.name}:{emoji.id}>")
            candidates.add(emoji.name)

        for key in candidates:
            if key in reaction_map:
                return reaction_map[key]

        return None
    


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self._debug_reaction(payload, f"reaction_add received: {payload.emoji} user={payload.user_id} msg={payload.message_id}")

        if payload.guild_id is None or payload.message_id not in self.reaction_roles:
            await self._debug_reaction(payload, "reaction_add ignored: message not tracked")
            return
        if payload.user_id == self.bot.user.id:
            await self._debug_reaction(payload, "reaction_add ignored: bot reaction")
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            await self._debug_reaction(payload, "reaction_add ignored: guild not found")
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            try:
                member = await guild.fetch_member(payload.user_id)
            except discord.NotFound:
                await self._debug_reaction(payload, f"reaction_add ignored: member {payload.user_id} not found")
                return

        role_id = self._get_role_id_for_emoji(payload.message_id, payload.emoji)
        if role_id is None:
            await self._debug_reaction(payload, f"reaction_add ignored: no role mapped for emoji {payload.emoji}")
            return

        role = guild.get_role(role_id)
        if role is None:
            await self._debug_reaction(payload, f"reaction_add ignored: mapped role id {role_id} not found")
            return
        if role in member.roles:
            await self._debug_reaction(payload, f"reaction_add ignored: {member.mention} already has {role.name}")
            return

        try:
            await member.add_roles(role)
            await self._debug_reaction(payload, f"reaction_add: gave {member.mention} the role {role.name}")
        except discord.Forbidden:
            await self._debug_reaction(payload, f"reaction_add FAILED: missing permission to give {role.name} (check role hierarchy)")
        except discord.HTTPException as e:
            await self._debug_reaction(payload, f"reaction_add FAILED: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self._debug_reaction(payload, f"reaction_remove received: {payload.emoji} user={payload.user_id} msg={payload.message_id}")

        if payload.guild_id is None or payload.message_id not in self.reaction_roles:
            await self._debug_reaction(payload, "reaction_remove ignored: message not tracked")
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            await self._debug_reaction(payload, "reaction_remove ignored: guild not found")
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            try:
                member = await guild.fetch_member(payload.user_id)
            except discord.NotFound:
                await self._debug_reaction(payload, f"reaction_remove ignored: member {payload.user_id} not found")
                return

        role_id = self._get_role_id_for_emoji(payload.message_id, payload.emoji)
        if role_id is None:
            await self._debug_reaction(payload, f"reaction_remove ignored: no role mapped for emoji {payload.emoji}")
            return

        role = guild.get_role(role_id)
        if role is None:
            await self._debug_reaction(payload, f"reaction_remove ignored: mapped role id {role_id} not found")
            return
        if role not in member.roles:
            await self._debug_reaction(payload, f"reaction_remove ignored: {member.mention} does not have {role.name}")
            return

        try:
            await member.remove_roles(role)
            await self._debug_reaction(payload, f"reaction_remove: removed {role.name} from {member.mention}")
        except discord.Forbidden:
            await self._debug_reaction(payload, f"reaction_remove FAILED: missing permission to remove {role.name} (check role hierarchy)")
        except discord.HTTPException as e:
            await self._debug_reaction(payload, f"reaction_remove FAILED: {e}")
            
    @commands.command()
    @commands.is_owner()
    async def debugmode(self, ctx):
        message = ""
        channel = self.bot.get_channel(DEBUG_CHANNEL_ID)
        self.debug_mode = not self.debug_mode
        if self.debug_mode:
            message = "✅ Debug mode is now ON. Debug messages will be sent to the debug channel."
        else:
            message = "❌ Debug mode is now OFF. Debug messages will not be sent."
        await channel.send(message)

    @commands.command()
    @commands.is_owner()
    async def addrole(self, ctx, user: discord.Member, role: discord.Role):
        """Adds a role to the user."""
        try:
            if role in user.roles:
                await ctx.send(f"❌ {user.mention} already has the role: {role.name}.")
                return
            await user.add_roles(role)
            await ctx.send(f"✅ {user.mention} has been given the role: {role.name}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to add that role.")
        except discord.HTTPException:
            await ctx.send("❌ An error occurred while trying to add the role.")

    @commands.command()
    @commands.is_owner()
    async def rmrole(self, ctx, user: discord.Member, role: discord.Role):
        """Removes a role from the user."""
        try:
            if role not in user.roles:
                await ctx.send(f"❌ {user.mention} does not have the role: {role.name}.")
                return
            await user.remove_roles(role)
            await ctx.send(f"✅ {user.mention} no longer has the role: {role.name}.")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to remove that role.")
        except discord.HTTPException:
            await ctx.send("❌ An error occurred while trying to remove the role.")

    async def _resolve_role(self, ctx, role_arg):
        try:
            return await commands.RoleConverter().convert(ctx, role_arg)
        except commands.BadArgument:
            if role_arg.isdigit():
                return discord.utils.get(ctx.guild.roles, id=int(role_arg))
            return None

    @commands.command()
    @commands.is_owner()
    async def reactionrole(self, ctx, *args):
        """Creates a reaction-role embed with multiple emoji-to-role assignments."""
        if len(args) == 0 or len(args) % 2 != 0:
            await ctx.send(
                "Usage: `$reactionrole <emoji> <role> <emoji> <role> ...`\n"
                "Example: `$reactionrole 😀 @Members 🤖 @Bots`"
            )
            return

        mapping = {}

        for i in range(0, len(args), 2):
            emoji = args[i]
            role_arg = args[i + 1]

            role = await self._resolve_role(ctx, role_arg)
            if role is None:
                await ctx.send(f"❌ Could not find the role: `{role_arg}`")
                return

            if emoji in mapping:
                await ctx.send(f"❌ Duplicate emoji: {emoji}")
                return

            mapping[emoji] = role.id

        embed = discord.Embed(
            title="🎭 Reaction Roles",
            description="React below to claim your role(s).",
            color=discord.Color.blurple(),
        )

        field_lines = [f"{emoji} - <@&{role_id}>" for emoji, role_id in mapping.items()]
        if field_lines:
            embed.description = "\n".join(field_lines)

        try:
            message = await ctx.send(embed=embed)
            self.reaction_roles[message.id] = mapping
            self._save_data()

            for emoji in mapping:
                await message.add_reaction(emoji)

            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to create the reaction-role message.")
        except discord.HTTPException:
            await ctx.send("❌ An error occurred while creating the reaction-role message.")

    @commands.command()
    @commands.is_owner()
    async def editreactionroles(self, ctx, message_id: int, emoji: str, role_arg: str):
        """Adds a new emoji-to-role mapping to an existing reaction-role message."""
        if message_id not in self.reaction_roles:
            await ctx.send(f"❌ Message ID `{message_id}` is not a tracked reaction-role message.")
            return

        role = await self._resolve_role(ctx, role_arg)
        if role is None:
            await ctx.send(f"❌ Could not find the role: `{role_arg}`")
            return

        if emoji in self.reaction_roles[message_id]:
            await ctx.send(f"❌ {emoji} is already mapped on that message.")
            return

        try:
            message = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("❌ Could not find that message in this channel (must be run in the same channel it was posted).")
            return
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to fetch that message.")
            return

        self.reaction_roles[message_id][emoji] = role.id
        self._save_data()

        try:
            await message.add_reaction(emoji)
        except discord.HTTPException as e:
            await ctx.send(f"⚠️ Mapping saved, but couldn't add the reaction to the message: {e}")
            return

        if message.embeds:
            embed = message.embeds[0]
            new_line = f"{emoji} - {role.mention}"
            embed.description = f"{embed.description}\n{new_line}" if embed.description else new_line
            try:
                await message.edit(embed=embed)
            except discord.HTTPException:
                pass

        await ctx.send(f"✅ Added {emoji} → {role.mention} to message `{message_id}`.")


async def setup(bot):
    await bot.add_cog(roles(bot))
