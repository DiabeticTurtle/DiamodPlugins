from discord.ext import commands
from discord import TextChannel
from datetime import datetime, timedelta

class ArtPrompts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.prompts = ["Draw a portrait of your favorite character", "Paint a landscape of your favorite place", "Create a collage of your favorite memories"]
        self.prompt_channel_id = None

    def get_next_prompt(self):
        # get the current date and time
        current_time = datetime.now()

        # get the time for the next prompt (every 24 hours)
        next_prompt_time = current_time + timedelta(hours=24)

        # get the index of the next prompt
        next_prompt_index = next_prompt_time.day % len(self.prompts)

        # get the next prompt
        next_prompt = self.prompts[next_prompt_index]

        return next_prompt

    @commands.Cog.listener()
    async def on_message(self, message):
        # check if the message is in the prompt channel
        if message.channel.id == self.prompt_channel_id:
            # get the next prompt
            next_prompt = self.get_next_prompt()

            # send the next prompt to the channel
            await message.channel.send(next_prompt)

    @commands.command()
    async def set_prompt_channel(self, ctx, channel: discord.TextChannel):
        self.prompt_channel_id = channel.id
        await ctx.send(f"Art prompt channel set to {channel.mention}")

async def setup(bot):
    await bot.add_cog(ArtPrompts(bot))
