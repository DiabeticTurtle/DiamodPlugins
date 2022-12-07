from discord.ext import commands
from discord import TextChannel
import asyncio
import random

class ArtPrompts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.prompt_channel_id = None

    @commands.Cog.listener()
    async def on_message(self, message):
        print(message.content)

    @commands.command()
    async def diabetesart(self, ctx):
        # Generate a random diabetes-related art prompt
        prompts = [
            "Create a portrait of someone living with diabetes",
            "Illustrate a scene from a day in the life of a person with diabetes",
            "Design a poster promoting diabetes awareness and education",
            "Draw a picture of a diabetes-friendly meal",
            "Paint a landscape that represents the emotional journey of living with diabetes"
        ]

        # Select a random art prompt from the list
        prompt = prompts[random.randint(0, len(prompts) - 1)]

        # Send the selected art prompt to the user
        await ctx.send(prompt)

    @commands.command()
    async def set_prompt_channel(self, ctx, channel: TextChannel):
        # Set the ID of the channel where the art prompts should be sent
        self.prompt_channel_id = channel.id

        # Confirm that the channel has been set
        await ctx.send(f"Art prompt channel set to {channel.mention}")

    async def send_prompt(self):
        # Get a reference to the channel
        channel = self.bot.get_channel(self.prompt_channel_id)

        while True:
            # Generate a random diabetes-related art prompt
            prompts = [
                "Create a portrait of someone living with diabetes",
                "Illustrate a scene from a day in the life of a person with diabetes",
                "Design a poster promoting diabetes awareness and education",
                "Draw a picture of a diabetes-friendly meal",
                "Paint a landscape that represents the emotional journey of living with diabetes"
            ]

            # Select a random art prompt from the list
            prompt = prompts[random.randint(0, len(prompts) - 1)]

            # Send the selected art prompt to the channel
            await channel.send(prompt)

            # Wait for 24 hours before sending the next art prompt
            await asyncio.sleep(24 * 60 * 60)

async def setup(bot):
    await bot.add_cog(ArtPrompts(bot))
