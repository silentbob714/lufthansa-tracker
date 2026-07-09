import discord

from discord.ext import commands

from database import get_tracked_aircraft



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



        for plane in aircraft:

            icao24 = plane[0]

            registration = plane[1] or icao24.upper()

            manufacturer = plane[2] or ""

            model = plane[3] or "Unknown"

            operator = plane[4] or "Unknown"

            category = plane[5] or "Unknown"



            embed.add_field(

                name=registration,

                value=(

                    f"{manufacturer} {model}\n"

                    f"Operator: `{operator}`\n"

                    f"Category: `{category}`"

                ),

                inline=False

            )



        await interaction.response.send_message(

            embed=embed

        )





async def setup(bot):

    await bot.add_cog(

        Fleet(bot)

    )
