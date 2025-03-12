import os

import requests
from babelfish import Language
from subliminal import Provider

from sickchill import logger, settings


class OpenSubtitlesRESTProvider(Provider):
    def __init__(self):
        self.apikey = settings.OPENSUBTITLES_APIKEY
        self.base_url = "https://api.opensubtitles.com/api/v1"
        self.session = requests.Session()
        self.session.headers.update({"Api-Key": self.apikey, "User-Agent": "SickChill v1.0", "Content-Type": "application/json"})
        self.token = None

    def login(self):
        if not settings.OPENSUBTITLES_USER or not settings.OPENSUBTITLES_PASS:
            logger.warning("OpenSubtitles username and password required for REST API")
            return False

        payload = {"username": settings.OPENSUBTITLES_USER, "password": settings.OPENSUBTITLES_PASS}
        try:
            response = self.session.post(f"{self.base_url}/login", json=payload)
            response.raise_for_status()
            data = response.json()
            self.token = data["token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return True
        except Exception as e:
            logger.error(f"Failed to login to OpenSubtitles REST API: {e}")
            return False

    def initialize(self):
        self.login()

    def terminate(self):
        self.session.close()

    def search_subtitles(self, video, languages, hearing_impaired=False):
        if not self.token and not self.login():
            return []

        subtitles = []
        query = {
            "query": video.series if hasattr(video, "series") else os.path.splitext(os.path.basename(video.name))[0],
            "languages": ",".join([lang.alpha2 for lang in languages]),
        }

        if hasattr(video, "season"):
            query["season"] = video.season
        if hasattr(video, "episode"):
            query["episode"] = video.episode

        try:
            response = self.session.get(f"{self.base_url}/subtitles", params=query)
            response.raise_for_status()
            data = response.json()

            for sub in data.get("data", []):
                subtitle = {
                    "id": sub["attributes"]["subtitle_id"],
                    "language": Language.fromopensubtitles(sub["attributes"]["language"]),
                    "download_link": sub["attributes"]["files"][0]["file_id"],
                    "hearing_impaired": sub["attributes"].get("hearing_impaired", False),
                    "release": sub["attributes"]["release"],
                }
                if hearing_impaired == subtitle["hearing_impaired"]:
                    subtitles.append(subtitle)

            return subtitles

        except Exception as e:
            logger.error(f"Error searching OpenSubtitles: {e}")
            return []

    def download_subtitle(self, subtitle):
        try:
            payload = {"file_id": subtitle["download_link"]}
            response = self.session.post(f"{self.base_url}/download", json=payload)
            response.raise_for_status()
            data = response.json()

            download_response = self.session.get(data["link"])
            download_response.raise_for_status()
            return download_response.content

        except Exception as e:
            logger.error(f"Error downloading subtitle from OpenSubtitles: {e}")
            return None
