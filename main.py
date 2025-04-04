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

level_roles = [
    (5, 9, "Farmer (Level 5)"),
    (10, 14, "Soldier (Level 10)"),
    (15, 19, "Craftsman (Level 15)"),
    (20, 24, "Merchant (Level 20)"),
    (25, 29, "Mayor (Level 25)"),
    (30, 34, "Shrine Maiden (Level 30)"),
    (35, 39, "Noble (Level 35)"),
    (40, 49, "Aub (Level 40)"),
    (50, 59, "Zent (Level 50)"),
    (60, 2000000, "Goddess (Level 60)"),
]

def get_cur_and_prev_role_names_for(level: int) -> tuple[str, list[str]]:
    if level < 5:
        return "", []
    prev_roles = []
    for role_level, role_level_up, role_name in level_roles:
        if role_level <= level <= role_level_up:
            return (role_name, prev_roles)
        prev_roles.append(role_name)
    assert False, "Not possible"


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

    role_name, prev_roles = get_cur_and_prev_role_names_for(level)
    print(f"Role calculation for {member}: current role={role_name}, previous roles={prev_roles}")

    if not role_name: # No role is returned, < lvl 5
        print(f"No role assigned for {member} at level {level} (below level 5)")
        return

    role_obj = nextcord.utils.get(guild.roles, name=role_name)
    if not role_obj:
        print(f"Role with name {role_name} not found.")
        return

    print(f"Adding role {role_name} to {member}")
    await member.add_roles(role_obj)

    for role in prev_roles:
        role_obj = nextcord.utils.get(guild.roles, name=role)
        if not role_obj:
            print(f"Role with name {role} not found.")
            continue
        print(f"Removing previous role {role} from {member}")
        await member.remove_roles(role_obj)

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
