from __future__ import annotations

from requests import Session

from gamdl.constants import *


class ItunesApi:
    def __init__(
        self,
        storefront: str = "us",
        language: str = "en-US",
        *args,
        **kwargs,
    ):
        self.storefront = storefront
        self.language = language
        self._setup_session()

    def _setup_session(self):
        self.storefront_id = STOREFRONT_IDS.get(self.storefront.upper())
        if not self.storefront_id:
            raise Exception(f"No storefront id for {self.storefront}")
        self.session = Session()
        self.session.params = {
            "country": self.storefront,
            "lang": self.language,
        }
        self.session.headers = {
            "X-Apple-Store-Front": f"{self.storefront_id} t:music31",
        }

    def get_resource(
        self,
        params: dict,
    ) -> dict:
        response = self.session.get(
            LOOKUP_API_URL,
            params=params,
        )
        if response.status_code != 200:
            raise Exception(f"Failed to get resource for {params}:\n{response.text}")
        return response.json()

    def get_itunes_page(
        self,
        resource_type: str,
        resource_id: str,
    ) -> dict:
        response = self.session.get(
            f"{ITUNES_PAGE_API_URL}/{resource_type}/{resource_id}"
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed to get itunes page for {resource_id}:\n{response.text}"
            )
        return response.json()
