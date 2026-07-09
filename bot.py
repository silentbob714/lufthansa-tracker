import os

import discord

from discord import app_commands

from dotenv import load_dotenv

from database import (
    initialize_database,
    get_tracked_aircraft,
    add_tracked_aircraft,
    get_connection
)


load_dotenv()


TOKEN = os.getenv("DISCORD_TOKEN")


initialize_database()



class FlightWatchBot(discord.Client):

    def __init__(self):

        intents = discord.Intents.default()

        super().__init__(
            intents=intents
        )

        self.tree = app_commands.CommandTree(self)



bot = FlightWatchBot()



@bot.event
async def on_ready():

    await bot.tree.sync()

    print(
        f"Logged in as {bot.user}"
    )



@bot.tree.command(
    name="fleet",
    description="Show tracked aircraft"
)
async def fleet(interaction: discord.Interaction):

    aircraft = get_tracked_aircraft()


    if not aircraft:

        await interaction.response.send_message(
            "No aircraft currently tracked."
        )

        return



    message = (
        "✈ **FlightWatch Fleet**\n\n"
    )


    for plane in aircraft:


        icao24 = plane[0]

        registration = plane[1] or icao24.upper()

        manufacturer = plane[2] or ""

        model = plane[3] or "Unknown"

        operator = plane[4] or "Unknown"

        category = plane[5] or "Unknown"



        message += (

            f"**{registration}**\n"

            f"{manufacturer} {model}\n"

            f"Operator: `{operator}`\n"

            f"Category: `{category}`\n\n"

        )



    await interaction.response.send_message(
        message
    )





@bot.tree.command(
    name="track",
    description="Track an aircraft by registration"
)
@app_commands.describe(
    registration="Aircraft registration (example: D-ABYN)"
)
async def track(
    interaction: discord.Interaction,
    registration: str
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            icao24,
            registration,
            manufacturer,
            model,
            operator,
            category

        FROM aircraft_metadata

        WHERE registration = ?

        """,

        (
            registration.upper(),
        )
    )


    plane = cursor.fetchone()


    conn.close()



    if not plane:

        await interaction.response.send_message(
            "Aircraft not found in database."
        )

        return



    add_tracked_aircraft(

        plane[0],

        plane[1],

        str(interaction.user)

    )



    await interaction.response.send_message(

        f"✅ Now tracking **{plane[1]}**\n"

        f"{plane[2]} {plane[3]}\n"

        f"Operator: {plane[4]}\n"

        f"Category: {plane[5]}"

    )





bot.run(TOKEN)
