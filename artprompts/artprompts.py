from discord.ext import commands
import asyncio
import random

class ArtPrompts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Create a background task that runs the send_prompt function every day
        self.bg_task = self.bot.loop.create_task(self.send_prompt())

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

    async def send_prompt(self):
        # Get the ID of the channel where the art prompts should be sent
        channel_id = 590818115756097537

        # Get a reference to the channel
        channel = self.bot.get_channel(channel_id)

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
