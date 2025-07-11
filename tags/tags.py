import json
import logging
import re
from typing import Any, TypedDict

import discord
from datetime import datetime
from discord.ext import commands
from discord import app_commands

from bot import ModmailBot
from core import checks
from core.models import PermissionLevel

logging = logging.getLogger(__name__)

# db schemas
class TagEntry(TypedDict):
    name: str
    content: str
    createdAt: datetime
    updatedAt: datetime
    author: int
    uses: int
    category: str


class CategoryEntry(TypedDict):
    category: str


class TagsPlugin(commands.Cog):
    def __init__(self, bot: ModmailBot):
        self.bot = bot
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
        # Check if the content starts and ends with triple backticks
        code_block_match = re.match(r"```(.*?)\n(.*?)```", content, re.DOTALL)

        if code_block_match:
            content = code_block_match.group(2)
            try:
                json.loads(content)
            except json.JSONDecodeError:
                await ctx.send(f":x: | The provided content is not valid JSON or JavaScript.")
                return

        # Save the tag to the database
        await self.db.insert_one(
            {
                "name": name,
                "content": content,
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


    @tags.command(name='list')
    async def list_(self, ctx):
        """Get a list of tags that have already been made."""
        tags = await self.db.find({}).to_list(length=None)

        if not tags:
            return await ctx.send(':x: | You don\'t have any tags.')

        embed = discord.Embed(title="Tag List", color=None)

        tags_by_category = {}
        for tag in tags:
            category = tag.get('category', 'Unidentified')
            tag_name = tag.get('name', 'No Name')


            if category not in tags_by_category:
                tags_by_category[category] = []

            if tag_name != 'No Name':
                tags_by_category[category].append(tag_name)

        sorted_categories = sorted(tags_by_category.keys())  # Sort categories alphabetically

        for category in sorted_categories:  # Iterate through sorted categories
            tag_names = sorted(tags_by_category[category])  # Sort the tag_names in alphabetical order
            tags_list_str = ", ".join(tag_names)
            embed.add_field(name=f"{category} Tags", value=tags_list_str, inline=False)

        await ctx.send(embed=embed)

    @tags.command(name='delete_category')
    async def delete_category(self, ctx: commands.Context, category: str):
        """
        Delete a category
        """
        tags_to_update = []

        async for tag in self.db.find({"category": category}):
            if 'name' in tag:
                tags_to_update.append(tag)

        for tag in tags_to_update:
            await self.db.find_one_and_update(
                {"_id": tag["_id"]},
                {"$set": {"category": "Unidentified"}},
            )

        await self.db.delete_many({"category": category})

        await ctx.send(f":white_check_mark: | Deleted category '{category}' and moved its tags to 'Unidentified'.")





    @tags.command()
    async def edit(self, ctx: commands.Context, name: str, category: str, *, content: str):
        """
        Edit an existing tag
        Only the owner of the tag or a user with Manage Server permissions can use this command
        """
        tag = await self.find_db(name=name)
        # Check if the content starts and ends with triple backticks
        code_block_match = re.match(r"```(.*?)\n(.*?)```", content, re.DOTALL)

        if code_block_match:
            # If it's a code block, treat it as JavaScript code
            content = code_block_match.group(2)
            try:
                eval(content, {"discord": discord, "datetime": datetime})
            except Exception as e:
                await ctx.send(f":x: | The provided content is not valid JavaScript. Error: {str(e)}")
                return
        else:
            # If it's not a code block, try to parse it as JSON
            try:
                json.loads(content)
            except json.JSONDecodeError:
                await ctx.send(":x: | The provided content is not valid JSON or JavaScript.")
                return

        if not tag:
            await ctx.send(f":x: | Tag `{name}` not found in the database.")
            return

        member: discord.Member = ctx.author

        if ctx.author.id == tag.get("author") or member.guild_permissions.manage_guild:
            updated_fields = {"content": content, "updatedAt": datetime.utcnow()}
            if category != tag.get("category"):
                updated_fields["category"] = category

            await self.db.find_one_and_update(
                {"name": name},
                {"$set": updated_fields},
            )

            await ctx.send(
                f":white_check_mark: | Tag `{name}` is updated successfully in the category `{category}`!"
            )
        else:
            await ctx.send("You don't have enough permissions to edit that tag")


    @tags.command()
    async def edit_category(self, ctx: commands.Context, category_name: str, new_category: str):
        """
        Edit an existing Category Name
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

        try:
            content = json.loads(tag["content"])  # Attempt to parse content as JSON
        except json.JSONDecodeError:
            content = tag["content"]

        # Check if the tag has "embed_type" field and it contains "js"
        if "embed_type" in tag and "js" in tag["embed_type"]:
            try:
                # Evaluate the JavaScript code and convert the result to a dict
                content = eval(content, {"discord": discord, "datetime": datetime})
                if not isinstance(content, dict):
                    raise ValueError("JavaScript code must return a dictionary for the embed.")
            except Exception as e:
                await ctx.send(f":x: | Error while evaluating JavaScript: {str(e)}")
                return
        else:
            if ctx.prefix == '?':
                # If command is ?tagname, send raw JSON content as a code block
                formatted_json = json.dumps(content, indent=4)
                await ctx.send(f"```json\n{formatted_json}\n```")
            else:
                # If command is ?tag tagname, treat content as an embed
                embed = discord.Embed.from_dict(content)
                await ctx.send(embed=embed)

            await self.db.find_one_and_update(
                {"name": name}, {"$set": {"uses": tag["uses"] + 1}}
            )

            return

        # Format content as JSON
        formatted_json = json.dumps(content, indent=4)

        # Check if the content exceeds 2000 characters
        if len(formatted_json) > 2000:
            # Content exceeds limit, send as a file
            with open("tag_content.json", "w") as file:
                file.write(formatted_json)
            await ctx.send(file=discord.File("tag_content.json"))
        else:
            # Content within limit, send as a code block
            await ctx.send(f"```json\n{formatted_json}\n```")



        # If content is a dictionary (valid JSON or JavaScript-generated)
        if isinstance(content, dict):
            embed = discord.Embed.from_dict(content)
            await ctx.send(embed=embed)
            await self.db.find_one_and_update(
                {"name": name}, {"$set": {"uses": tag["uses"] + 1}}
            )
        else:
            await ctx.send(":x: | Invalid JSON or JavaScript-generated embed content.")

    @tags.command()
    async def move_category(self, ctx: commands.Context, new_category: str, *tag_names: str):
        """
        Move one or more tags to a specific category.
        """
        moved_tags = []
        failed_tags = []

        for name in tag_names:
            tag = await self.find_db(name=name)
            if tag is None:
                failed_tags.append(name)
                continue

            updated_tag = await self.db.find_one_and_update(
                {"name": name}, {"$set": {"category": new_category}}
            )

            if updated_tag:
                moved_tags.append(name)
            else:
                failed_tags.append(name)

        response = ""

        if moved_tags:
            response += f":white_check_mark: | Moved tags `{', '.join(moved_tags)}` to category `{new_category}`!\n"

        if failed_tags:
            response += f":x: | Failed to move tags `{', '.join(failed_tags)}` to category `{new_category}`.\n"

        await ctx.send(response.strip())


    @tags.command()
    async def create_category(self, ctx: commands.Context, category_name: str):
        """
        Create a new category for tags.
        """
        existing_category = await self.db.find_one({"category": category_name})
        if existing_category:
            await ctx.send(f":x: | Category `{category_name}` already exists.")
            return

        await self.db.insert_one({"category": category_name})
        await ctx.send(f":white_check_mark: | Category `{category_name}` has been created!")

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        # if msg.content.startswith("Please set your Nightscout") and msg.author.bot:
        #     await ctx.send("If you'd like to learn more about Nightscout, type `?nightscout`.")
        #     return
        if not msg.content.startswith(self.bot.prefix) or msg.author.bot:
            return

        content = msg.content.replace(self.bot.prefix, "")
        names = content.split(" ")

        try:
            embed = await self.get_tag_embed(names[0])
        except json.JSONDecodeError:
            await msg.channel.send("Error: The content of this tag is not valid JSON.")
            return
        if not embed:
            return

        await msg.channel.send(embed=embed)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        logging.error("Interaction %s failed", interaction, exc_info=error)

    @app_commands.command(name="tag", description="Get details about a tag")
    @app_commands.describe(
        name='Tag name'
    )
    @commands.guild_only()
    async def tags_slash(self, interaction: discord.Interaction, name: str):
        try:
            embed = await self.get_tag_embed(name)
        except json.JSONDecodeError:
            logging.error("Tag '%s' has invalid JSON content", name, exc_info=True)
            await interaction.response.send_message(
                "Error: The content of this tag is not valid JSON."
            )
            return
        if not embed:
            await interaction.response.send_message(
                f"Tag `{name}` was not found.", ephemeral=True
            )
            return

        await interaction.response.send_message(embed=embed)

    @tags_slash.autocomplete("name")
    async def tag_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        emoji_regex = re.compile(r"<a?:(\w+):(\d{18})>")
        def extract_display_name(tag: TagEntry) -> str:
            """Extract the display name from a tag entry's embed, or the tag name if missing."""
            try:
                content = json.loads(tag["content"])
                title = content.get("embed", {}).get("title", None)
                if title:
                    # clean embed title; remove markdown
                    title = discord.utils.remove_markdown(title)
                    # remove emotes/emojis
                    title = emoji_regex.sub("", title).strip()

                if 0 < len(title or "") < 50:
                    title = tag["name"] + " | " + title
                else:
                    # title was too long or nonexistent
                    title = tag["name"]
                return title
            except json.JSONDecodeError:
                logging.error("Extracting display name failed on tag '%s' due to JSON error", tag, exc_info=True)
                return tag["name"]
            except Exception:
                logging.error("Extracting display name failed on tag '%s'", tag, exc_info=True)
                return tag["name"]

        tags: list[TagEntry] = await self.db.find(
            {
                "name": {
                    "$regex": fr"{current}",
                    "$options": 'i',
                }
            }
        ).to_list(length=None)

        return [
            app_commands.Choice(name=extract_display_name(tag)[:100], value=tag["name"])
            for tag in tags[:25]
        ]

    async def get_tag_embed(self, name: str, add_use: bool = True) -> discord.Embed | None:
        tag = await self.find_db(name)
        if tag is None:
            return None

        content = json.loads(tag["content"])
        embed = discord.Embed.from_dict(content["embed"])
        if add_use:
            await self.db.find_one_and_update(
                {"name": name}, {"$set": {"uses": tag["uses"] + 1}}
            )
        return embed

    async def find_db(self, name: str) -> TagEntry | None:
        return await self.db.find_one({"name": name})


async def setup(bot: ModmailBot):
    await bot.add_cog(TagsPlugin(bot))

    cmds = await bot.tree.sync()
    for g in bot.guilds:
        await bot.tree.sync(guild=g)
    logging.error(f"Synced {len(cmds)} commands")