import discord
from discord.ext import commands


class roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reaction_roles = {}

    async def _debug_reaction(self, payload, message):
        channel = self.bot.get_channel(payload.channel_id)
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
            await self._debug_reaction(payload, f"reaction_add ignored: message not tracked")
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

        await member.add_roles(role)
        await self._debug_reaction(payload, f"reaction_add: gave {member.mention} the role {role.name}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self._debug_reaction(payload, f"reaction_remove received: {payload.emoji} user={payload.user_id} msg={payload.message_id}")

        if payload.guild_id is None or payload.message_id not in self.reaction_roles:
            await self._debug_reaction(payload, f"reaction_remove ignored: message not tracked")
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

        await member.remove_roles(role)
        await self._debug_reaction(payload, f"reaction_remove: removed {role.name} from {member.mention}")

    @commands.command()
    async def addrole(self, ctx, user: discord.Member, role: discord.Role):
        """Adds a role to the user."""
        try:
            if role in user.roles:
                await ctx.send(f"❌ {user.mention} already has the role: {role.name}.")
                return
            await user.add_roles(role)
            await ctx.send(f"✅ {user.mention} has been given the role: {role.name}.")
            if "test" in role.name.lower():
                await user.remove_roles(role)
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to add that role.")
        except discord.HTTPException:
            await ctx.send("❌ An error occurred while trying to add the role.")

    @commands.command()
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

    @commands.command()
    async def reactionrole(self, ctx, *args):
        """Creates a reaction-role embed with multiple emoji-to-role assignments."""
        if len(args) == 0 or len(args) % 2 != 0:
            await ctx.send(
                "Usage: `!reactionrole <emoji> <role> <emoji> <role> ...`\n"
                "Example: `!reactionrole 😀 @Members 🤖 @Bots`"
            )
            return

        mapping = {}

        for i in range(0, len(args), 2):
            emoji = args[i]
            role_arg = args[i + 1]

            try:
                role = await commands.RoleConverter().convert(ctx, role_arg)
            except commands.BadArgument:
                if role_arg.isdigit():
                    role = discord.utils.get(ctx.guild.roles, id=int(role_arg))
                else:
                    role = None

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

        field_lines = []
        for emoji, role_id in mapping.items():
            role = ctx.guild.get_role(role_id)
            if role is not None:
                field_lines.append(f"{emoji} - {role.mention}")

        if field_lines:
            embed.description = "\n".join(field_lines)

        try:
            message = await ctx.send(embed=embed)
            self.reaction_roles[message.id] = mapping

            for emoji in mapping:
                await message.add_reaction(emoji)

            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to create the reaction-role message.")
        except discord.HTTPException:
            await ctx.send("❌ An error occurred while creating the reaction-role message.")


async def setup(bot):
    await bot.add_cog(roles(bot))