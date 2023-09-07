import asyncio
import emoji
import re
import typing

import discord
from discord.ext import commands
from discord.utils import MISSING

class UnicodeEmoji(commands.Converter):
    async def convert(self, ctx, argument):
        argument = emoji.emojize(emoji.demojize(argument))
        if argument in emoji.UNICODE_EMOJI["en"]:
            return discord.PartialEmoji(name=argument, animated=False)
        raise commands.BadArgument('Unknown emoji')

Emoji = typing.Union[discord.PartialEmoji, discord.Emoji, UnicodeEmoji]

class ReactionRoleView(discord.ui.View):
    def __init__(self, ctx, roles):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.roles = roles

        for role in roles:
            # Create a button for each role
            button = Button(style=discord.ButtonStyle.primary, label=role.name, custom_id=f"assign_role:{role.id}")
            self.add_item(button)

    async def on_button_click(self, interaction):
        if interaction.custom_id.startswith("assign_role:"):
            # Handle the button click event
            role_id = int(interaction.custom_id.split(":")[1])
            role = discord.utils.get(self.roles, id=role_id)
            member = interaction.user

            if role and role not in member.roles:
                await member.add_roles(role)
                await interaction.response.send_message(f"You've been assigned the {role.name} role!", ephemeral=True)
            elif role and role in member.roles:
                await member.remove_roles(role)
                await interaction.response.send_message(f"You've been removed from the {role.name} role!", ephemeral=True)


