import casbin
from casbin_async_sqlalchemy_adapter import Adapter
from sqlalchemy import update

from core.base import models
from ..models import CasbinRule
from typing import List


class CasbinService(models.Assembly):
    _enforcer = None

    async def get_enforcer(self) -> casbin.AsyncEnforcer:
        """Initialize and return the Casbin Enforcer singleton."""
        if self._enforcer is None:
            adapter = Adapter(self.get_engine())  # SQLAlchemy Session as the adapter
            config_path = self.get_viper().get("system.casbin-path")
            self._enforcer = casbin.AsyncEnforcer(config_path, adapter)
        await self._enforcer.load_policy()  # Load existing policies
        return self._enforcer

    async def add_grouping_policy(self, g: str, p: str) -> None:
        """Add a grouping policy (e.g., assign a user to a role)."""
        e = await self.get_enforcer()
        await self.clear_groups(0, [g])  # Clear existing groups for 'g'
        if not await e.add_grouping_policy(g, p):
            raise Exception("权限设置失败，请联系管理员！")

    async def update_casbin(self, role_code: str, casbins: List[dict] | List[str], casbin_type) -> None:
        """Update Casbin policies for a given role."""
        e = await self.get_enforcer()
        await self.clear_casbin(0, [role_code, casbin_type])  # Clear existing policies for the role
        if not casbins:  # If no policies to add, return early
            return
        if casbin_type == 'menu':
            rules = [[role_code, casbin_type, v, "all"] for v in casbins]  # Prepare rules
        else:
            rules = [[role_code, casbin_type, v['path'], v['act']] for v in casbins]  # Prepare rules
        if not await e.add_policies(rules):
            raise Exception("权限设置失败，请联系管理员！")

    async def update_casbin_mark(self, old_path: str, new_path: str) -> None:
        """Update the 'v1' field (e.g., path) in Casbin rules."""
        async with self.get_db() as session:
            session.execute(
                update(CasbinRule).where(CasbinRule.v1 == old_path).values(v1=new_path)
            )

    async def update_casbin_role_mark(self, old_path: str, new_path: str) -> None:
        """Update the 'v0' field (e.g., role) in Casbin rules."""
        async with self.get_db() as session:
            await session.execute(
                update(CasbinRule).where(CasbinRule.v0 == old_path).values(v0=new_path)
            )

    async def clear_casbin(self, v: int, p: List[str]) -> bool:
        """Clear Casbin policies matching the given field and values."""
        e = await self.get_enforcer()
        ok = await e.remove_filtered_policy(v, *p)
        return ok

    async def clear_groups(self, v: int, g: List[str]) -> bool:
        """Clear grouping policies matching the given field and values."""
        e = await self.get_enforcer()
        ok = await e.remove_filtered_grouping_policy(v, *g)
        return ok

    async def get_filtered_policy(self, *p):
        """Retrieve filtered Casbin policies."""
        e = await self.get_enforcer()
        rules = e.get_filtered_policy(0, *p)
        return rules


# Global instance for easy access
casbin_service = CasbinService()
