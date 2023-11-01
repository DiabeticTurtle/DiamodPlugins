from discord.ext import commands
from discord import Member, File
import io
from PIL import Image, ImageDraw

class Beetify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def beetify(self, ctx, member: Member):
        """Add a thick blue circle (Diabetes Awareness Month style) around a user's profile picture"""
        # Get the user's avatar
        user_avatar = member.avatar_url_as(size=128)

        # Create an Image object from the user's avatar
        with io.BytesIO(await user_avatar.read()) as image_binary:
            avatar_image = Image.open(image_binary)

            # Create a drawing context
            draw = ImageDraw.Draw(avatar_image)

            # Draw a thick blue circle (Diabetes Awareness Month style) around the avatar
            draw.ellipse((0, 0, 128, 128), outline="blue", width=10)

            # Save the modified image to a BytesIO object
            with io.BytesIO() as output_binary:
                avatar_image.save(output_binary, format="PNG")
                output_binary.seek(0)

                # Send the modified avatar as a file
                await ctx.send(file=File(output_binary, filename="beetified_avatar.png"))

async def setup(bot):
    await bot.add_cog(Beetify(bot))
