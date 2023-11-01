from discord.ext import commands
from discord import File
import io
from PIL import Image, ImageDraw
import colorsys

class Beetify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def beetify(self, ctx):
        """Add a thicker blue circle (Diabetes Awareness Month style) around your profile picture"""
        
        user_avatar = ctx.author.avatar.with_size(128)  

        
        with io.BytesIO(await user_avatar.read()) as image_binary:
            avatar_image = Image.open(image_binary)

            
            draw = ImageDraw.Draw(avatar_image)

            
            circle_color = "#465cec"

            
            draw.ellipse((0, 0, 128, 128), outline=circle_color, width=14)  

            
            with io.BytesIO() as output_binary:
                avatar_image.save(output_binary, format="PNG")
                output_binary.seek(0)

                # Send the modified avatar as a file
                await ctx.send(file=File(output_binary, filename="beetified_avatar.png"))

    @commands.command()
    async def rainbow_circle(self, ctx):
        """Add a rainbow circle effect around your profile picture"""

        user_avatar = ctx.author.avatar.with_size(128)

        with io.BytesIO(await user_avatar.read()) as image_binary:
            avatar_image = Image.open(image_binary)

            draw = ImageDraw.Draw(avatar_image)

            circle_radius = 63
            num_colors = 6  # Number of colors in the rainbow (360 degrees)
            colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 128, 0), (0, 0, 255), (148, 0, 211)]

            for i in range(num_colors):
                start_angle = i * (360 / num_colors)
                end_angle = (i + 1) * (360 / num_colors)
                color = colors[i]

                # Calculate the position of the circle
                x1 = 64 - circle_radius
                y1 = 64 - circle_radius
                x2 = 64 + circle_radius
                y2 = 64 + circle_radius

                # Draw the rainbow-colored circle segment
                draw.arc((x1, y1, x2, y2), start_angle, end_angle, + 1, fill=color, width=14)

            with io.BytesIO() as output_binary:
                avatar_image.save(output_binary, format="PNG")
                output_binary.seek(0)

                # Send the modified avatar as a file
                await ctx.send(file=File(output_binary, filename="rainbow_circle_avatar.png"))


async def setup(bot):
    await bot.add_cog(Beetify(bot))
