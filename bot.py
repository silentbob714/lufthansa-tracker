import os

import discord

from dotenv import load_dotenv

from database import initialize_database


load_dotenv()


TOKEN = os.getenv("DISCORD_TOKEN")


initialize_database()



class FlightWatchBot(discord.Client):

    def __init__(self):

        intents = discord.Intents.default()

        super().__init__(
            intents=intents
        )

        self.tree = discord.app_commands.CommandTree(self)



    async def setup_hook(self):

        await self.load_extension(
            "cogs.aircraft"
        )

        await self.load_extension(
            "cogs.fleet"
        )

        await self.load_extension(
            "cogs.system"
        )

        await self.tree.sync()



bot = FlightWatchBot()



@bot.event
async def on_ready():

    print(
        f"Logged in as {bot.user}"
    )



bot.run(TOKEN)
