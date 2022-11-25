from __future__ import annotations

import base64
import datetime
import urllib.parse as parse

import aiohttp

from spotify import rest, utils


def build_auth_token(client_id: str, client_secret: str) -> str:
    """Build an authorization token from the client ID and secret.

    Parameters
    ----------
    client_id : str
        The client's ID.
    client_secret : str
        The client's secret.

    Returns
    -------
    str
        The authorization token.
    """
    token = f"{client_id}:{client_secret}".encode("utf-8")
    token = base64.urlsafe_b64encode(token)
    token = token.decode("utf-8")
    return token


class AuthorizationCodeFlow:
    """Implementation to help with the Authorization Code Flow.

    Spotify Reference: https://developer.spotify.com/documentation/general/guides/authorization/code-flow/

    Parameters
    ----------
    client_id : str
        The client's ID.
    client_secret : str
        The client's secret.
    """

    def __init__(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret

        self.auth_token = build_auth_token(client_id, client_secret)
        self.access: AuthorizationCodeFlowAccessManager | None = None
        self._rest: rest.REST | None = None

    @property
    def rest(self) -> rest.REST:
        if not self._rest:
            raise RuntimeError("Didn't authorize your access token, did you? Idot.")
        return self._rest

    def build_url(
        self,
        redirect_uri: str,
        *,
        state: str | None = None,
        scopes: list[str] | None = None,
        show_dialog: bool | None = None,
    ) -> str:
        """Build an authorization code flow url from the given parameters.

        Parameters
        ----------
        redirect_uri : str
            The URI to redirect to after the user grants or denies permission.
        state : str, optional
            This provides protection against attacks such as cross-site request forgery.
        scopes : list[str], optional
            A list of scopes. TODO: Change once I introduce enums
        show_dialog : bool, optional
            Whether or not to force the user to approve the app again if they've already done so.

        Returns
        -------
        str
            The authorization code flow url.
        """
        query = parse.urlencode(
            utils.dict_work(
                {
                    "client_id": self.client_id,
                    "response_type": "code",
                    "redirect_uri": redirect_uri,
                    "state": state,
                    "scope": " ".join(scopes) if scopes else None,
                    "show_dialog": show_dialog,
                }
            )
        )
        return f"https://accounts.spotify.com/authorize?{query}"

    async def request_access_token(
        self, code: str, redirect_uri: str
    ) -> AuthorizationCodeFlowAccessManager:
        """Request an access token using the code returned by Spotify.

        Parameters
        ----------
        code : str
            The authorization code returned by Spotify after the user granted permission to access their account.
        redirect_uri : str
            The URI Spotify redirected to in the previous request.

        Returns
        -------
        AccessManager
            The access token and relevant information.
        """
        async with aiohttp.request(
            "POST",
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {self.auth_token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
        ) as r:
            r.raise_for_status()
            data = await r.json()
            self.access = AuthorizationCodeFlowAccessManager(
                self.auth_token,
                data["access_token"],
                data["token_type"],
                datetime.timedelta(seconds=data["expires_in"]),
                data["scope"].split(" "),
                data["refresh_token"],
            )
            self._rest = rest.REST(self.access)
            return self.access


class AuthorizationCodeFlowAccessManager:
    """An implementation to manage API access by storing and refreshing access tokens (if necessary).

    Parameters
    ----------
    auth_token : str
        Base64 encoded `client_id:client_secret`.
    access_token : str
        An access token that can be used in API calls.
    token_type : str
        How the access token may be used.
    expires_in : datetime.datetime
        The time period for which the access token is valid.
    scopes : list[str]
        A list of scopes which have been granted for the access token.
    refresh_token : str
        Used to refresh the access token once it has expired.
    """

    def __init__(
        self,
        auth_token: str,
        access_token: str,
        token_type: str,
        expires_in: datetime.timedelta,
        scopes: list[str],  # TODO: Update with Scope enum
        refresh_token: str,
    ) -> None:
        self.auth_token = auth_token
        self.access_token = access_token
        self.token_type = token_type
        self.scopes = scopes
        self.expires_in = expires_in
        self.refresh_token = refresh_token

        self.expires_at = datetime.datetime.now(datetime.timezone.utc) + expires_in

    async def validate_token(self) -> None:
        if datetime.datetime.now(datetime.timezone.utc) > self.expires_at:
            await self.refresh_access_token()

    async def refresh_access_token(self):
        async with aiohttp.request(
            "POST",
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {self.auth_token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
        ) as r:
            r.raise_for_status()
            data = await r.json()
            self.access_token = data["access_token"]
            self.token_type = data["token_type"]
            self.scopes = data["scope"].split(" ")
            self.expires_in = datetime.timedelta(seconds=data["expires_in"])
            self.expires_at = (
                datetime.datetime.now(datetime.timezone.utc) + self.expires_in
            )
            self.refresh_token = data.get("refresh_token") or self.refresh_token


class AuthorizationCodeFlowWithPKCE:
    """Implementation to help with the Authorization Code Flow with the PKCE extension.

    Spotify Reference: https://developer.spotify.com/documentation/general/guides/authorization/code-flow/

    Parameters
    ----------
    client_id : str
        The client's ID.
    """

    def __init__(self, client_id: str) -> None:
        self.client_id = client_id

        self.access: AuthorizationCodeFlowWithPKCEAccessManager | None = None
        self._rest: rest.REST | None = None

    @property
    def rest(self) -> rest.REST:
        if not self._rest:
            raise RuntimeError("Didn't authorize your access token, did you? Idot.")
        return self._rest

    def build_url(
        self,
        redirect_uri: str,
        code_challenge: str,
        *,
        state: str | None = None,
        scopes: list[str] | None = None,
        show_dialog: bool | None = None,
    ) -> str:
        """Build an authorization code flow url from the given parameters.

        Parameters
        ----------
        redirect_uri : str
            The URI to redirect to after the user grants or denies permission.
        code_challenge : str
            Code challenge.
        state : str, optional
            This provides protection against attacks such as cross-site request forgery.
        scopes : list[str], optional
            A list of scopes. TODO: Change once I introduce enums
        show_dialog : bool, optional
            Whether or not to force the user to approve the app again if they've already done so.

        Returns
        -------
        str
            The authorization code flow url.
        """
        query = parse.urlencode(
            utils.dict_work(
                {
                    "client_id": self.client_id,
                    "response_type": "code",
                    "redirect_uri": redirect_uri,
                    "state": state,
                    "scope": " ".join(scopes) if scopes else None,
                    "show_dialog": show_dialog,
                    "code_challenge_method": "S256",
                    "code_challenge": code_challenge,
                }
            )
        )
        return f"https://accounts.spotify.com/authorize?{query}"

    async def request_access_token(
        self, code: str, redirect_uri: str, code_verifier: str
    ) -> AuthorizationCodeFlowWithPKCEAccessManager:
        """Request an access token using the code returned by Spotify.

        Parameters
        ----------
        code : str
            The authorization code returned by Spotify after the user granted permission to access their account.
        redirect_uri : str
            The URI Spotify redirected to in the previous request.
        code_verifier : str
            Must match the code_challenge passed to AuthorizationCodeFlowWithPKCE.build_url

        Returns
        -------
        AccessManager
            The access token and relevant information.
        """
        async with aiohttp.request(
            "POST",
            "https://accounts.spotify.com/api/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": self.client_id,
                "code_verifier": code_verifier,
            },
        ) as r:
            r.raise_for_status()
            data = await r.json()
            self.access = AuthorizationCodeFlowWithPKCEAccessManager(
                self.client_id,
                data["access_token"],
                data["token_type"],
                datetime.timedelta(seconds=data["expires_in"]),
                data["scope"].split(" "),
                data["refresh_token"],
            )
            self._rest = rest.REST(self.access)
            return self.access


class AuthorizationCodeFlowWithPKCEAccessManager:
    """An implementation to manage API access by storing and refreshing access tokens (if necessary).

    Parameters
    ----------
    client_id : str
        The client's ID.
    access_token : str
        An access token that can be used in API calls.
    token_type : str
        How the access token may be used.
    expires_in : datetime.datetime
        The time period for which the access token is valid.
    scopes : list[str]
        A list of scopes which have been granted for the access token.
    refresh_token : str
        Used to refresh the access token once it has expired.
    """

    def __init__(
        self,
        client_id: str,
        access_token: str,
        token_type: str,
        expires_in: datetime.timedelta,
        scopes: list[str],  # TODO: Update with Scope enum
        refresh_token: str,
    ) -> None:
        self.client_id = client_id
        self.access_token = access_token
        self.token_type = token_type
        self.scopes = scopes
        self.expires_in = expires_in
        self.refresh_token = refresh_token

        self.expires_at = datetime.datetime.now(datetime.timezone.utc) + expires_in

    async def validate_token(self) -> None:
        if datetime.datetime.now(datetime.timezone.utc) > self.expires_at:
            await self.refresh_access_token()

    async def refresh_access_token(self):
        async with aiohttp.request(
            "POST",
            "https://accounts.spotify.com/api/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
            },
        ) as r:
            r.raise_for_status()
            data = await r.json()
            self.access_token = data["access_token"]
            self.token_type = data["token_type"]
            self.scopes = data["scope"].split(" ")
            self.expires_in = datetime.timedelta(seconds=data["expires_in"])
            self.expires_at = (
                datetime.datetime.now(datetime.timezone.utc) + self.expires_in
            )
            self.refresh_token = data.get("refresh_token") or self.refresh_token


class ClientCredentialsFlow:
    """Implementation to help with the Client Credentials Flow.

    Spotify Reference: https://developer.spotify.com/documentation/general/guides/authorization/client-credentials/

    Parameters
    ----------
    client_id : str
        The client's ID.
    client_secret : str
        The client's secret.
    """

    def __init__(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret

        self.auth_token = build_auth_token(client_id, client_secret)
        self.access: ClientCredentialsFlowAccessManager | None = None
        self._rest: rest.REST | None = None

    @property
    def rest(self) -> rest.REST:
        if not self._rest:
            raise RuntimeError("Didn't authorize your access token, did you? Idot.")
        return self._rest

    async def request_access_token(self) -> ClientCredentialsFlowAccessManager:
        """Request an access token using the code returned by Spotify

        Returns
        -------
        AccessManager
            The access token and relevant information.
        """
        async with aiohttp.request(
            "POST",
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {self.auth_token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
            },
        ) as r:
            r.raise_for_status()
            data = await r.json()
            self.access = ClientCredentialsFlowAccessManager(
                self.auth_token,
                data["access_token"],
                data["token_type"],
                datetime.timedelta(seconds=data["expires_in"]),
            )
            self._rest = rest.REST(self.access)
            return self.access


class ClientCredentialsFlowAccessManager:
    """An implementation to manage API access by storing and refreshing access tokens (if necessary).

    Parameters
    ----------
    auth_token : str
        Base64 encoded `client_id:client_secret`.
    access_token : str
        An access token that can be used in API calls.
    token_type : str
        How the access token may be used.
    expires_in : datetime.datetime
        The time period for which the access token is valid.
    """

    def __init__(
        self,
        auth_token: str,
        access_token: str,
        token_type: str,
        expires_in: datetime.timedelta,
    ) -> None:
        self.auth_token = auth_token
        self.access_token = access_token
        self.token_type = token_type
        self.expires_in = expires_in

        self.expires_at = datetime.datetime.now(datetime.timezone.utc) + expires_in

    async def validate_token(self) -> None:
        if datetime.datetime.now(datetime.timezone.utc) > self.expires_at:
            await self.refresh_access_token()

    async def refresh_access_token(self):
        async with aiohttp.request(
            "POST",
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {self.auth_token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
            },
        ) as r:
            r.raise_for_status()
            data = await r.json()

            self.access_token = data["access_token"]
            self.token_type = data["token_type"]
            self.expires_in = datetime.timedelta(seconds=data["expires_in"])
            self.expires_at = (
                datetime.datetime.now(datetime.timezone.utc) + self.expires_in
            )
