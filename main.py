import os
import random
import time
from enum import Enum

import cooldowns
import nextcord
from cooldowns import Cooldown
from databases import Database
from dotenv import load_dotenv
from nextcord.ext import commands

from dislevel import init_dislevel
from dislevel.leveling_service import sync_level_roles
from dislevel.utils import update_xp

load_dotenv()
intents = nextcord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="?", help_command=None, intents=intents)

botchannel = 638020706935767100

@bot.event
async def on_ready():
    db = Database("sqlite:///leveling.db")
    await db.connect()
    await init_dislevel(bot, db, "leveling")
    print("Ready! Let's go...")

@bot.event
async def on_dislevel_levelup(guild_id, member_id, level):
    print(f"Level up event triggered for member {member_id} in guild {guild_id} to level {level}")

    guild = bot.get_guild(guild_id)
    if not guild:
        print(f"Guild with ID {guild_id} not found.")
        return

    member = guild.get_member(member_id)
    if not member:
        print(f"Member with ID {member_id} not found.")
        return

    print(f"{member} leveled up to level {level}")
    await sync_level_roles(guild, member, level)
    print(f"Level up processing complete for {member}")


class CooldownBucket(Enum):
    message_author = 1
    def process(self, *args, **kwargs):
        return args[0].author.id

cooldown = Cooldown(1, 1, CooldownBucket.message_author)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel and message.channel.id == botchannel:
        if message.content.startswith("!rank"):
            await message.channel.send(f"`!rank` has been discontinued on the server.\nPlease use {bot.user.mention}'s </rank:1029756764092121098> command.")
        return
    else:
        try:
            async with cooldown(message):
                last_executed = time.time()
                expvalue = random.randint(15,25)
                await update_xp(bot, message.author.id, message.guild.id, last_message=last_executed, amount=expvalue)
        except cooldowns.CallableOnCooldown:
            guild = bot.get_guild(message.guild.id)
            member = guild.get_member(message.author.id)
            print(f'{member} is cooldown')
    #await bot.process_commands(message)

bot.load_extension("dislevel.nextcord.slash")
bot.run(os.getenv("TOKEN"))
