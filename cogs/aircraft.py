import discord

from discord import app_commands
from discord.ext import commands

from database import (
    add_tracked_aircraft,
    remove_tracked_aircraft,
    get_connection
)


def format_event_type(event_type):
    if not event_type:
        return "Unknown Event"

    return event_type.replace("_", " ").strip().title()


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


    @app_commands.command(
        name="info",
        description="Show live aircraft status"
    )
    @app_commands.describe(
        registration="Aircraft registration (example: D-ABYN)"
    )
    async def info(
        self,
        interaction: discord.Interaction,
        registration: str
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                m.registration,
                m.manufacturer,
                m.model,
                m.operator,
                m.icao24,
                s.status,
                s.callsign,
                s.altitude,
                s.speed,
                s.latitude,
                s.longitude,
                s.last_seen
            FROM aircraft_metadata m
            LEFT JOIN aircraft_state s
                ON m.icao24 = s.icao24
            WHERE m.registration = ?
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
            title="✈ FlightWatch Live Info",
            description=f"**{plane[0]}**"
        )

        embed.add_field(
            name="Aircraft",
            value=f"{plane[1]} {plane[2]}",
            inline=False
        )

        embed.add_field(
            name="Operator",
            value=plane[3] or "Unknown",
            inline=True
        )

        embed.add_field(
            name="ICAO24",
            value=plane[4],
            inline=True
        )

        embed.add_field(
            name="Status",
            value=plane[5] or "No current data",
            inline=True
        )

        embed.add_field(
            name="Callsign",
            value=plane[6] or "Unknown",
            inline=True
        )

        embed.add_field(
            name="Altitude",
            value=f"{plane[7]} ft" if plane[7] else "Unknown",
            inline=True
        )

        embed.add_field(
            name="Speed",
            value=f"{plane[8]} knots" if plane[8] else "Unknown",
            inline=True
        )

        if plane[9] is not None and plane[10] is not None:
            embed.add_field(
                name="Position",
                value=f"{plane[9]}, {plane[10]}",
                inline=False
            )

        embed.add_field(
            name="Last Seen",
            value=plane[11] or "Unknown",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed
        )


    @app_commands.command(
        name="history",
        description="Show recent events for an aircraft"
    )
    @app_commands.describe(
        aircraft=(
            "Aircraft registration or ICAO24 "
            "(example: D-ABYN or 3c4b2e)"
        )
    )
    async def history(
        self,
        interaction: discord.Interaction,
        aircraft: str
    ):

        aircraft_input = aircraft.strip()
        registration_input = aircraft_input.upper()
        icao24_input = aircraft_input.lower()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                icao24,
                registration,
                manufacturer,
                model,
                operator
            FROM aircraft_metadata
            WHERE UPPER(registration) = ?
               OR LOWER(icao24) = ?
            LIMIT 1
            """,
            (
                registration_input,
                icao24_input
            )
        )

        plane = cursor.fetchone()

        if not plane:
            conn.close()

            await interaction.response.send_message(
                f"Aircraft **{aircraft_input}** was not found "
                "in the metadata database."
            )

            return

        icao24 = plane[0]
        registration = plane[1]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM aircraft_events
            WHERE LOWER(icao24) = ?
            """,
            (
                icao24.lower(),
            )
        )

        total_events = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT
                event_type,
                callsign,
                latitude,
                longitude,
                timestamp
            FROM aircraft_events
            WHERE LOWER(icao24) = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (
                icao24.lower(),
            )
        )

        events = cursor.fetchall()

        conn.close()

        if not events:
            await interaction.response.send_message(
                f"No event history has been recorded for "
                f"**{registration}**."
            )

            return

        aircraft_name = " ".join(
            part
            for part in (
                plane[2],
                plane[3]
            )
            if part
        )

        embed = discord.Embed(
            title="📜 FlightWatch Aircraft History",
            description=(
                f"**{registration}**\n"
                f"{aircraft_name or 'Aircraft type unknown'}\n"
                f"ICAO24: `{icao24}`"
            )
        )

        if plane[4]:
            embed.add_field(
                name="Operator",
                value=plane[4],
                inline=False
            )

        for index, event in enumerate(events, start=1):
            event_type = format_event_type(
                event[0]
            )

            callsign = event[1] or "Unknown"
            latitude = event[2]
            longitude = event[3]
            timestamp = event[4] or "Unknown"

            details = [
                f"**Recorded:** {timestamp}",
                f"**Callsign:** {callsign}"
            ]

            if latitude is not None and longitude is not None:
                map_url = (
                    "https://www.google.com/maps/search/"
                    f"?api=1&query={latitude},{longitude}"
                )

                details.append(
                    f"**Position:** "
                    f"[{latitude}, {longitude}]({map_url})"
                )

            embed.add_field(
                name=f"{index}. {event_type}",
                value="\n".join(details),
                inline=False
            )

        embed.set_footer(
            text=(
                f"Showing newest {len(events)} "
                f"of {total_events} recorded events"
            )
        )

        await interaction.response.send_message(
            embed=embed
        )


    @app_commands.command(
        name="stats",
        description="Show FlightWatch fleet statistics"
    )
    async def stats(
        self,
        interaction: discord.Interaction
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM aircraft_metadata
            """
        )

        metadata_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM tracked_aircraft
            WHERE active = 1
            """
        )

        tracked_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT
                COALESCE(
                    NULLIF(TRIM(s.status), ''),
                    'No current state'
                ) AS status_label,
                COUNT(*)
            FROM tracked_aircraft t
            LEFT JOIN aircraft_state s
                ON t.icao24 = s.icao24
            WHERE t.active = 1
            GROUP BY
                COALESCE(
                    NULLIF(TRIM(s.status), ''),
                    'No current state'
                )
            ORDER BY
                COUNT(*) DESC,
                status_label
            """
        )

        state_counts = cursor.fetchall()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM aircraft_events
            """
        )

        total_events = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT
                COALESCE(
                    NULLIF(TRIM(event_type), ''),
                    'unknown'
                ) AS event_label,
                COUNT(*)
            FROM aircraft_events
            GROUP BY
                COALESCE(
                    NULLIF(TRIM(event_type), ''),
                    'unknown'
                )
            ORDER BY
                COUNT(*) DESC,
                event_label
            """
        )

        event_counts = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                m.registration,
                s.callsign,
                s.status,
                s.last_seen
            FROM aircraft_state s
            LEFT JOIN aircraft_metadata m
                ON s.icao24 = m.icao24
            WHERE s.last_seen IS NOT NULL
            ORDER BY s.last_seen DESC
            LIMIT 1
            """
        )

        latest_state = cursor.fetchone()

        cursor.execute(
            """
            SELECT
                m.registration,
                e.icao24,
                e.event_type,
                e.callsign,
                e.timestamp
            FROM aircraft_events e
            LEFT JOIN aircraft_metadata m
                ON LOWER(e.icao24) = LOWER(m.icao24)
            ORDER BY e.id DESC
            LIMIT 1
            """
        )

        latest_event = cursor.fetchone()

        conn.close()

        embed = discord.Embed(
            title="📊 FlightWatch Statistics",
            description="Current fleet and event database summary"
        )

        embed.add_field(
            name="Fleet",
            value=(
                f"**Tracked aircraft:** {tracked_count}\n"
                f"**Metadata records:** {metadata_count}"
            ),
            inline=False
        )

        if state_counts:
            state_lines = []

            for state in state_counts:
                state_lines.append(
                    f"**{state[0]}:** {state[1]}"
                )

            state_summary = "\n".join(
                state_lines
            )

        else:
            state_summary = "No actively tracked aircraft."

        embed.add_field(
            name="Current Tracked States",
            value=state_summary,
            inline=False
        )

        if event_counts:
            event_lines = []

            for event in event_counts:
                event_lines.append(
                    f"**{format_event_type(event[0])}:** "
                    f"{event[1]}"
                )

            event_summary = "\n".join(
                event_lines
            )

        else:
            event_summary = "No events recorded."

        embed.add_field(
            name=f"Recorded Events — {total_events} Total",
            value=event_summary,
            inline=False
        )

        if latest_state:
            registration = (
                latest_state[0]
                or "Unknown registration"
            )

            callsign = (
                latest_state[1]
                or "Unknown"
            )

            status = (
                latest_state[2]
                or "Unknown"
            )

            last_seen = (
                latest_state[3]
                or "Unknown"
            )

            embed.add_field(
                name="Newest Stored Aircraft State",
                value=(
                    f"**Aircraft:** {registration}\n"
                    f"**Callsign:** {callsign}\n"
                    f"**Status:** {status}\n"
                    f"**Last seen:** {last_seen}"
                ),
                inline=False
            )

        else:
            embed.add_field(
                name="Newest Stored Aircraft State",
                value="No aircraft states have been recorded.",
                inline=False
            )

        if latest_event:
            registration = (
                latest_event[0]
                or latest_event[1]
                or "Unknown aircraft"
            )

            event_type = format_event_type(
                latest_event[2]
            )

            callsign = (
                latest_event[3]
                or "Unknown"
            )

            timestamp = (
                latest_event[4]
                or "Unknown"
            )

            embed.add_field(
                name="Newest Recorded Event",
                value=(
                    f"**Aircraft:** {registration}\n"
                    f"**Event:** {event_type}\n"
                    f"**Callsign:** {callsign}\n"
                    f"**Recorded:** {timestamp}"
                ),
                inline=False
            )

        else:
            embed.add_field(
                name="Newest Recorded Event",
                value="No aircraft events have been recorded.",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )


    @app_commands.command(
        name="recent",
        description="Show the newest events across the tracked fleet"
    )
    async def recent(
        self,
        interaction: discord.Interaction
    ):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM aircraft_events
            """
        )

        total_events = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT
                e.icao24,
                m.registration,
                m.manufacturer,
                m.model,
                e.event_type,
                e.callsign,
                e.latitude,
                e.longitude,
                e.timestamp
            FROM aircraft_events e
            LEFT JOIN aircraft_metadata m
                ON LOWER(e.icao24) = LOWER(m.icao24)
            ORDER BY e.id DESC
            LIMIT 10
            """
        )

        events = cursor.fetchall()

        conn.close()

        if not events:
            await interaction.response.send_message(
                "No fleet events have been recorded yet."
            )

            return

        embed = discord.Embed(
            title="🕘 Recent FlightWatch Events",
            description=(
                "Newest takeoffs, landings, and tracking "
                "events across the fleet"
            )
        )

        for index, event in enumerate(events, start=1):
            icao24 = event[0] or "Unknown"
            registration = event[1] or icao24
            manufacturer = event[2]
            model = event[3]
            event_type = format_event_type(
                event[4]
            )
            callsign = event[5] or "Unknown"
            latitude = event[6]
            longitude = event[7]
            timestamp = event[8] or "Unknown"

            aircraft_name = " ".join(
                part
                for part in (
                    manufacturer,
                    model
                )
                if part
            )

            details = [
                f"**Recorded:** {timestamp}",
                f"**Callsign:** {callsign}",
                f"**ICAO24:** `{icao24}`"
            ]

            if aircraft_name:
                details.append(
                    f"**Aircraft:** {aircraft_name}"
                )

            if latitude is not None and longitude is not None:
                map_url = (
                    "https://www.google.com/maps/search/"
                    f"?api=1&query={latitude},{longitude}"
                )

                details.append(
                    f"**Position:** "
                    f"[{latitude}, {longitude}]({map_url})"
                )

            embed.add_field(
                name=(
                    f"{index}. {registration} — "
                    f"{event_type}"
                ),
                value="\n".join(details),
                inline=False
            )

        embed.set_footer(
            text=(
                f"Showing newest {len(events)} "
                f"of {total_events} recorded events"
            )
        )

        await interaction.response.send_message(
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(
        Aircraft(bot)
    )
