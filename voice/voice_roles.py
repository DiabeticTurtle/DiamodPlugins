import discord
from discord.ext import commands

ROLE_ID = 804977475217391657


class VoiceRolePlugin(commands.Cog):
    """
    A plugin to automatically add and remove a voice role from users who join voice chats.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener("on_voice_state_update")
    async def add_or_remove_voice_role(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        # user just joined a channel.
        if not before.channel and after.channel:
            try:
                await member.add_roles(
                    ROLE_ID,
                    reason=f"Automatically done for joining voice channel {after.channel}",
                )
            except discord.Forbidden:
                return

        # user was in a channel, then left.
        if before.channel and not after.channel:
            try:
                await member.remove_roles(
                    ROLE_ID,
                    reason=f"Automatically done for user leaving voice channel {before.channel}",
                )
            except discord.Forbidden:
                return
