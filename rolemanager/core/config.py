from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

from discord.ext.modmail_utils import Config


from .models import AutoRoleManager, ReactionRoleManager

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorCollection
    from ..rolemanager import RoleManager
    from .types import ConfigPayload


_default_config: ConfigPayload = {
    "autoroles": {
        "roles": [],
        "enable": False,
    },
    "reactroles": {
        "data": [],
        "enable": True,
    },
}


class RoleManagerConfig(Config):
    """
    Config class for RoleManager.
    """

    def __init__(self, cog: RoleManager, db: AsyncIOMotorCollection):
        super().__init__(cog, db, defaults=_default_config, use_cache=False)

    async def fetch(self, *args, **kwargs) -> ConfigPayload:
        if not self.defaults:
            self.defaults = self.deepcopy(_default_config)
        data = await super().fetch(*args, **kwargs)
        self.defaults.clear()
        return data

    async def update(self, *, data: Dict[str, Any] = None) -> None:
        if not data:
            data = self.to_dict()
        await super().update(data=data)

    def to_dict(self) -> ConfigPayload:
        return {
            "autoroles": self.cog.autorole_manager.to_dict(),
            "reactroles": self.cog.reactrole_manager.to_dict(),
        }