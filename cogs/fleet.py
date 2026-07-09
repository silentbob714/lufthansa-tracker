import discord

from discord.ext import commands

from database import get_tracked_aircraft, get_connection



class Fleet(commands.Cog):

    def __init__(self, bot):

        self.bot = bot



    @discord.app_commands.command(
        name="fleet",
        description="Show tracked aircraft"
    )
    async def fleet(
        self,
        interaction: discord.Interaction
    ):

        aircraft = get_tracked_aircraft()



        if not aircraft:

            await interaction.response.send_message(
                "No aircraft currently tracked."
            )

            return



        embed = discord.Embed(

            title="✈ FlightWatch Fleet",

            description="Currently tracked aircraft"

        )



        conn = get_connection()

        cursor = conn.cursor()



        for plane in aircraft:

            icao24 = plane[0]

            registration = plane[1] or icao24.upper()

            manufacturer = plane[2] or ""

            model = plane[3] or "Unknown"

            operator = plane[4] or "Unknown"

            category = plane[5] or "Unknown"



            cursor.execute(
                """
                SELECT

                    status,
                    callsign,
                    altitude,
                    speed,
                    latitude,
                    longitude,
                    last_seen

                FROM aircraft_state

                WHERE icao24 = ?

                """,

                (
                    icao24,
                )

            )


            state = cursor.fetchone()



            if state:

                status = state[0] or "Unknown"

                callsign = state[1] or "Unknown"

                altitude = (

                    f"{state[2]} ft"

                    if state[2]

                    else "Unknown"

                )

                speed = (

                    f"{state[3]} kts"

                    if state[3]

                    else "Unknown"

                )

                position = (

                    f"{state[4]}, {state[5]}"

                    if state[4] and state[5]

                    else "Unknown"

                )

                last_seen = state[6] or "Unknown"



            else:

                status = "No live data"

                callsign = "Unknown"

                altitude = "Unknown"

                speed = "Unknown"

                position = "Unknown"

                last_seen = "Unknown"



            embed.add_field(

                name=registration,

                value=(

                    f"{manufacturer} {model}\n"

                    f"Operator: `{operator}`\n"

                    f"Status: `{status}`\n"

                    f"Altitude: `{altitude}`\n"

                    f"Speed: `{speed}`\n"

                    f"Callsign: `{callsign}`\n"

                    f"Position: `{position}`\n"

                    f"Last Seen: `{last_seen}`"

                ),

                inline=False

            )



        conn.close()



        await interaction.response.send_message(

            embed=embed

        )





async def setup(bot):

    await bot.add_cog(

        Fleet(bot)

    )
