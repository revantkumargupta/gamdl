from __future__ import annotations

import re
from http.cookiejar import MozillaCookieJar
from pathlib import Path

from requests import Session

from gamdl.constants import *


class AppleMusicApi:
    def __init__(
        self,
        cookies_location: Path = None,
        storefront: str = "us",
        language: str = "en-US",
        *args,
        **kwargs,
    ):
        self.cookies_location = cookies_location
        self.storefront = storefront
        self.language = language
        self._setup_session()

    def _setup_session(self):
        self.session = Session()
        if self.cookies_location:
            cookies = MozillaCookieJar(self.cookies_location)
            cookies.load(ignore_discard=True, ignore_expires=True)
            self.session.cookies.update(cookies)
            self.storefront = self.session.cookies.get_dict()["itua"]
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "content-type": "application/json",
                "Media-User-Token": self.session.cookies.get_dict().get(
                    "media-user-token", ""
                ),
                "x-apple-renewal": "true",
                "DNT": "1",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "origin": APPLE_MUSIC_HOMEPAGE_URL,
            }
        )
        home_page = self.session.get(APPLE_MUSIC_HOMEPAGE_URL).text
        index_js_uri = re.search(
            r"/(assets/index-legacy-[^/]+\.js)",
            home_page,
        ).group(1)
        index_js_page = self.session.get(
            f"{APPLE_MUSIC_HOMEPAGE_URL}/{index_js_uri}"
        ).text
        token = re.search('(?=eyJh)(.*?)(?=")', index_js_page).group(1)
        self.session.headers.update({"authorization": f"Bearer {token}"})
        self.session.params = {"l": self.language}

    def _get_resource(
        self,
        resource_type: str,
        resource_id: str,
        params: dict = None,
    ) -> dict:
        response = self.session.get(
            f"{CATALOG_API_URL}/{self.storefront}/{resource_type}/{resource_id}",
            params=params,
        )
        if (
            response.status_code != 200
            or not response.json().get("data")
            or not response.json()["data"][0].get("attributes")
        ):
            raise Exception(
                f"Failed to get resource for {resource_id}:\n{response.text}"
            )
        return response.json()["data"][0]

    def get_song(
        self,
        song_id: str,
        extend: str = "extendedAssetUrls",
        include: str = "lyrics",
    ) -> dict:
        return self._get_resource(
            "songs",
            song_id,
            {
                "extend": extend,
                "include": include,
            },
        )

    def get_music_video(
        self,
        music_video_id: str,
    ) -> dict:
        return self._get_resource("music-videos", music_video_id)

    def get_album(
        self,
        album_id: str,
        extend: str = "extendedAssetUrls",
    ) -> dict:
        return self._get_resource(
            "albums",
            album_id,
            {
                "extend": extend,
            },
        )

    def get_playlist(
        self,
        playlist_id: str,
        limit_tracks: int = 300,
        extend: str = "extendedAssetUrls",
    ) -> dict:
        return self._get_resource(
            "playlists",
            playlist_id,
            {
                "limit[tracks]": limit_tracks,
                "extend": extend,
            },
        )

    def get_webplayback(
        self,
        track_id: str,
    ) -> dict:
        response = self.session.post(
            WEBPLAYBACK_API_URL,
            json={
                "salableAdamId": track_id,
                "language": self.language,
            },
        )
        if response.status_code != 200 or not response.json().get("songList"):
            raise Exception(
                f"Failed to get webplayback for {track_id}:\n{response.text}"
            )
        return response.json()["songList"][0]

    def get_license(
        self,
        track_id: str,
        track_uri: str,
        challenge: str,
    ) -> str:
        response = self.session.post(
            LICENSE_API_URL,
            json={
                "challenge": challenge,
                "key-system": "com.widevine.alpha",
                "uri": track_uri,
                "adamId": track_id,
                "isLibrary": False,
                "user-initiated": True,
            },
        )
        if response.status_code != 200 or not response.json().get("license"):
            raise Exception(f"Failed to get license for {track_id}:\n{response.text}")
        return response.json()["license"]
