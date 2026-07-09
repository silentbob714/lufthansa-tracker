import os

import discord

from discord.ext import commands

from dotenv import load_dotenv

from database import initialize_database


load_dotenv()


TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 408190501045534720


initialize_database()


class FlightWatchBot(commands.Bot):

    def __init__(self):

        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents
        )


    async def setup_hook(self):

        print("===== SETUP HOOK START =====")


        print("Loading cogs...")


        await self.load_extension(
            "cogs.aircraft"
        )

        print("Loaded aircraft cog")


        await self.load_extension(
            "cogs.fleet"
        )

        print("Loaded fleet cog")


        await self.load_extension(
            "cogs.system"
        )

        print("Loaded system cog")


        guild = discord.Object(
            id=GUILD_ID
        )


        print("Clearing guild command cache...")


        self.tree.clear_commands(
            guild=guild
        )


        await self.tree.sync(
            guild=guild
        )


        print("Syncing fresh guild commands...")


        synced = await self.tree.sync(
            guild=guild
        )


        print(
            f"Synced {len(synced)} guild commands:"
        )


        for command in synced:

            print(
                f"- /{command.name}"
            )


        print("===== SETUP HOOK COMPLETE =====")



bot = FlightWatchBot()



@bot.event
async def on_ready():

    print(
        f"Logged in as {bot.user}"
    )



bot.run(TOKEN)
