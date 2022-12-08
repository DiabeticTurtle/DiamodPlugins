from discord.ext import commands

class ModContact(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Set the bot's status to let people know they can DM it to contact the mods
    @commands.Cog.listener()
    async def on_ready(self):
        activity = discord.Activity(name="DM me to contact the mods", type=discord.ActivityType.listening)
        await self.bot.change_presence(status=discord.Status.online, activity=activity)

    @commands.command()
    async def join(self, ctx, thread_id: int):
        if ctx.message.thread_id is not None:
            await ctx.message.channel.join_thread(thread_id)

async def setup(bot):
    await bot.add_cog(ModContact(bot))
