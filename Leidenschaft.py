import time, nextcord, random, cooldowns, os
from nextcord.ext import commands
from databases import Database
from dislevel import init_dislevel
from dislevel.utils import update_xp
from cooldowns import Cooldown
from dotenv import load_dotenv
from enum import Enum

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
    (5, 9, "Farmer (level 5)"),
    (10, 14, "Soldier (level 10)"),
    (15, 19, "Craftsman (level 15)"),
    (20, 24, "Merchant (level 20)"),
    (25, 29, "Mayor (level 25)"),
    (30, 34, "Shrine Maiden (level 30)"),
    (35, 39, "Noble (level 35)"),
    (40, 49, "Aub (level 40)"),
    (50, 59, "Zent (level 50)"),
    (60, 2000000, "Goddess (level 60)"),
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
    guild = bot.get_guild(guild_id)
    member = guild.get_member(member_id)

    print(f"{member} leveled up")
    
    role_name, prev_roles = get_cur_and_prev_role_names_for(level)
    if not role_name: # No role is returned, < lvl 5
        return
    
    role_obj = nextcord.utils.get(guild.roles, name=role_name)
    await member.add_roles(role_obj)
    for role in prev_roles:
        role_obj = nextcord.utils.get(guild.roles, name=role)
        await member.remove_roles(role_obj)


class CooldownBucket(Enum):
    message_author = 1
    def process(self, *args, **kwargs):
        return args[0].author.id

cooldown = Cooldown(1, 60, CooldownBucket.message_author)

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