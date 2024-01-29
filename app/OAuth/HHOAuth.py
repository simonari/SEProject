import aiohttp
from dotenv import load_dotenv
import os
import webbrowser

from starlette.requests import Request

load_dotenv()


class ImproperlyConfiguredEnvVariables(Exception):
    """Raises if """


class ClientIDMissingEnv(ImproperlyConfiguredEnvVariables):
    """Raises if CLIENT_ID not persists in .env file"""


class ClientSecretMissingEnv(ImproperlyConfiguredEnvVariables):
    """Raises if CLIENT_SECRET not persists in .env file"""


class HHOAuth:
    _base_url: str = "https://api.hh.ru/"
    _login_url: str = "https://hh.ru/oauth/"
    _response_type: str = "code"
    _grant_type: str = "authorization_code"
    _redirect_uri: str = "localhost:8000/auth_code"

    def __init__(self):
        self._client_id, self._client_secret = self._load_secrets()

    def _load_secrets(self) -> tuple[str, str]:
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")

        self._validate_secrets(client_id, client_secret)

        return client_id, client_secret

    @staticmethod
    def _validate_secrets(client_id, client_secret):
        if client_id is None:
            raise ClientIDMissingEnv

        if client_secret is None:
            raise ClientSecretMissingEnv

    async def code_redirect(self):
        webbrowser.open_new_tab(self._assemble_code_url())

    def _assemble_code_url(self) -> str:
        return f"{self._login_url}?response_type={self._response_type}&client_id={self._client_id}&redirect_uri={self._redirect_uri}"

    async def get_auth_code(self, request: Request) -> str:
        return request.query_params.get("code")

    async def get_access_token(self, auth_code: str) -> str:
        async with aiohttp.ClientSession(self._base_url) as session:
            response = await session.get("token", params=self.assemble_access_params(auth_code))

            content: dict[str, str] = await response.json()

        return content["access_token"]

    def assemble_access_params(self, auth_code) -> dict[str, str]:
        return {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "code": auth_code,
            "grant_type": self._grant_type,
            "redirect_uri": self._redirect_uri
        }