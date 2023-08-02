import json
from typing import Any, Dict, Union

import discord
from datetime import datetime
from discord.ext import commands
from box import Box
from core import checks
from core.models import PermissionLevel
from .models import apply_vars, SafeString


class TagsPlugin(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.db = bot.plugin_db.get_partition(self)
        
    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def tags(self, ctx: commands.Context):
        """
        Create Edit & Manage Tags
        """
        await ctx.send_help(ctx.command)

    @tags.command()
    async def add(self, ctx: commands.Context, name: str, category: str, *, content: str):
        """
        Make a new tag
        """
        if (await self.find_db(name=name)) is not None:
            await ctx.send(f":x: | Tag with name `{name}` already exists!")
            return
        else:
            try:
                json.loads(content)  # Attempt to parse content as JSON
            except json.JSONDecodeError:
                await ctx.send(":x: | The provided content is not valid JSON.")
                return

            ctx.message.content = content
            await self.db.insert_one(
                {
                    "name": name,
                    "content": ctx.message.clean_content,
                    "createdAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow(),
                    "author": ctx.author.id,
                    "uses": 0,
                    "category": category,
                }
            )

            await ctx.send(
                f":white_check_mark: | Tag with name `{name}` has been successfully created in the category `{category}`!"
            )
            return
        
    @tags.command(name='list')
    async def list_(self, ctx):
        '''Get a list of tags that have already been made.'''

        tags = await self.db.find({}).to_list(length=None)

        if not tags:
            return await ctx.send(':x: | You don\'t have any tags.')

        embed = discord.Embed(title="Tag List", color=None)

        tags_by_category = {}
        for tag in tags:
            category = tag.get('category', 'Unidentified')
            if category not in tags_by_category:
                tags_by_category[category] = []
            tags_by_category[category].append(tag['name'])

        for category, tag_names in tags_by_category.items():
            tags_list_str = ", ".join(tag_names)
            embed.add_field(name=f"{category} Tags", value=tags_list_str, inline=False)

        # Send the embed object
        await ctx.send(embed=embed)
   



    @tags.command()
    async def edit(self, ctx: commands.Context, name: str, category: str, *, content: str):
        """
        Edit an existing tag
        Only owner of tag or user with Manage Server permissions can use this command
        """
        tag = await self.find_db(name=name)

        if tag is None:
            await ctx.send(f":x: | Tag with name `{name}` does not exist")
            return
        else:
            try:
                json.loads(content)  # Attempt to parse content as JSON
            except json.JSONDecodeError:
                await ctx.send(":x: | The provided content is not valid JSON.")
                return

            member: discord.Member = ctx.author
            if ctx.author.id == tag["author"] or member.guild_permissions.manage_guild:
                await self.db.find_one_and_update(
                    {"name": name},
                    {"$set": {"content": content, "updatedAt": datetime.utcnow(), "category": category}},
                )

                await ctx.send(
                    f":white_check_mark: | Tag `{name}` is updated successfully in the category `{category}`!"
                )
            else:
                await ctx.send("You don't have enough permissions to edit that tag")

    @tags.command()
    async def edit_category(self, ctx: commands.Context, category_name: str, new_category: str):
        """
        Edit the category of tags with the specified category_name to the new_category
        Only the owner of the tag or a user with Manage Server permissions can use this command
        """
        member: discord.Member = ctx.author
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("You don't have enough permissions to edit the category of tags.")
            return

        tags_to_update = await self.db.find({"category": category_name}).to_list(length=None)

        if not tags_to_update:
            await ctx.send(f":x: | Category `{category_name}` does not exist or has no tags.")
            return

        for tag in tags_to_update:
            await self.db.find_one_and_update(
                {"name": tag["name"]},
                {"$set": {"category": new_category}},
            )

        await ctx.send(
            f":white_check_mark: | Category of all tags with category `{category_name}` has been updated to `{new_category}`!"
        )

    @tags.command()
    async def delete(self, ctx: commands.Context, name: str):
        """
        Delete a tag.
        Only owner of tag or user with Manage Server permissions can use this command
        """
        tag = await self.find_db(name=name)
        if tag is None:
            await ctx.send(f":x: | Tag `{name}` not found in the database.")
        else:
            if (
                ctx.author.id == tag["author"]
                or ctx.author.guild_permissions.manage_guild
            ):
                await self.db.delete_one({"name": name})

                await ctx.send(
                    f":white_check_mark: | Tag `{name}` has been deleted successfully!"
                )
            else:
                await ctx.send("You don't have enough permissions to delete that tag")

    @tags.command()
    async def claim(self, ctx: commands.Context, name: str):
        """
        Claim a tag if the user has left the server
        """
        tag = await self.find_db(name=name)

        if tag is None:
            await ctx.send(f":x: | Tag `{name}` not found.")
        else:
            member = await ctx.guild.get_member(tag["author"])
            if member is not None:
                await ctx.send(
                    f":x: | The owner of the tag is still in the server `{member.name}#{member.discriminator}`"
                )
                return
            else:
                await self.db.find_one_and_update(
                    {"name": name},
                    {"$set": {"author": ctx.author.id, "updatedAt": datetime.utcnow()}},
                )

                await ctx.send(
                    f":white_check_mark: | Tag `{name}` is now owned by `{ctx.author.name}#{ctx.author.discriminator}`"
                )

    @tags.command()
    async def info(self, ctx: commands.Context, name: str):
        """
        Get info on a tag
        """
        tag = await self.find_db(name=name)

        if tag is None:
            await ctx.send(f":x: | Tag `{name}` not found.")
        else:
            user: discord.User = await self.bot.fetch_user(tag["author"])
            embed = discord.Embed()
            embed.colour = discord.Colour.green()
            embed.title = f"{name}'s Info"
            embed.add_field(
                name="Created By", value=f"{user.name}#{user.discriminator}"
            )
            embed.add_field(name="Created At", value=tag["createdAt"])
            embed.add_field(
                name="Last Modified At", value=tag["updatedAt"], inline=False
            )
            embed.add_field(name="Uses", value=tag["uses"], inline=False)
            await ctx.send(embed=embed)
            return

    @commands.command()
    async def tag(self, ctx: commands.Context, name: str):
        
        """
        Use a tag!
        """
        tag = await self.find_db(name=name)
        if tag is None:
            await ctx.send(f":x: | Tag {name} not found.")
            return
        else:
            await ctx.send("```" + tag["content"] + "```")
            await self.db.find_one_and_update(
                {"name": name}, {"$set": {"uses": tag["uses"] + 1}}
            )
            return

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.content.startswith("Please set your Nightscout") and msg.author.bot:
            await ctx.send("If you'd like to learn more about Nightscout, type `?nightscout`.")
            return
        if not msg.content.startswith(self.bot.prefix) or msg.author.bot:
            return
        
        content = msg.content.replace(self.bot.prefix, "")
        names = content.split(" ")

        tag = await self.db.find_one({"name": names[0]})
        thing = json.loads(tag["content"])
        embed = discord.Embed.from_dict(thing['embed'])
        if tag is None:
            return
        else:
            
            
            
            await msg.channel.send(embed=embed)
            await self.db.find_one_and_update(
                {"name": names[0]}, {"$set": {"uses": tag["uses"] + 1}}
            )
            return

    async def find_db(self, name: str):
        return await self.db.find_one({"name": name})


async def setup(bot):
    await bot.add_cog(TagsPlugin(bot))