from typing import Any, Callable

import string

import discord
from discord.ext import commands


class SafeFormat(object):
    def __init__(self, **kw):
        self.__dict = kw

    def __getitem__(self, name):
        return self.__dict.get(name, SafeString('{%s}' % name))


class SafeString(str):
    def __getattr__(self, name):
        try:
            super().__getattr__(name)
        except AttributeError:
            return SafeString('%s.%s}' % (self[:-1], name))


def apply_vars(self, member, message, invite):
    return string.Formatter().vformat(message, [], SafeFormat(
        member=member,
        guild=member.guild,
        bot=self.bot.user,
        invite=invite
    ))
