import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nextcord import Guild, Member


LEVEL_ROLES = (
    (5, 9, "Farmer (Level 5)"),
    (10, 14, "Soldier (Level 10)"),
    (15, 19, "Craftsman (Level 15)"),
    (20, 24, "Merchant (Level 20)"),
    (25, 29, "Shrine Maiden (Level 25)"),
    (30, 39, "High Bishop (Level 30)"),
    (40, 49, "Noble (Level 40)"),
    (50, 59, "Archduke Candidate (Level 50)"),
    (60, 69, "Aub (Level 60)"),
    (70, 79, "Zent (Level 70)"),
    (80, 99, "Divine Avatar (Level 80)"),
    (100, 2_000_000, "Goddess (Level 100)"),
)


@dataclass(frozen=True)
class LevelingState:
    xp: int
    level: int


def get_role_names() -> list[str]:
    return [role_name for _, _, role_name in LEVEL_ROLES]


def get_role_name_for_level(level: int) -> str:
    if level < LEVEL_ROLES[0][0]:
        return ""

    for min_level, max_level, role_name in LEVEL_ROLES:
        if min_level <= level <= max_level:
            return role_name

    return ""


def get_xp_for_next_level(level: int) -> int:
    return 5 * (level ** 2) + (50 * level) + 100


def get_xp_before_level(level: int) -> int:
    total = 0
    for current_level in range(level):
        total += get_xp_for_next_level(current_level)
    return total


def calculate_level_from_xp(total_xp: int) -> int:
    clamped_xp = max(0, total_xp)
    level = 0
    remaining_xp = clamped_xp

    while remaining_xp >= get_xp_for_next_level(level):
        remaining_xp -= get_xp_for_next_level(level)
        level += 1

    return level


def build_leveling_state(total_xp: int) -> LevelingState:
    clamped_xp = max(0, total_xp)
    return LevelingState(xp=clamped_xp, level=calculate_level_from_xp(clamped_xp))


async def sync_level_roles(guild: "Guild", member: "Member", level: int) -> None:
    import nextcord

    role_name = get_role_name_for_level(level)
    managed_role_names = set(get_role_names())

    if role_name:
        target_role = nextcord.utils.get(guild.roles, name=role_name)
        if target_role and target_role not in member.roles:
            await member.add_roles(target_role)

    removable_role_names = managed_role_names - ({role_name} if role_name else set())
    for existing_role in member.roles:
        if existing_role.name in removable_role_names:
            await member.remove_roles(existing_role)


async def change_member_xp(
    bot,
    member_id: int,
    guild_id: int,
    xp_delta: int,
    *,
    last_message: float | None = None,
    dispatch_levelup: bool = True,
) -> dict[str, int]:
    from dislevel.utils import get_member_data

    database = bot.dislevel_database
    leveling_table = os.environ.get("DISLEVEL_TABLE")
    user_data = await get_member_data(bot, member_id, guild_id)

    previous_xp = user_data["xp"] if user_data else 0
    previous_level = user_data["level"] if user_data else 0
    new_state = build_leveling_state(previous_xp + xp_delta)

    if user_data:
        await database.execute(
            f"""
            UPDATE  {leveling_table}
                SET  xp = :xp,
                    level = :level
                WHERE  member_id = :member_id
                AND  guild_id = :guild_id
            """,
            {
                "xp": new_state.xp,
                "level": new_state.level,
                "guild_id": guild_id,
                "member_id": member_id,
            },
        )
    else:
        await database.execute(
            f"""
            INSERT  INTO {leveling_table}
                    (member_id, guild_id, xp, level)
            VALUES  (:member_id, :guild_id, :xp, :level)
            """,
            {
                "xp": new_state.xp,
                "level": new_state.level,
                "guild_id": guild_id,
                "member_id": member_id,
            },
        )

    if last_message is not None:
        cooldown_amount = 60
        await database.execute(
            f"""
            UPDATE  {leveling_table}
                SET  last_message = :last_message
                WHERE  member_id = :member_id
                AND  guild_id = :guild_id
            """,
            {
                "last_message": last_message + cooldown_amount,
                "guild_id": guild_id,
                "member_id": member_id,
            },
        )

    if dispatch_levelup and new_state.level > previous_level:
        bot.dispatch(
            "dislevel_levelup",
            guild_id=guild_id,
            member_id=member_id,
            level=new_state.level,
        )

    return {
        "previous_xp": previous_xp,
        "previous_level": previous_level,
        "xp": new_state.xp,
        "level": new_state.level,
    }
