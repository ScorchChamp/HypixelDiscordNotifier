from discord.ext import commands
import os
import json
from dotenv import dotenv_values, load_dotenv
import requests
import discord
import MojangAPI
import asyncio

bot = commands.Bot(command_prefix='.')


load_dotenv()
config = dotenv_values(".env")

def startBot(token): bot.run(token)
def getBasePath(file): return os.path.dirname(os.path.realpath(file))


API_KEY = config["API_KEY"]
BASE_PATH = getBasePath(__file__)
DATA_FILE = BASE_PATH + "/data.json"

def getLastLogin(username):
    data = requests.get("https://api.hypixel.net/player", params={"key": API_KEY, "uuid": MojangAPI.getUUIDFromUsername(username)}).json()
    if not "player" in data: return 0
    if not "lastLogin" in data["player"]: return 0
    return data["player"]["lastLogin"]

def getFullFileData():
    try: 
        with open(DATA_FILE, 'r') as f: return json.load(f)
    except:
        with open(DATA_FILE, 'w') as f: f.write("{}")
    return {}

def storeData(guild_id, key, data):
    guild_id = str(guild_id)

    with open(DATA_FILE, "r") as jsonFile:
        full_data = json.load(jsonFile)

    if not guild_id in full_data: full_data[guild_id] = {}
    full_data[guild_id][key] = data

    with open(DATA_FILE, "w") as jsonFile:
        json.dump(full_data, jsonFile, indent=4)

def readData(guild_id, key):
    guild_id = str(guild_id)
    if not guild_id in getFullFileData(): return None
    if not key in getFullFileData()[guild_id]: return None
    return getFullFileData()[guild_id][key]

async def generateListEmbed(guild_id):
    trackers = readData(guild_id, "trackers")
    if not trackers: return

    embed = discord.Embed(title="Tracking login dates...", color=discord.Color.red())
    names = ""
    dates = ""

    for player in trackers:
        names += f"{player}\n"
        dates += f"<t:{int(getLastLogin(player)/1000)}>\n"
        last_online = readData("players", player)
        new_online = getLastLogin(player)
        if last_online == None: 
            storeData("players", player, new_online)
            continue
        if last_online + 10 < new_online:
            embed = embed=discord.Embed(description=f"{player} WENT ONLINE AT <t:{int(new_online/1000)}>!", color=discord.Color.red())
            await (await bot.fetch_channel(readData(guild_id, "bot_channel"))).send(content="@everyone", embed=embed)
            for member in readData(guild_id, "notifies"):
                user = await bot.fetch_user(int(member))
                await user.send(embed=embed, content="<@!" + str(user.id) + ">")

        storeData("players", player, new_online)

    embed.add_field(name="Usernames:", value = names)
    embed.add_field(name="Last Login:", value = dates)
    return embed

async def reloadMessages():
    print("Reloading!")
    for guild in getFullFileData():
        channel_id = readData(guild, "bot_channel")
        if not channel_id: return
        channel = await bot.fetch_channel(channel_id)

        message_id = readData(guild, "last_tracker_message")
        if not message_id: 
            msg = await channel.send("Loading players...")
            storeData(guild, "last_tracker_message", msg.id)

        for message in (await channel.history(limit=100).flatten()):
            if message.id == message_id: 
                await message.edit(embed=await generateListEmbed(guild), content="")
                return
        msg = await channel.send(embed=await generateListEmbed(guild), content="")
        storeData(guild, "last_tracker_message", msg.id)

@bot.command()
async def setThisChannel(ctx):
    storeData(ctx.guild.id, "bot_channel", ctx.channel.id)
    await ctx.reply(embed=discord.Embed(description="This channel will now be used for player login updates!"), delete_after=5)
    await ctx.message.delete()

@bot.command()
async def lastlogin(ctx, arg):
    await ctx.reply(embed=discord.Embed(title=arg, description=f"Last login: <t:{int(int(getLastLogin(arg))/1000)}>"))

@bot.command()
async def notifyme(ctx):
    notifies = readData(ctx.guild.id, "notifies")
    if not notifies: notifies = []
    notifies.append(ctx.author.id)
    storeData(ctx.guild.id, "notifies", notifies)
    await ctx.reply(embed=discord.Embed(description=f"You will now be notified when someone gets online!", delete_after=5))


@bot.command()
async def add(ctx, arg):
    trackers = readData(ctx.guild.id, "trackers")
    print(trackers)
    if not trackers: trackers = []
    if not arg in trackers: trackers.append(arg)
    storeData(ctx.guild.id, "trackers", trackers)
    await reloadMessages()
    await ctx.reply(embed=discord.Embed(title=arg, description=f"Player {arg} has been added!", delete_after=5))

async def runTask(task):
    while True:
        await task()
        await asyncio.sleep(10)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} connected!")
    bot.loop.create_task(runTask(reloadMessages))
