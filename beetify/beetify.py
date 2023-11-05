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
        """Add a blue circle (Diabetes Awareness Month style) around your profile picture"""
        
        user_avatar = ctx.author.avatar.with_size(512)  

        
        with io.BytesIO(await user_avatar.read()) as image_binary:
            avatar_image = Image.open(image_binary)

            
            draw = ImageDraw.Draw(avatar_image)

            circle_color = "#465cec"
            avatar_image = avatar_image.resize((128*4, 128*4), resample=Image.LANCZOS)
            draw = ImageDraw.Draw(avatar_image)
            draw.ellipse((0, 0, 128*4, 128*4), outline=circle_color, width=49)
            avatar_image = avatar_image.resize((128, 128), resample=Image.LANCZOS)

            
            with io.BytesIO() as output_binary:
                avatar_image.save(output_binary, format="PNG")
                output_binary.seek(0)

                # Send the modified avatar as a file
                await ctx.send(file=File(output_binary, filename="beetified_avatar.png"))

async def setup(bot):
    await bot.add_cog(Beetify(bot))