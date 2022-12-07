from discord.ext import commands
from discord import TextChannel
import asyncio
import random

class ArtPrompts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.prompt_channel_id = None

        # List of possible categories
        self.categories = ["animals", "food", "colors", "emotions", "sports", "music", "places", "books", "movies", "television shows", "mythical creatures", "sci-fi and fantasy", "nature and the environment", "historical events and figures", "art and design", "fashion and beauty", "science and technology", "politics and current events"]

    @commands.Cog.listener()
    async def on_message(self, message):
        print(message.content)

    @commands.command()
    async def diabetesart(self, ctx):
        """Generate a random diabetes-related art prompt"""
        prompts = [
            "Create a portrait of someone living with diabetes",
            "Illustrate a scene from a day in the life of a person with diabetes",
            "Design a poster promoting diabetes awareness and education",
            "Draw a picture of a diabetes-friendly meal",
            "Paint a landscape that represents the emotional journey of living with diabetes",
            "Illustrate the challenges of managing blood sugar levels",
            "Create a collage depicting the impact of diabetes on daily life",
            "Paint a picture of a support group for people with diabetes",
            "Design a graphic novel about the journey of a person with diabetes",
            "Draw a portrait of a medical professional who specializes in diabetes care",
            "Illustrate the benefits of regular exercise for people with diabetes",
            "Create a poster promoting healthy eating for people with diabetes",
            "Paint a scene from a diabetes education class",
            "Design a series of illustrations about the history of diabetes treatment",
            "Draw a picture of a diabetic child learning to manage their condition",
            "Illustrate the emotional challenges of living with diabetes",
            "Create a collage of famous people who have lived with diabetes",
            "Paint a portrait of a diabetes advocate or activist",
            "Design a poster about the importance of regular check-ups for people with diabetes",
            "Draw a picture of a family supporting a loved one with diabetes",
            "Illustrate the role of technology in managing diabetes",
            "Create a series of illustrations depicting the emotional journey of a person with diabetes",
            "Paint a portrait of a person with diabetes who is thriving and living a full life",
            "Design a poster about the impact of diabetes on mental health"
        ]

        # Select a random art prompt from the list
        prompt = prompts[random.randint(0, len(prompts) - 1)]

        # Send the selected art prompt to the user
        await ctx.send(prompt)

    @commands.command()
    async def set_prompt_channel(self, ctx, channel: TextChannel):
        
        """Set the ID of the channel where the art prompts should be sent"""
        self.prompt_channel_id = channel.id

        # Confirm that the channel has been set
        await ctx.send(f"Art prompt channel set to {channel.mention}")

    async def send_prompt(self):
        # Get a reference to the channel
        channel = self.bot.get_channel(self.prompt_channel_id)

        while True:
            # Choose two random categories
            category1 = random.choice(self.categories)
            category2 = random.choice(self.categories)

            # Generate the art prompt
            prompt = "Create a piece of art that combines the concepts of " + category1 + " and " + category2

            # Send the selected art prompt to the channel
            await channel.send(prompt)

            # Wait for 24 hours before sending the next art prompt
            await asyncio.sleep(24 * 60 * 60)

async def setup(bot):
    await bot.add_cog(ArtPrompts(bot))
