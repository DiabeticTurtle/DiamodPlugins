from discord.ext import commands

class slashcmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        print(message.content)

    @commands.command()
    async def say(self, ctx, *, message):
        await ctx.send(message)

    # This is the new command that will be added
    @commands.command()
    async def mycommand(self, ctx):
        await ctx.send("This is my command!")

async def setup(bot):
    await bot.add_cog(slashcmd(bot))