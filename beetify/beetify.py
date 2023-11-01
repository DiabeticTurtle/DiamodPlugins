from discord.ext import commands
from discord import File
import io
from PIL import Image, ImageDraw

class beetify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def beetify(self, ctx):
        """Add a thick blue circle (Diabetes Awareness Month style) around your profile picture"""
        
        user_avatar = ctx.author.avatar_url

        
        with io.BytesIO(await user_avatar.read()) as image_binary:
            avatar_image = Image.open(image_binary)

           
            draw = ImageDraw.Draw(avatar_image)

           
            draw.ellipse((0, 0, 128, 128), outline="blue", width=10)

            
            with io.BytesIO() as output_binary:
                avatar_image.save(output_binary, format="PNG")
                output_binary.seek(0)

                
                await ctx.send(file=File(output_binary, filename="beetified_avatar.png"))

async def setup(bot):
    bot.add_cog(beetify(bot))
