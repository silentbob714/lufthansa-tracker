import discord

from discord import app_commands

from discord.ext import commands

from database import (
    add_tracked_aircraft,
    remove_tracked_aircraft,
    get_connection
)



class Aircraft(commands.Cog):

    def __init__(self, bot):

        self.bot = bot



    @app_commands.command(
        name="track",
        description="Track an aircraft by registration"
    )
    @app_commands.describe(
        registration="Aircraft registration (example: D-ABYN)"
    )
    async def track(
        self,
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





    @app_commands.command(
        name="untrack",
        description="Stop tracking an aircraft"
    )
    @app_commands.describe(
        registration="Aircraft registration (example: D-ABYN)"
    )
    async def untrack(
        self,
        interaction: discord.Interaction,
        registration: str
    ):

        removed = remove_tracked_aircraft(
            registration.upper()
        )


        if removed:

            await interaction.response.send_message(

                f"🛑 Stopped tracking **{registration.upper()}**"

            )

        else:

            await interaction.response.send_message(

                f"Aircraft **{registration.upper()}** was not found."

            )





    @app_commands.command(
        name="lookup",
        description="Lookup aircraft information"
    )
    @app_commands.describe(
        registration="Aircraft registration (example: D-AING)"
    )
    async def lookup(
        self,
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
                type_designator,
                operator,
                owner,
                country,
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



        embed = discord.Embed(

            title="✈ Aircraft Lookup",

            description=f"**{plane[1]}**"

        )


        embed.add_field(

            name="Aircraft",

            value=f"{plane[2]} {plane[3]}",

            inline=False

        )


        embed.add_field(

            name="ICAO24",

            value=plane[0],

            inline=True

        )


        embed.add_field(

            name="Operator",

            value=plane[5] or "Unknown",

            inline=True

        )


        embed.add_field(

            name="Owner",

            value=plane[6] or "Unknown",

            inline=True

        )


        embed.add_field(

            name="Country",

            value=plane[7] or "Unknown",

            inline=True

        )


        embed.add_field(

            name="Category",

            value=plane[8] or "Unknown",

            inline=True

        )


        await interaction.response.send_message(

            embed=embed

        )





async def setup(bot):

    await bot.add_cog(
        Aircraft(bot)
    )
