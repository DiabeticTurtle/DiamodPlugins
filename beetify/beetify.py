from discord.ext import commands
from discord import File, Member
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw, ImageOps

class beetify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def beetify(self, ctx, member: Member = None):
        """Add a thick blue circle (Diabetes Awareness Month style) around a user's profile picture"""

        user = member if member else ctx.author
        user_avatar = user.avatar.url

        pfp = Image.open(BytesIO(await user_avatar.read()))
        pfp = pfp.resize((125, 125))

        my_image = Image.new("RGB", (512, 512))
        my_image.paste(pfp, (36, 80))

        draw = ImageDraw.Draw(my_image)
        circle_color = "#465cec"
        circle_width = 24

        draw.ellipse((0, 0, 128, 128), outline=circle_color, width=circle_width)

        # You can add text or other modifications here if needed

        with BytesIO() as output_binary:
            my_image.save(output_binary, format="PNG")
            output_binary.seek(0)

            await ctx.send(file=File(output_binary, filename="beetified_avatar.png"))

async def setup(bot):
    await bot.add_cog(beetify(bot))
