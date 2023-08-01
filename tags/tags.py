import discord
from datetime import datetime
from discord.ext import commands
from core import checks
from core.models import PermissionLevel
import json
from typing import Any, Dict, Union
from box import Box
from .models import apply_vars, SafeString

class TagSelectMenu(discord.ui.View):
    def __init__(self, tags):
        super().__init__()
        self.add_item(discord.ui.Select(
            placeholder='Select a tag category...',
            options=[discord.SelectOption(label=tag, value=tag) for tag in tags]
        ))

class TagsPlugin(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Client = bot
        self.db = bot.plugin_db.get_partition(self)
        self.categories = set()  # A set to store unique tag categories

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
        Make a new tag with a specified category
        """
        if (await self.find_db(name=name)) is not None:
            await ctx.send(f":x: | Tag with name `{name}` already exists!")
            return

        ctx.message.content = content
        await self.db.insert_one(
            {
                "name": name,
                "content": ctx.message.clean_content,
                "category": category,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow(),
                "author": ctx.author.id,
                "uses": 0,
            }
        )

        # Initialize the categories set if it doesn't exist yet
        if not self.categories:
            all_tags = await self.db.find({}).to_list(length=None)
            self.categories = set(tag['category'] for tag in all_tags)

        self.categories.add(category)  # Add the new category to the set of categories

        await ctx.send(
            f":white_check_mark: | Tag with name `{name}` and category `{category}` has been successfully created!"
        )
        return

    

    @tags.command(name='list')
    async def list_(self, ctx):
        '''Get a list of tags that have already been made.'''

        tags = await self.db.find({}).to_list(length=None)

        if tags is None:
            return await ctx.send(':x: | You don\'t have any tags.')
        
        list_tags = []

        for tag in tags:
            try:
                list_tags.append(tag['name'])
            except:
                continue

        send_tags = 'Tags: ' + ', '.join(list_tags)

        # Create the embed object
        embed = discord.Embed(title="Tag List", description=send_tags, color=None)

        # Send the embed object
        await ctx.send(embed=embed)

    # ... (your other commands)

    @tags.command()
    async def select(self, ctx: commands.Context):
        '''
        Select a tag category from the dropdown menu.
        '''

        tags = await self.db.find({}).to_list(length=None)

        if tags is None:
            return await ctx.send(':x: | You don\'t have any tags.')

        # Create and send the dropdown menu
        view = TagSelectMenu([tag['name'] for tag in tags])
        await ctx.send('Select a tag category:', view=view)

        # Wait for the user to make a selection
        interaction = await self.bot.wait_for('select_option', check=lambda i: i.user == ctx.author and i.component == view.children[0])

        selected_tag = interaction.values[0]
        await ctx.send(f'You selected the tag category: {selected_tag}')

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if not msg.content.startswith(self.bot.prefix) or msg.author.bot:
            return

        content = msg.content.replace(self.bot.prefix, "")
        names = content.split(" ")

        tag = await self.db.find_one({"name": names[0]})
        if tag is None:
            return
        else:
            await msg.channel.send("```" + tag["content"] + "```")
            await self.db.find_one_and_update(
                {"name": names[0]}, {"$set": {"uses": tag["uses"] + 1}}
            )
            return

    async def find_db(self, name: str):
        return await self.db.find_one({"name": name})


async def setup(bot):
    await bot.add_cog(TagsPlugin(bot))
