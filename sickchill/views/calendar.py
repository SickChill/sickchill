import datetime

from tornado.web import authenticated

from sickchill import logger, settings
from sickchill.helper import try_int

from ..oldbeard import db, network_timezones
from .index import BaseHandler


class CalendarHandler(BaseHandler):
    def get(self):
        if settings.CALENDAR_UNPROTECTED:
            self.write(self.calendar())
        else:
            self.calendar_auth()

    @authenticated
    def calendar_auth(self):
        self.write(self.calendar())

    # Raw iCalendar implementation by Pedro Jose Pereira Vieito (@pvieito).
    #
    # iCalendar (iCal) - Standard RFC 5545 <http://tools.ietf.org/html/rfc5546>
    # Works with iCloud, Google Calendar and Outlook.
    def calendar(self):
        """Provides a subscribeable URL for iCal subscriptions"""

        logger.info(f"Receiving iCal request from {self.request.remote_ip}")

        # Create a iCal string
        ical = "BEGIN:VCALENDAR\r\n"
        ical += "VERSION:2.0\r\n"
        ical += "X-WR-CALNAME:SickChill\r\n"
        ical += "X-WR-CALDESC:SickChill\r\n"
        ical += "PRODID://SickChill Upcoming Episodes//\r\n"

        future_weeks = try_int(self.get_argument("future", "52"), 52)
        past_weeks = try_int(self.get_argument("past", "52"), 52)

        # Limit dates
        past_date = (datetime.date.today() + datetime.timedelta(weeks=-past_weeks)).toordinal()
        future_date = (datetime.date.today() + datetime.timedelta(weeks=future_weeks)).toordinal()

        # Get all the shows that are not paused and are currently on air (from kjoconnor Fork)
        main_db_con = db.DBConnection()
        # noinspection PyPep8
        calendar_shows = main_db_con.select(
            "SELECT show_name, indexer_id, network, airs, runtime FROM tv_shows WHERE "
            "( status = 'Continuing' OR status = 'Returning Series' ) AND paused != '1'"
        )
        for show in calendar_shows:
            # Get all episodes of this show airing between today and next month
            episode_list = main_db_con.select(
                "SELECT indexerid, name, season, episode, description, airdate FROM tv_episodes WHERE airdate >= ? AND airdate < ? AND showid = ?",
                (past_date, future_date, int(show["indexer_id"])),
            )

            for episode in episode_list:
                air_date_time = network_timezones.parse_date_time(episode["airdate"], show["airs"], show["network"]).astimezone(datetime.timezone.utc)
                air_date_time_end = air_date_time + datetime.timedelta(minutes=try_int(show["runtime"], 60))

                # Create event for episode
                ical += "BEGIN:VEVENT\r\n"
                ical += f'DTSTART:{air_date_time.strftime("%Y%m%d")}T{air_date_time.strftime("%H%M%S")}Z\r\n'
                ical += f'DTEND:{air_date_time_end.strftime("%Y%m%d")}T{air_date_time_end.strftime("%H%M%S")}Z\r\n'
                if settings.CALENDAR_ICONS:
                    ical += "X-GOOGLE-CALENDAR-CONTENT-ICON:https://sickchill.github.io/images/ico/favicon-16.png\r\n"
                    ical += "X-GOOGLE-CALENDAR-CONTENT-DISPLAY:CHIP\r\n"
                ical += f'SUMMARY: {show["show_name"]} - {episode["season"]}x{episode["episode"]} - {episode["name"]}\r\n'
                ical += f'UID:SickChill-{datetime.date.today().isoformat()}-{show["show_name"].replace(" ", "-")}-S{episode["season"]}E{episode["episode"]}\r\n'
                ical += f'DESCRIPTION:{show["airs"] or "(Unknown airs)"} on {show["network"] or "Unknown network"}'
                if episode["description"]:
                    ical += f' \\n\\n {episode["description"].splitlines()[0]}'
                ical += "\r\nEND:VEVENT\r\n"

        # Ending the iCal
        ical += "END:VCALENDAR"

        return ical
