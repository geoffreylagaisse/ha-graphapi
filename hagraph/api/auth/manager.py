"""
Authentication Manager
Authenticate with Microsoft Online.
"""
import logging
import json
from typing import List, Optional
from urllib.parse import urlencode, quote_plus

from .models import OAuth2TokenResponse

import aiohttp
from yarl import URL

log = logging.getLogger("authentication")

DEFAULT_SCOPES = ["https://graph.microsoft.com/Presence.Read", "https://graph.microsoft.com/Presence.Read.All"]
AUTHORITY = "https://login.microsoftonline.com/common"
# ENDPOINT = 'https://graph.microsoft.com/v1.0/users'

class AuthenticationManager:
    def __init__(
        self,
        client_session: aiohttp.ClientSession,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: Optional[List[str]] = None,
    ):
        self.session: aiohttp.ClientSession = client_session
        self._client_id: str = client_id
        self._client_secret: str = client_secret
        self._redirect_uri: str = redirect_uri
        self._scopes: List[str] = scopes or DEFAULT_SCOPES

        self.oauth: OAuth2TokenResponse = None

    def generate_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate Microsoft Authorization URL."""
        query_string = {
            "client_id": self._client_id,
            "response_type": "code",
            "response_mode": "query",
            "approval_prompt": "auto",
            "code_challenge_method": "plain",
            "code_challenge": "YTFjNjI1OWYzMzA3MTI4ZDY2Njg5M2RkNmVjNDE5YmEyZGRhOGYyM2IzNjdmZWFhMTQ1ODg3NDcxY2Nl",
            "scope": " ".join(self._scopes),
            "redirect_uri": self._redirect_uri,
        }

        log.critical(">>>> oauth query_string: %s", query_string)

        if state:
            query_string["state"] = state

        return str(
            URL(AUTHORITY + "/oauth2/v2.0/authorize").with_query(query_string)
        )

    async def request_tokens(self, authorization_code: str) -> None:
        """Request all tokens."""
        log.critical("auth manager: requesting all tokens")
        self.oauth = await self.request_oauth_token(authorization_code)
        log.critical("self.oauth %s", self.oauth)

    async def refresh_tokens(self) -> None:
        """Refresh all tokens."""
        if not (self.oauth and self.oauth.is_valid()):
            self.oauth = await self.refresh_oauth_token()

    async def request_token(self, authorization_code: str) -> dict:
        """Request OAuth2 token."""
        log.critical("auth manager: requesting token (code %s)", authorization_code)
        return await self._oauth2_token_request(
            {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "authorization_code",
                "code": authorization_code,
                "scope": " ".join(self._scopes),
                "code_challenge": "YTFjNjI1OWYzMzA3MTI4ZDY2Njg5M2RkNmVjNDE5YmEyZGRhOGYyM2IzNjdmZWFhMTQ1ODg3NDcxY2Nl",
                "redirect_uri": self._redirect_uri,
                # "code_verifier": "9ED0A85C593A555C95CFC1CBC40705E1857CEA1C38575F78D0117A09E3B34A86"
            }
        )

    async def refresh_oauth_token(self) -> dict:
        """Refresh OAuth2 token."""
        log.critical("self.oauth: %s", self.oauth)
        return await self._oauth2_token_request(
            {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "authorization_code",
                "code": authorization_code,
                "scope": " ".join(self._scopes),
                "code_challenge": "YTFjNjI1OWYzMzA3MTI4ZDY2Njg5M2RkNmVjNDE5YmEyZGRhOGYyM2IzNjdmZWFhMTQ1ODg3NDcxY2Nl",
                "redirect_uri": self._redirect_uri,
                # "grant_type": "refresh_token",
                # "scope": " ".join(self._scopes),
                # "refresh_token": self.oauth.refresh_token,
                # "client_id": self._client_id,
                # "client_secret": self._client_secret,
                # "redirect_uri": self._redirect_uri,
                # "code_verifier": "YTFjNjI1OWYzMzA3MTI4ZDY2Njg5M2RkNmVjNDE5YmEyZGRhOGYyM2IzNjdmZWFhMTQ1ODg3NDcxY2Nl"
            }
        )

    async def _oauth2_token_request(self, data: dict) -> OAuth2TokenResponse:
        """Execute token requests."""
        log.critical("_oauth2_token_request raw: %s", data)

        data["code_verifier"] = data["code_challenge"]
        del data["code_challenge"]
        # del data["client_secret"]
        data["redirect_uri"] = self._redirect_uri

        log.critical("_oauth2_token_request updated: %s", data)
        if self._client_secret:
            data["client_secret"] = self._client_secret
            
        custom_headers = { 
            "Origin": self._redirect_uri
        }

        resp = await self.session.post(
            AUTHORITY + "/oauth2/v2.0/token", data=data
        )

        json = await resp.json()
        print("Token response: %s", OAuth2TokenResponse.parse_raw(await resp.text()))
        # resp.raise_for_status()
        return OAuth2TokenResponse.parse_raw(await resp.text())