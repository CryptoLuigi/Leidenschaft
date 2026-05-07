from __future__ import annotations

import sys
import types

import pytest


def test_calculate_level_from_xp(load_source_module):
    service = load_source_module("test_leveling_service", "dislevel/leveling_service.py")

    assert service.calculate_level_from_xp(0) == 0
    assert service.calculate_level_from_xp(99) == 0
    assert service.calculate_level_from_xp(100) == 1
    assert service.calculate_level_from_xp(254) == 1
    assert service.calculate_level_from_xp(255) == 2


def test_get_role_name_for_level(load_source_module):
    service = load_source_module("test_leveling_service_roles", "dislevel/leveling_service.py")

    assert service.get_role_name_for_level(4) == ""
    assert service.get_role_name_for_level(35) == "High Bishop (Level 30)"
    assert service.get_role_name_for_level(39) == "High Bishop (Level 30)"
    assert service.get_role_name_for_level(40) == "Noble (Level 40)"
    assert service.get_role_name_for_level(70) == "Zent (Level 70)"
    assert service.get_role_name_for_level(80) == "Divine Avatar (Level 80)"


def test_build_leveling_state_clamps_negative_xp(load_source_module):
    service = load_source_module("test_leveling_service_state", "dislevel/leveling_service.py")

    state = service.build_leveling_state(-50)

    assert state.xp == 0
    assert state.level == 0


def test_random_blessing_thresholds(load_source_module):
    service = load_source_module("test_leveling_service_blessing", "dislevel/leveling_service.py")

    assert service.get_random_blessing_odds(0) == 500
    assert service.get_random_blessing_odds(49) == 500
    assert service.get_random_blessing_odds(50) == 5_000
    assert service.get_random_blessing_odds(100) == 5_000


def test_random_blessing_xp_scales_with_level(load_source_module, monkeypatch):
    service = load_source_module(
        "test_leveling_service_blessing_xp", "dislevel/leveling_service.py"
    )

    monkeypatch.setattr(service.random, "randint", lambda start, end: 4_000)

    assert service.get_random_blessing_xp(0) == 4_000
    assert service.get_random_blessing_xp(20) == 8_000
    assert service.get_random_blessing_xp(50) == 14_000


@pytest.mark.asyncio
async def test_sync_level_roles_removes_higher_roles(load_source_module, monkeypatch):
    service = load_source_module("test_leveling_service_sync", "dislevel/leveling_service.py")

    class Role:
        def __init__(self, name):
            self.name = name

    class Member:
        def __init__(self, roles):
            self.roles = roles[:]
            self.added = []
            self.removed = []

        async def add_roles(self, role):
            self.added.append(role.name)
            if role not in self.roles:
                self.roles.append(role)

        async def remove_roles(self, role):
            self.removed.append(role.name)
            self.roles = [existing for existing in self.roles if existing.name != role.name]

    class Guild:
        def __init__(self, roles):
            self.roles = roles

    def fake_get(roles, name):
        for role in roles:
            if role.name == name:
                return role
        return None

    nextcord_module = types.ModuleType("nextcord")
    nextcord_module.utils = types.SimpleNamespace(get=fake_get)
    monkeypatch.setitem(sys.modules, "nextcord", nextcord_module)

    high_bishop = Role("High Bishop (Level 30)")
    zent = Role("Zent (Level 70)")
    guild = Guild([high_bishop, zent])
    member = Member([zent])

    await service.sync_level_roles(guild, member, 35)

    assert member.added == ["High Bishop (Level 30)"]
    assert member.removed == ["Zent (Level 70)"]
