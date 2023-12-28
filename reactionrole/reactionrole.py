import asyncio
import emoji
import re
import typing

import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

class UnicodeEmoji(commands.Converter):
    async def convert(self, ctx, argument):
        argument = emoji.emojize(emoji.demojize(argument))
        if argument in emoji.UNICODE_EMOJI["en"]:
            return discord.PartialEmoji(name=argument, animated=False)
        raise commands.BadArgument('Unknown emoji')

Emoji = typing.Union[discord.PartialEmoji, discord.Emoji, UnicodeEmoji]

class reactionrole(commands.Cog):
    """Assign roles to your members with Reactions"""

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.api.get_plugin_partition(self)
        
    @commands.group(name="reactionrole", aliases=["rr"], invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def reactionrole(self, ctx: commands.Context):
        """Assign roles to your members with Reactions"""
        await ctx.send_help(ctx.command)
        
    @reactionrole.command(name="add", aliases=["create"])
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def rr_add(self, ctx, message: str, role: discord.Role, emoji: Emoji,
                     ignored_roles: commands.Greedy[discord.Role] = None, whitelist_roles: commands.Greedy[discord.Role] = None):
        """
        Sets up the reaction role.
        - Note(s):
        You can only use the emoji once, you can't use the emoji multiple times.
        - Usage:
        Send message in any channel visible to the bot, copy MESSAGE_ID, and use command
        {prefix}reactionrole add MESSAGE_ID "role name" :unique_emoji:
        
        [To copy MESSAGE_ID you need to enable Developer Mod in User Settings]
        """
        emote = emoji.name if emoji.id is None else str(emoji.id)
        message_id = int(message.split("/")[-1])
        
        for channel in ctx.guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
            except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                message = None
                continue
            else:
                break
                
        if not message:
            return await ctx.send("Message could not be found.")
        
        if ignored_roles:
            blacklist = [role.id for role in ignored_roles]
        else:
            blacklist = []

        if whitelist_roles:
            whitelist = [role.id for role in whitelist_roles]
        else:
            whitelist = []

            
        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {emote: {"role": role.id, "msg_id": message.id, "ignored_roles": blacklist, "whitelist_roles": whitelist, "state": "unlocked"}}},
            upsert=True)
        
        await message.add_reaction(emoji)
        await ctx.send("Successfuly set the Reaction Role!")
    @reactionrole.command(name="list")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def rr_list(self, ctx):
        """List all reaction roles with their attributes."""
        config = await self.db.find_one({"_id": "config"})
    
        if not config:
            return await ctx.send("No reaction roles are configured.")
    
        embed = discord.Embed(title="List of Reaction Roles", color=discord.Color.blue())
    
        for emote, data in config.items():
            role = ctx.guild.get_role(data["role"])
        
            if not role:
                continue
        
            whitelist = data.get("whitelist_roles", [])
            ignored = data.get("ignored_roles", [])
        
            description = f"Role: {role.mention}\nWhitelisted Roles: {', '.join([ctx.guild.get_role(r).mention for r in whitelist])}\nIgnored Roles: {', '.join([ctx.guild.get_role(r).mention for r in ignored])}"
        
            embed.add_field(name=f"Reaction: {emote}", value=description, inline=False)
    
        await ctx.send(embed=embed)    
    @reactionrole.command(name="remove", aliases=["delete"])
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def rr_remove(self, ctx, emoji: Emoji):
        """Delete something from the reaction role."""
        emote = emoji.name if emoji.id is None else str(emoji.id)
        config = await self.db.find_one({"_id": "config"})
        
        valid, msg = self.valid_emoji(emote, config)
        if not valid:
            return await ctx.send(msg)
            
        await self.db.find_one_and_update({"_id": "config"}, {"$unset": {emote: ""}})
        await ctx.send("Successfully removed the role from the reaction role.")
        
    @reactionrole.command(name="lock", aliases=["pause", "stop"])
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def rr_lock(self, ctx, emoji: Emoji):
        """
        Lock a reaction role to disable it temporarily.
         - Example(s):
        `{prefix}rr lock 👀`
        """
        emote = emoji.name if emoji.id is None else str(emoji.id)
        config = await self.db.find_one({"_id": "config"})
        
        valid, msg = self.valid_emoji(emote, config)
        if not valid:
            return await ctx.send(msg)
        
        config[emote]["state"] = "locked"
        
        await self.db.find_one_and_update(
        {"_id": "config"}, {"$set": {emote: config[emote]}}, upsert=True)
        await ctx.send("Succesfully locked the reaction role.")
        
    @reactionrole.command(name="unlock", aliases=["resume"])
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def rr_unlock(self, ctx, emoji: Emoji):
        """
        Unlock a disabled reaction role.
         - Example(s):
        `{prefix}rr unlock 👀`
        """
        emote = emoji.name if emoji.id is None else str(emoji.id)
        config = await self.db.find_one({"_id": "config"})
        
        valid, msg = self.valid_emoji(emote, config)
        if not valid:
            return await ctx.send(msg)

        config[emote]["state"] = "unlocked"
        
        await self.db.find_one_and_update(
        {"_id": "config"}, {"$set": {emote: config[emote]}}, upsert=True)
        await ctx.send("Succesfully unlocked the reaction role.")
            
    @reactionrole.command(name="make")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def rr_make(self, ctx):
        """Make a reaction role through interactive setup."""
    
        def check(msg):
            return ctx.author == msg.author and ctx.channel == msg.channel

        await ctx.send("Alright! In which channel would you like the announcement to be sent? (Make sure to mention the channel)")
    
        try:
            channel_msg = await self.bot.wait_for("message", check=check, timeout=30.0)
            channel = channel_msg.channel_mentions[0]
        except asyncio.TimeoutError:
            return await ctx.send("Too late! The reaction role setup is canceled.", delete_after=10.0)
    
        await ctx.send("Ok, now what message would you like to use for the reaction role?")
    
        try:
            message_content = await self.bot.wait_for("message", check=check, timeout=120.0)
        except asyncio.TimeoutError:
            return await ctx.send("Too late! The reaction role setup is canceled.", delete_after=10.0)
    
        # Create the message and add it to the specified channel
        message = await channel.send(message_content.content)
    
        await ctx.send("Great! Now, let's set up the reaction roles on this message.")
        await ctx.send("Please mention the roles you want to associate with emojis in the format: `<@&RoleName>` followed by the emoji.")
        await ctx.send("For example: `@RoleName1 :emoji1: @RoleName2 :emoji2:`")
    
        try:
            roles_msg = await self.bot.wait_for("message", check=check, timeout=300.0)
        except asyncio.TimeoutError:
            return await ctx.send("Too late! The reaction role setup is canceled.", delete_after=10.0)
    
        roles_and_emojis = re.findall(r'<@&(\d+)> :([^:\s]+):', roles_msg.content)
    
        if not roles_and_emojis:
            return await ctx.send("No valid roles and emojis were found. The reaction role setup is canceled.")
    
        for role_id, emoji_name in roles_and_emojis:
            role = discord.utils.get(ctx.guild.roles, id=int(role_id))
            emoji = await UnicodeEmoji().convert(ctx, emoji_name)
        
            if role and emoji:
                await self.rr_add(ctx, f"message/{message.id}", role, emoji)
    
        await ctx.send("Reaction roles have been set up on the message successfully!")

                  

    @reactionrole.group(name="blacklist", aliases=["ignorerole"], invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def blacklist(self, ctx):
        """Ignore certain roles from reacting on a reaction role."""
        await ctx.send_help(ctx.command)
        
    @blacklist.command(name="add")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def blacklist_add(self, ctx, emoji: Emoji, roles: commands.Greedy[discord.Role]):
        """Ignore certain roles from reacting."""
        emote = emoji.name if emoji.id is None else str(emoji.id)
        config = await self.db.find_one({"_id": "config"})
        valid, msg = self.valid_emoji(emote, config)
        if not valid:
            return await ctx.send(msg)
        
        blacklisted_roles = config[emote]["ignored_roles"] or []
        
        new_blacklist = [role.id for role in roles if role.id not in blacklisted_roles]
        blacklist = blacklisted_roles + new_blacklist
        config[emote]["ignored_roles"] = blacklist
        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {emote: config[emote]}}, upsert=True)
        
        ignored_roles = [f"<@&{role}>" for role in blacklist]
        
        embed = discord.Embed(title="Successfully blacklisted the roles.", color=discord.Color.green())
        try:
            embed.add_field(name=f"Current ignored roles for {emoji}", value=" ".join(ignored_roles))
        except HTTPException:
            pass
        await ctx.send(embed=embed)
        
    @blacklist.command(name="remove")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def blacklist_remove(self, ctx, emoji: Emoji, roles: commands.Greedy[discord.Role]):
        """Allow certain roles to react on a reaction role they have been blacklisted from."""
        emote = emoji.name if emoji.id is None else str(emoji.id)
        config = await self.db.find_one({"_id": "config"})
        valid, msg = self.valid_emoji(emote, config)
        if not valid:
            return await ctx.send(msg)
        
        blacklisted_roles = config[emote]["ignored_roles"] or []
        blacklist = blacklisted_roles.copy()
        
        [blacklist.remove(role.id) for role in roles if role.id in blacklisted_roles]
        config[emote]["ignored_roles"] = blacklist
        
        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {emote: config[emote]}}, upsert=True)
        
        ignored_roles = [f"<@&{role}>" for role in blacklist]
        
        embed = discord.Embed(title="Succesfully removed the roles.", color=discord.Color.green())
        try:
            embed.add_field(name=f"Current ignored roles for {emoji}", value=" ".join(ignored_roles))
        except:
            pass
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.guild_id:
            return
        
        config = await self.db.find_one({"_id": "config"})
        
        emote = payload.emoji.name if payload.emoji.id is None else str(payload.emoji.id)
        emoji = payload.emoji.name if payload.emoji.id is None else payload.emoji
        
        guild = self.bot.get_guild(payload.guild_id)
        member = discord.utils.get(guild.members, id=payload.user_id)
        
        if member.bot:
            return
        
        try:
            msg_id = config[emote]["msg_id"]
        except (KeyError, TypeError):
            return
        
        if payload.message_id != int(msg_id):
            return
        
        ignored_roles = config[emote].get("ignored_roles")
        if ignored_roles:
            for role_id in ignored_roles:
                role = discord.utils.get(guild.roles, id=role_id)
                if role in member.roles:
                    await self._remove_reaction(payload, emoji, member)
                    return
        
        state = config[emote].get("state", "unlocked")
        if state and state == "locked":
            await self._remove_reaction(payload, emoji, member)
            return
        
        if payload.channel_id != payload.guild_id:  # If in a thread
            thread = self.bot.get_channel(payload.channel_id)
            try:
                message = await thread.fetch_message(payload.message_id)
            except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                return
        else:  # If not in a thread, it's a regular channel
            channel = self.bot.get_channel(payload.channel_id)
            try:
                message = await channel.fetch_message(payload.message_id)
            except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                return    
        
        rrole = config[emote]["role"]
        role = discord.utils.get(guild.roles, id=int(rrole))

        if role:
            # Check if the member has any role in the whitelist
            whitelist_roles = config[emote].get("whitelist_roles", [])  # Get the whitelist roles for this emoji
            has_whitelist_role = any(role.id in whitelist_roles for role in member.roles)

            if has_whitelist_role:
                await member.add_roles(role)
            else:
                await self._remove_reaction(payload, emoji, member)

        if payload.channel_id != payload.guild_id:  # If in a thread
            thread = self.bot.get_channel(payload.channel_id)
            try:
                message = await thread.fetch_message(payload.message_id)
            except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                return
        else:  # If not in a thread
            channel = self.bot.get_channel(payload.channel_id)
            try:
                message = await channel.fetch_message(payload.message_id)
            except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                return

    @reactionrole.command(name="whitelista")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def whitelist_add(self, ctx, emoji: Emoji, roles: commands.Greedy[discord.Role]):
        """Allow certain roles to react on a reaction role."""
        emote = emoji.name if emoji.id is None else str(emoji.id)
        config = await self.db.find_one({"_id": "config"})
        valid, msg = self.valid_emoji(emote, config)
        if not valid:
            return await ctx.send(msg)

        whitelist_roles = config[emote].get("whitelist_roles") or []
        new_whitelist = [role.id for role in roles if role.id not in whitelist_roles]
        whitelist = whitelist_roles + new_whitelist
        config[emote]["whitelist_roles"] = whitelist
        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {emote: config[emote]}}, upsert=True)

        whitelisted_roles = [f"<@&{role}>" for role in whitelist]

        embed = discord.Embed(title="Successfully whitelisted the roles.", color=discord.Color.green())
        try:
            embed.add_field(name=f"Current whitelisted roles for {emoji}", value=" ".join(whitelisted_roles))
        except HTTPException:
            pass
        await ctx.send(embed=embed)

    @reactionrole.command(name="whitelistr")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def whitelist_remove(self, ctx, emoji: Emoji, roles: commands.Greedy[discord.Role]):
        """Remove certain roles from the whitelist."""
        emote = emoji.name if emoji.id is None else str(emoji.id)
        config = await self.db.find_one({"_id": "config"})
        valid, msg = self.valid_emoji(emote, config)
        if not valid:
            return await ctx.send(msg)

        whitelist_roles = config[emote].get("whitelist_roles") or []
        whitelist = whitelist_roles.copy()

        [whitelist.remove(role.id) for role in roles if role.id in whitelist_roles]
        config[emote]["whitelist_roles"] = whitelist

        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {emote: config[emote]}}, upsert=True)

        whitelisted_roles = [f"<@&{role}>" for role in whitelist]

        embed = discord.Embed(title="Successfully removed roles from the whitelist.", color=discord.Color.green())
        try:
            embed.add_field(name=f"Current whitelisted roles for {emoji}", value=" ".join(whitelisted_roles))
        except:
            pass
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id is None:
            return
        config = await self.db.find_one({"_id": "config"})
        emote = payload.emoji.name if payload.emoji.id is None else str(payload.emoji.id)
        try:
            msg_id = config[emote]["msg_id"]
        except (KeyError, TypeError):
            return
        
        if payload.message_id != int(msg_id):
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = discord.utils.get(guild.members, id=payload.user_id)

        if member and member.bot:
            return

        rrole = config[emote]["role"]
        role = discord.utils.get(guild.roles, id=int(rrole))

        if role:
            await member.remove_roles(role)
                
    async def _remove_reaction(self, payload, emoji, member):
        channel = self.bot.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        reaction = discord.utils.get(msg.reactions, emoji=emoji)
        await reaction.remove(member)
                                  
    def valid_emoji(self, emoji, config):
        try:
            emoji = config[emoji]
            return True, None
        except (KeyError, TypeError):
            return False, "There's no reaction role set with this emoji!"
                
async def setup(bot):
   await bot.add_cog(reactionrole(bot))