class rr(commands.Cog):
    """Assign roles to your members with Reactions"""

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.api.get_plugin_partition(self)

    @commands.group(name="reactionrole", aliases=["rr"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def reactionrole(self, ctx: commands.Context):
        """Assign roles to your members with Reactions"""
        await ctx.send_help(ctx.command)
        
    @reactionrole.command(name="add", aliases=["make"])
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def rr_add(self, ctx, message: str, role: discord.Role, emoji: Emoji,
                     ignored_roles: commands.Greedy[discord.Role] = None):
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

        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {emote: {"role": role.id, "msg_id": message.id, "ignored_roles": blacklist, "state": "unlocked"}}},
            upsert=True)

        await message.add_reaction(emoji)
        await ctx.send("Successfuly set the Reaction Role!")

    @reactionrole.command(name="remove", aliases=["delete"])
    @commands.has_permissions(administrator=True)
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
    @commands.has_permissions(administrator=True)
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

    @reactionrole.group(name="whitelist", invoke_without_command=True)
    async def rr_whitelist(self, ctx):
        """Manage the whitelist for reaction roles."""
        await ctx.send_help(ctx.command)
        
    @rr_whitelist.command(name="add")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def whitelist_add(self, ctx, emoji: Emoji, roles: commands.Greedy[discord.Role]):
        """Add roles to the whitelist for a reaction role."""
        emote = emoji.name if emoji.id is None else str(emoji.id)
        config = await self.db.find_one({"_id": "config"})
        valid, msg = self.valid_emoji(emote, config)
        if not valid:
            return await ctx.send(msg)
        
        whitelist = config[emote].get("whitelist", [])
        
        for role in roles:
            if role.id not in whitelist:
                whitelist.append(role.id)
        
        config[emote]["whitelist"] = whitelist
        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {emote: config[emote]}}, upsert=True)
        
        whitelist_mentions = [f"<@&{role_id}>" for role_id in whitelist]
        
        embed = discord.Embed(title="Successfully added roles to the whitelist.", color=discord.Color.green())
        try:
            embed.add_field(name=f"Current whitelist for {emoji}", value=" ".join(whitelist_mentions))
        except HTTPException:
            pass
        await ctx.send(embed=embed)
        
    @rr_whitelist.command(name="remove")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def whitelist_remove(self, ctx, emoji: Emoji, roles: commands.Greedy[discord.Role]):
        """Remove roles from the whitelist for a reaction role."""
        emote = emoji.name if emoji.id is None else str(emoji.id)
        config = await self.db.find_one({"_id": "config"})
        valid, msg = self.valid_emoji(emote, config)
        if not valid:
            return await ctx.send(msg)
        
        whitelist = config[emote].get("whitelist", [])
        
        for role in roles:
            if role.id in whitelist:
                whitelist.remove(role.id)
        
        config[emote]["whitelist"] = whitelist
        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {emote: config[emote]}}, upsert=True)
        
        whitelist_mentions = [f"<@&{role_id}>" for role_id in whitelist]
        
        embed = discord.Embed(title="Successfully removed roles from the whitelist.", color=discord.Color.green())
        try:
            embed.add_field(name=f"Current whitelist for {emoji}", value=" ".join(whitelist_mentions))
        except HTTPException:
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
            msg_id = None


        if msg_id and payload.message_id == int(msg_id):
            # Handle button interactions
            if payload.event_type == "MESSAGE_COMPONENT":
                if payload.custom_id.startswith("assign_role:"):
                    role_id = int(payload.custom_id.split(":")[1])
                    role = discord.utils.get(guild.roles, id=role_id)

                    if role:
                        if role in member.roles:
                            await member.remove_roles(role)
                            await member.send(f"You've been removed from the {role.name} role!")
                        else:
                            await member.add_roles(role)
                            await member.send(f"You've been assigned the {role.name} role!")
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
        
        whitelist = config[emote].get("whitelist", [])
        if whitelist:
            if not any(role.id in whitelist for role in member.roles):
                await self._remove_reaction(payload, emoji, member)
                return
        
        state = config[emote].get("state", "unlocked")
        if state and state == "locked":
            await self._remove_reaction(payload, emoji, member)
            return
        
        rrole = config[emote]["role"]
        role = discord.utils.get(guild.roles, id=int(rrole))

        if role:
            await member.add_roles(role)


    @reactionrole.group(name="list", invoke_without_command=True)
    async def rr_list(self, ctx):
        """List active reaction roles and their attributes."""
        config = await self.db.find_one({"_id": "config"})
        
        if not config:
            return await ctx.send("There are no active reaction roles.")
        
        embed = discord.Embed(title="Active Reaction Roles", color=discord.Color.blue())
        
        for emote, data in config.items():
            if emote == "_id":
                continue
            
            role_id = data.get("role")
            state = data.get("state", "unlocked")
            ignored_roles = data.get("ignored_roles", [])
            
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            
            if role:
                role_name = role.name
            else:
                role_name = "Role not found"
            
            if state == "locked":
                status = "Locked"
            else:
                status = "Unlocked"
                
            ignored_role_mentions = [f"<@&{role_id}>" for role_id in ignored_roles]
            ignored_roles_str = ", ".join(ignored_role_mentions) if ignored_roles else "None"
            
            embed.add_field(
                name=f"Reaction: {emote}",
                value=f"Role: {role_name}\nStatus: {status}\nIgnored Roles: {ignored_roles_str}",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
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

    @reactionrole.command(name="make", aliases=["menu"])
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)        
    async def rr_make(self, ctx):
        """
        Make a reaction role through interactive setup
        Note: You can only use the emoji once, you can't use the emoji multiple times.
        """

        # checks 
        def check(msg):
            return ctx.author == msg.author and ctx.channel == msg.channel

        def channel_check(msg):
            return check(msg) and len(msg.channel_mentions) != 0

        def emoji_and_role_check(msg):
            return check(msg) and (discord.utils.get(ctx.guild.roles, name=msg.content.strip()[1:].strip()) is not None)
        
        # getting the values (inputs) from the user
        await ctx.send("Alright! In which channel would you like the announcement to be sent? (Make sure to mention the channel)")
        try:
            channel_msg = await self.bot.wait_for("message", check=channel_check, timeout=30.0)
            channel = channel_msg.channel_mentions[0]
        except asyncio.TimeoutError:
            return await ctx.send("Too late! The reaction role is canceled.", delete_after=10.0)
        
        # Get the title and description from the user
        await ctx.send(f"Ok, so the channel is {channel.mention}. What do you want the message to be? Use | to separate the title "
                       "from the description\n **Example:** `This is my title. | This is my description!`")
        try:
            title_and_description = await self.bot.wait_for("message", check=check, timeout=120.0)
            title, description = map(str.strip, title_and_description.content.split("|", 1))
        except asyncio.TimeoutError:
            return await ctx.send("Too late! The reaction role is canceled.", delete_after=10.0)

        # Get the color from the user
        await ctx.send("Sweet! Would you like the message to have a color? Respond with a hex code if you'd like to, or if you don't, "
                       f"type `{ctx.prefix}none`\nConfused about what a hex code is? Check out https://htmlcolorcodes.com/color-picker/")
        
        valid_hex = False
        while not valid_hex:
            try:
                hex_code = await self.bot.wait_for("message", check=check, timeout=60.0)
                if hex_code.content.lower() == "none" or hex_code.content.lower() == f"{ctx.prefix}none":
                    color = self.bot.main_color
                    break
                valid_hex = re.search(r"^#(?:[0-9a-fA-F]{3}){1,2}$", hex_code.content)
            except asyncio.TimeoutError:
                return await ctx.send("Too late! The reaction role is canceled.", delete_after=10.0)
            if not valid_hex:
                embed = discord.Embed(description="""This doesn't seem like a valid Hex Code!
                                                   Please enter a **valid** [hex code](https://htmlcolorcodes.com/color-picker)""")
                await ctx.send(embed=embed)
            else:
                color = hex_code.content.replace("#", "0x")

        # Create and send the embed
        embed = discord.Embed(title=title, description=description, color=color)
        await ctx.send("Great! The embed should now look like this:", embed=embed)

        # Get roles from the user
        await ctx.send("The last step we need to do is picking the roles. The format for adding roles is the emoji then the name of "
                       f"the role. When you're done, type `{ctx.prefix}done`\n**Example:** `🎉 Giveaways`")
        emojis = []
        roles = []
        whitelist_mentions = [f"<@&{role_id}>" for role_id in whitelist]


        while True:
            try:
                emoji_and_role = await self.bot.wait_for("message", check=emoji_and_role_check, timeout=60.0)
            except asyncio.TimeoutError:
                return await ctx.send("Too late! The reaction role is canceled.", delete_after=10.0)
            else:
                if emoji_and_role.content.lower() == "done" or emoji_and_role.content.lower() == f"{ctx.prefix}done":
                    if len(roles) == 0:
                        await ctx.send("You need to specify at least 1 role for the reaction role.")
                    else:
                        break
                else:
                    emoji = emoji_and_role.content[0]
                    role = emoji_and_role.content[1:].strip()
                    emojis.append(emoji)
                    roles.append(role)
                  

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

        embed = discord.Embed(title="Successfully added roles to the whitelist!")
        embed.add_field(name="Roles Added:", value=", ".join(whitelist_mentions), inline=False)
        await ctx.send(embed=embed)

    @rr_whitelist.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def whitelist_remove(self, ctx, emoji: Emoji, roles: commands.Greedy[discord.Role]):
        """Remove roles from the whitelist for a reaction role."""
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
            msg_id = None

        if msg_id and payload.message_id == int(msg_id):
            # Handle button interactions
            if payload.event_type == "MESSAGE_COMPONENT":
                if payload.custom_id.startswith("assign_role:"):
                    role_id = int(payload.custom_id.split(":")[1])
                    role = discord.utils.get(guild.roles, id=role_id)

                    if role:
                        if role in member.roles:
                            await member.remove_roles(role)
                            await member.send(f"You've been removed from the {role.name} role!")
                        else:
                            await member.add_roles(role)
                            await member.send(f"You've been assigned the {role.name} role!")

            # Handle emoji reactions
            else:
                reaction_rule = config[emote].get("reaction_rule", "normal")  # Default to "normal"
                
                if reaction_rule == "unique":
                    # Handle the "unique" reaction rule (Only one reaction allowed)
                    for emote_key, data in config.items():
                        if emote_key != emote:
                            # Remove other reactions
                            await self._remove_reaction(payload, emote_key, member)

                ignored_roles = config[emote].get("ignored_roles")
                if ignored_roles:
                    for role_id in ignored_roles:
                        role = discord.utils.get(guild.roles, id=role_id)
                        if role in member.roles:
                            await self._remove_reaction(payload, emoji, member)
                            return

                whitelist = config[emote].get("whitelist", [])
                if whitelist:
                    if not any(role.id in whitelist for role in member.roles):
                        await self._remove_reaction(payload, emoji, member)
                        return

                state = config[emote].get("state", "unlocked")
                if state and state == "locked":
                    await self._remove_reaction(payload, emoji, member)
                    return
                    
        whitelist = config[emote].get("whitelist", [])

                rrole = config[emote]["role"]
                role = discord.utils.get(guild.roles, id=int(rrole))

                if role:
                    await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id is None:
            return
        for role in roles:
            if role.id in whitelist:
                whitelist.remove(role.id)

        config = await self.db.find_one({"_id": "config"})
        emote = payload.emoji.name if payload.emoji.id is None else str(payload.emoji.id)
        config[emote]["whitelist"] = whitelist
        
        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {emote: config[emote]}}, upsert=True)

        whitelist_mentions = [f"<@&{role_id}>" for role_id in whitelist]

        try:
            msg_id = config[emote]["msg_id"]
        except (KeyError, TypeError):
            msg_id = None
        embed = discord.Embed(title="Successfully removed roles from the whitelist!")
        embed.add_field(name="Roles Removed:", value=", ".join(whitelist_mentions), inline=False)
        await ctx.send(embed=embed)

    def valid_emoji(self, emote, config):
        if not config:
            return False, "No reaction roles found in the config."
        if emote not in config:
            return False, "This emoji is not set up as a reaction role."
        return True, ""
        if msg_id and payload.message_id == int(msg_id):
            # Handle emoji reactions
            if payload.event_type == "REACTION_REMOVE":
                guild = self.bot.get_guild(payload.guild_id)
                rrole = config[emote]["role"]
                role = discord.utils.get(guild.roles, id=int(rrole))

                if role:
                    member = discord.utils.get(guild.members, id=payload.user_id)
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
    await bot.add_cog(rr(bot))
