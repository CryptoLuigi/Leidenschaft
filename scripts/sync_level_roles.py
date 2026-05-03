import argparse
import asyncio
import os
from types import SimpleNamespace

import nextcord
from databases import Database
from dotenv import load_dotenv

from dislevel import init_dislevel
from dislevel.leveling_service import sync_level_roles

DEFAULT_BREAKPOINTS = [
    "[35,40)",
    "[70,inf)",
]


def parse_breakpoint(spec: str) -> tuple[int, int]:
    if not spec.startswith("[") or not spec.endswith(")"):
        raise argparse.ArgumentTypeError(
            f"Invalid breakpoint '{spec}'. Range must use [min,max) notation."
        )

    bounds = spec[1:-1]
    try:
        min_level_text, max_level_text = bounds.split(",", 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid breakpoint '{spec}'. Expected two comma-separated bounds."
        ) from exc

    min_level = int(min_level_text.strip())
    max_level_raw = max_level_text.strip().lower()
    max_level = 2_000_000 if max_level_raw == "inf" else int(max_level_raw)
    role_name = role_name.strip()

    if min_level < 0:
        raise argparse.ArgumentTypeError("Breakpoint minimum level cannot be negative.")
    if max_level <= min_level:
        raise argparse.ArgumentTypeError("Breakpoint upper bound must be greater than lower bound.")

    return (min_level, max_level - 1)


def level_in_breakpoints(level: int, breakpoints: list[tuple[int, int]]) -> bool:
    return any(min_level <= level <= max_level for min_level, max_level in breakpoints)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync Discord level roles from the stored leveling table."
    )
    parser.add_argument(
        "--guild-id",
        type=int,
        required=True,
        help="Discord guild ID to sync.",
    )
    parser.add_argument(
        "--database-url",
        default="sqlite:///leveling.db",
        help="Database URL for the leveling data.",
    )
    parser.add_argument(
        "--table",
        default="leveling",
        help="Leveling table name.",
    )
    parser.add_argument(
        "--breakpoint",
        dest="breakpoints",
        action="append",
        type=parse_breakpoint,
        help=(
            "Level breakpoint in [min,max) format. "
            "Repeat to provide multiple ranges. Example: --breakpoint '[35,40)'"
        ),
    )
    return parser.parse_args()


async def run_sync(
    guild_id: int,
    database_url: str,
    table: str,
    breakpoints: list[tuple[int, int]] | None,
) -> None:
    load_dotenv()

    token = os.getenv("TOKEN")
    if not token:
        raise RuntimeError("TOKEN is not set.")

    intents = nextcord.Intents.none()
    intents.guilds = True
    intents.members = True

    bot = nextcord.Client(intents=intents)
    database = Database(database_url)

    @bot.event
    async def on_ready() -> None:
        try:
            await database.connect()
            await init_dislevel(SimpleNamespace(), database, table_name=table)
            active_breakpoints = breakpoints or [parse_breakpoint(spec) for spec in DEFAULT_BREAKPOINTS]

            guild = bot.get_guild(guild_id)
            if guild is None:
                guild = await bot.fetch_guild(guild_id)

            print(f"Syncing roles for guild {guild_id}...")

            rows = await database.fetch_all(
                f"""
                SELECT member_id, level
                FROM {table}
                WHERE guild_id = :guild_id
                """,
                {"guild_id": guild_id},
            )

            synced = 0
            skipped = 0

            for row in rows:
                member_id = int(row["member_id"])
                level = int(row["level"])

                if not level_in_breakpoints(level, active_breakpoints):
                    continue

                try:
                    member = guild.get_member(member_id) or await guild.fetch_member(member_id)
                except nextcord.NotFound:
                    skipped += 1
                    continue

                await sync_level_roles(guild, member, level)
                synced += 1

            print(f"Role sync complete. Synced {synced} members, skipped {skipped}.")
        finally:
            await database.disconnect()
            await bot.close()

    await bot.start(token)


def main() -> None:
    args = parse_args()
    asyncio.run(
        run_sync(
            args.guild_id,
            args.database_url,
            args.table,
            args.breakpoints,
        )
    )


if __name__ == "__main__":
    main()
