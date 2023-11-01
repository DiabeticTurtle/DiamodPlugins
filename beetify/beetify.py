from discord.ext import commands
from discord import File
import io
from PIL import Image, ImageDraw

class beetify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.avatar_size_threshold = 512

    @commands.command()
    async def beetify(self, ctx):
        """Add a thick blue circle (Diabetes Awareness Month style) around your profile picture"""
        
        user_avatar = ctx.author.avatar.with_size(128)
        user_avatar_512 = ctx.author.avatar.with_size(512)
        ellipse_dimensions = (0, 0, 0, 0)
        circle_width = 0

        if user_avatar == user_avatar:
            # Use the 128-pixel version with a width of 24
            ellipse_dimensions = (0, 0, 128, 128)
            circle_width = 24
            
        else:
            # Use the 512-pixel version with a width of 39
            user_avatar = user_avatar_512
            ellipse_dimensions = (0, 0, 512, 512)
            circle_width = 39


        with io.BytesIO(await user_avatar.read()) as image_binary:
            avatar_image = Image.open(image_binary)

            draw = ImageDraw.Draw(avatar_image)

            circle_color = "#465cec"

            draw.ellipse(ellipse_dimensions, outline=circle_color, width=circle_width)

            with io.BytesIO() as output_binary:
                avatar_image.save(output_binary, format="PNG")
                output_binary.seek(0)

                await ctx.send(file=File(output_binary, filename="beetified_avatar.png"))

async def setup(bot):
   await bot.add_cog(beetify(bot))
