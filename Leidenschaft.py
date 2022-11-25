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
bot = commands.Bot(command_prefix='?',help_command=None, intents=intents)

botchannel = 638020706935767100

@bot.event
async def on_ready():
    db = Database("sqlite:///leveling.db")
    await db.connect()
    await init_dislevel(bot, db, "leveling")
    print("Ready! Let's go...")



@bot.event
async def on_dislevel_levelup(guild_id, member_id, level):
    guild = bot.get_guild(guild_id)
    member = guild.get_member(member_id)
    channel = guild.get_channel(botchannel)
    role_lvl5 = nextcord.utils.get(guild.roles, name="Farmer (level 5)")
    role_lvl10 = nextcord.utils.get(guild.roles, name="Soldier (level 10)")
    role_lvl15 = nextcord.utils.get(guild.roles, name="Craftsman (level 15)")
    role_lvl20 = nextcord.utils.get(guild.roles, name="Merchant (level 20)")
    role_lvl25 = nextcord.utils.get(guild.roles, name="Shrine Maiden (level 25)")
    role_lvl30 = nextcord.utils.get(guild.roles, name="Noble (level 30)")
    role_lvl40 = nextcord.utils.get(guild.roles, name="Aub (level 40)")
    role_lvl50 = nextcord.utils.get(guild.roles, name="Zent (level 50)")
    role_lvl60 = nextcord.utils.get(guild.roles, name="Goddess (level 60)")

    print(f'{member} leveled up')

    if level >= 5 and level <= 9:
        await member.add_roles(role_lvl5)

    if level >= 10 and level <= 14:
        await member.add_roles(role_lvl10)
        await member.remove_roles(role_lvl5)

    if level >= 15 and level <= 19:
        await member.add_roles(role_lvl15)
        await member.remove_roles(role_lvl5)
        await member.remove_roles(role_lvl10)

    if level >= 20 and level <= 24:
        await member.add_roles(role_lvl20)
        await member.remove_roles(role_lvl5)
        await member.remove_roles(role_lvl10)
        await member.remove_roles(role_lvl15)

    if level >= 25 and level <= 29:
        await member.add_roles(role_lvl25)
        await member.remove_roles(role_lvl5)
        await member.remove_roles(role_lvl10)
        await member.remove_roles(role_lvl15)
        await member.remove_roles(role_lvl20)

    if level >= 30 and level <= 39:
        await member.add_roles(role_lvl30)
        await member.remove_roles(role_lvl5)
        await member.remove_roles(role_lvl10)
        await member.remove_roles(role_lvl15)
        await member.remove_roles(role_lvl20)
        await member.remove_roles(role_lvl25)

    if level >= 40 and level <= 49:
        await member.add_roles(role_lvl40)
        await member.remove_roles(role_lvl5)
        await member.remove_roles(role_lvl10)
        await member.remove_roles(role_lvl15)
        await member.remove_roles(role_lvl20)
        await member.remove_roles(role_lvl25)
        await member.remove_roles(role_lvl30)

    if level >= 50 and level <= 59:
        await member.add_roles(role_lvl50)
        await member.remove_roles(role_lvl5)
        await member.remove_roles(role_lvl10)
        await member.remove_roles(role_lvl15)
        await member.remove_roles(role_lvl20)
        await member.remove_roles(role_lvl25)
        await member.remove_roles(role_lvl30)
        await member.remove_roles(role_lvl40)

    if level >= 60:
        await member.add_roles(role_lvl60)
        await member.remove_roles(role_lvl5)
        await member.remove_roles(role_lvl10)
        await member.remove_roles(role_lvl15)
        await member.remove_roles(role_lvl20)
        await member.remove_roles(role_lvl25)
        await member.remove_roles(role_lvl30)
        await member.remove_roles(role_lvl40)
        await member.remove_roles(role_lvl50)

class CooldownBucket(Enum):
    message_author = 1
    def process(self, *args, **kwargs):
        return args[0].author.id

cooldown = Cooldown(1, 60, CooldownBucket.message_author)

@bot.event
async def on_message(message):
    banchannel = f"bots"
    if message.author.bot:
        return

    if (f"{message.channel}") == banchannel:    
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

bot.load_extension('dislevel.nextcord.slash')
bot.run(os.getenv("TOKEN"))