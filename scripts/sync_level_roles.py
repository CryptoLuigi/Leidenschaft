import argparse
import asyncio
import os
from types import SimpleNamespace

import nextcord
from databases import Database
from dotenv import load_dotenv

from dislevel import init_dislevel
from dislevel.leveling_service import sync_level_roles


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
    return parser.parse_args()


async def run_sync(guild_id: int, database_url: str, table: str) -> None:
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
    asyncio.run(run_sync(args.guild_id, args.database_url, args.table))


if __name__ == "__main__":
    main()
