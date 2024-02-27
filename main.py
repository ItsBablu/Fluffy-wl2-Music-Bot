import discord
import os

import wavelink

import jishaku
from discord.ext import commands, tasks
import asyncio
import sqlite3
import Fluffy
import psutil


con = sqlite3.connect("database.db")
cur = con.cursor()


async def get_prefix(client, message):
    cursor = con.execute(
        f"""SELECT prefix FROM Prefix WHERE guild_id = {message.guild.id}"""
    )
    resultz = cursor.fetchone()
    cursor = con.execute(f"SELECT users FROM Np")
    NP = cursor.fetchall()
    if resultz is None:
        con.execute(
            "INSERT INTO Prefix(prefix, guild_id) VALUES(?, ?)",
            (
                "&",
                message.guild.id,
            ),
        )
        con.commit()

    c = con.execute("SELECT prefix FROM Prefix WHERE guild_id = ?", (message.guild.id,))
    result = c.fetchone()

    if message.author.id in ([int(i[0]) for i in NP]):
        a = commands.when_mentioned_or("", result[0])(client, message)
        return sorted(a, reverse=True)
    else:
        return commands.when_mentioned_or(result[0])(client, message)


class Fluffy(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix,
            intents=discord.Intents.all(),
            case_insensitive=True,
            strip_after_prefix=True,
        )


client = Fluffy()
shard_guild_counts = {}


@client.event
async def on_connect():
    await client.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(type=discord.ActivityType.listening, name="&help"),
    )


@client.event
async def setup_hook():
    cur.execute("CREATE TABLE IF NOT EXISTS Np(users)")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS Prefix(guild_id TEXT NOT NULL, prefix TEXT NOT NULL)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS ignored_channels (guild_id INTEGER, channel_id INTEGER, PRIMARY KEY (guild_id, channel_id))"
    )
    cur.execute("CREATE TABLE IF NOT EXISTS blacklist (user_id INTEGER PRIMARY KEY)")
    cur.execute("CREATE TABLE IF NOT EXISTS Owner (user_id INTEGER PRIMARY KEY)")
    cur.execute("CREATE TABLE IF NOT EXISTS Profile (user_id INTEGER PRIMARY KEY)")
    print("Table Initated")


@client.event
async def on_shard_ready(shard_id):
    guild_count = len(client.guilds)
    shard_guild_counts[shard_id] = guild_count
    print(f"Shard {shard_id} is ready and handling {guild_count} servers.")


@client.event
async def on_ready():
    await client.load_extension("jishaku")
    client.owner_ids = [
        786926252811485186,
        1177262245034606647,
    ]
    client.loop.create_task(node_connect())
    cache_sweeper.start()
    print(f"Connected as {client.user}")


@client.event
async def node_connect():
    await client.wait_until_ready()
    node = wavelink.Node(uri="http://n1.ll.darrennathanael.com:2269", password="glasshost1984")
    await wavelink.Pool.connect(client=client, nodes=[node])

@client.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"Node {node.identifier} is ready")


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    cur.execute(
        "SELECT * FROM ignored_channels WHERE channel_id = ?", (message.channel.id,)
    )
    if cur.fetchone():
        return
    cur.execute("SELECT * FROM blacklist WHERE user_id = ?", (message.author.id,))
    if cur.fetchone():
        return
    await client.process_commands(message)


@tasks.loop(minutes=60)
async def cache_sweeper():
    client._connection._private_channels.clear()
    client._connection._users.clear()
    client._connection._messages.clear()
    print("Cleared Cache")


async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")


async def main():
    async with client:
        await load()
        await client.start(
            "MTE5NzE2NzUwNDM3NjcyNTY5OA.GRtxFE.lOOP_TZ0PyEgqBwiTIRP1UUgxklMoHGClUK9I4"
        )


asyncio.run(main())
