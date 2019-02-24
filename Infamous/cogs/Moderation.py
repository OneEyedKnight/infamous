import datetime
import logging
from .utils.rpg_tools import yon as choose
import discord
from discord.ext import commands


logging.basicConfig(level=logging.INFO)


class Sinner(commands.Converter):
    async def convert(self, ctx, argument):
        argument = await commands.MemberConverter().convert(ctx, argument)
        permission = argument.guild_permissions.manage_messages
        if not permission:
            return argument
        else:
            raise commands.BadArgument("You cannot punish other staff members")


class Redeemed(commands.Converter):
    async def convert(self, ctx, argument):
        argument = await commands.MemberConverter().convert(ctx, argument)
        muted = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted in argument.roles:
            return argument
        else:
            raise commands.BadArgument("The user was not muted.")


async def muted_role(ctx):
    try:
        return discord.utils.get(ctx.guild.roles, name="Muted")
    except discord.HTTPException:
        role = await ctx.guild.create_role(name="Muted", reason="To mute people")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False,
                                          read_message_history=False,
                                          read_messages=False)

        return discord.utils.get(ctx.guild.roles, name="Muted")


class Moderation(commands.Cog):
    """Commands to get your users in place."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.author.guild_permissions.manage_messages:
            return True
        return False

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            return await ctx.send(error)

    @commands.command()
    async def mute(self, ctx, user: Sinner = None, reason=None):
        """Silences a person"""

        user = user or await ctx.send("Pick a user to mute.")
        reason = reason or "No reason provided."
        await ctx.send(f"Are you sure you want to mute {user.mention} for **{reason}**?")
        yon = await choose(ctx)
        if yon == "Yes":
            try:
                await user.add_roles(await muted_role(ctx), reason=reason)
            except discord.Forbidden:
                await ctx.send("Did you try banning someone higher than you in role, "
                               "or did you try to ban the server owner?")
            else:
                await ctx.send(f"**{user.mention}** has been muted for **{reason}**")
        else:
            await ctx.send("I guessed you changed your mind.")

    @commands.command()
    async def unmute(self, ctx, user: Redeemed = None):
        """Unmutes the silenced"""

        user = user or await ctx.send("Provide a user")
        await user.remove_roles(await muted_role(ctx))

    @commands.command()
    async def ban(self, ctx, user: Sinner = None, reason=None):
        """Gets rid of troublemakers"""

        user = user or await ctx.send("Provide a user")
        reason = reason or "No reason provided"

        await ctx.send(f"Are you sure you want to ban {user.mention} for **{reason}**")
        yon = await choose(ctx)
        if yon == "Yes":
            try:
                await ctx.guild.ban(user, reason=f"For {reason} by {ctx.author}")
                await user.send(f"You have been banned by {ctx.author} for {reason}")
            except discord.Forbidden:
                await ctx.send("Did you try banning someone higher than you in role, "
                               "or did you try to ban the server owner?")
            else:
                await ctx.send(f"**{user}** has been banned from the server for **{reason}**")

    @commands.command()
    async def softban(self, ctx, user: Sinner = None, reason=None):
        """The perfect placebo"""

        user = user or await ctx.send("Provide a user")
        reason = reason or "No reason provided"

        await ctx.send(f"Are you sure you want to ban {user.mention} for **{reason}**")
        yon = await choose(ctx)
        if yon == "Yes":
            try:
                await ctx.guild.ban(user, reason=f"For {reason} by {ctx.author}")
                await user.send(f"You have been banned by {ctx.author} for {reason}")
                await ctx.guild.unban(user, reason=f"Was softbanned by {ctx.author} for {reason}")
            except discord.Forbidden:
                await ctx.send("Did you try banning someone higher than you in role, "
                               "or did you try to softban the server owner?")
            else:
                await ctx.send(f"**{user}** has been softbanned from the server for **{reason}**")

    @commands.command()
    async def purge(self, ctx, amount: int, user: discord.Member = None):
        """Delete x amount of messages in chat"""
        
        if user:
            await ctx.channel.purge(amount=amount + 1, check=lambda e: e.author == user)
            await ctx.send(f"Purged {amount} messages from **{user}**.", delete_after=15)

        await ctx.channel.purge(amount=amount + 1)
        await ctx.send(f"Purged {amount} messages.", delete_after=15)

    @commands.group(invoke_without_command=True, case_insensitive=True)
    async def logging(self, ctx):
        """Checks if logging is enabled."""
        
        if self.bot.logging[ctx.guild.id][0] is True:
            await ctx.send(f"Logging is enabled for **{ctx.guild.name}**")
        else:
            await ctx.send(f"Logging is disabled for **{ctx.guild.name}**")

    @logging.command(name="enable")
    async def enable_(self, ctx, channel: discord.TextChannel=None):
        """Enables logging on current/specified channel"""

        channel = channel or ctx.channel

        async with ctx.db.acquire() as db:
            d = await db.fetchval("SELECT logging FROM settings WHERE guild=$1", ctx.guild.id)
            d_ = await db.fetchval("SELECT logchannel FROM settings WHERE guild=$1", ctx.guild.id)

        if d is False:
            async with ctx.db.acquire() as db:
                await db.execute("UPDATE settings SET logging=TRUE, logchannel=$1 WHERE guild=$2", channel.id,
                                 ctx.guild.id)
            self.bot.logging[ctx.guild.id] = [True, channel.id]
            await ctx.send(f"Logging all actions to {channel.mention}")
        elif channel.id != d_:
            async with ctx.db.acquire() as db:
                await db.execute("UPDATE settings SET logchannel=$1 WHERE guild=$2", channel.id, ctx.guild.id)
            self.bot.logging[ctx.guild.id][1] = channel.id
            await ctx.send(f"Changed log channel to {channel.mention}")

    @logging.command(name="disable")
    async def disable_(self, ctx):
        """Disables logging on server"""
        
        if self.bot.logging[ctx.guild.id][0] is True:
            self.bot.logging[ctx.guild.id][0] = False
            async with ctx.db.acquire() as db:
                await db.execute("UPDATE settings SET logging=FALSE, logchannel=NULL WHERE guild=$1", ctx.guild.id)
            await ctx.send("Disabled logging for this server.")
        await ctx.send("Logging is already disabled.")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if self.bot.logging[message.guild.id][0] is True:
            embed = discord.Embed(color=message.author.color)
            embed.set_author(name=message.author, icon_url=message.author.avatar_url)
            embed.description = message.content
            if message.attachments:
                embed.set_image(url=message.attachments[0].url)
            embed.set_footer(text="Message deleted at")
            embed.timestamp = datetime.datetime.utcnow()
            await (self.bot.get_channel(self.bot.logging[message.guild.id][1])).send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if self.bot.logging[before.guild.id][0] is True:
            embed = discord.Embed(color=before.author.color)
            embed.set_author(name=before.author, icon_url=before.author)
            embed.title = "Before"
            embed.description = before.content
            embed.add_field(name="After", value=after.content, inline=False)
            embed.set_footer(text="Message edited at")
            embed.timestamp = datetime.datetime.utcnow()
            if before.attachments:
                embed.set_image(url=before.attachments[0].url)
            await (self.bot.get_channel(self.bot.logging[before.guild.id][1])).send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if self.bot.logging[before.guild.id][0] is True:
            if before.nick != after.nick:
                embed = discord.Embed(color=before.color)
                embed.set_author(name=before, icon_url=before.avatar_url)
                embed.title = "Before"
                embed.description = before.nick
                embed.add_field(name="After", value=after.nick, inline=False)
                embed.set_footer(text="Nickname changed at")
                embed.timestamp = datetime.datetime.utcnow()
                await (self.bot.get_channel(self.bot.logging[before.guild.id][1])).send(embed=embed)
            elif before.roles != after.roles:
                embed = discord.Embed(color=after.author.color)
                embed.set_author(name=before, icon_url=before.avatar_url)
                embed.title = "Before"
                embed.description = ", ".join([x.mention for x in before.roles])
                embed.add_field(name="After", value=", ".join([x.mention for x in after.roles]))
                embed.set_footer(text="Roles changed at")
                embed.timestamp = datetime.datetime.utcnow()
                await (self.bot.get_channel(self.bot.logging[before.guild.id][1])).send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        if self.bot.logging[role.guild.id][0] is True:
            embed = discord.Embed(color=role.color)
            embed.description = f"New Role {role.mention}"
            embed.add_field(name="Permissions", value="\n".join([x for (x, y) in role.permissions]))
            await (self.bot.get_channel(self.bot.logging[role.guild.id][1])).send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if self.bot.logging[role.guild.id][0] is True:
            embed = discord.Embed(color=role.color)
            embed.description = f"Deleted Role `{role.name}`"
            await (self.bot.get_channel(self.bot.logging[role.guild.id][1])).send(embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
