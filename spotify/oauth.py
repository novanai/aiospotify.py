from __future__ import annotations

import base64
import datetime
import typing
import urllib.parse as parse

import aiohttp

from spotify import enums, utils


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
    """Implementation to help with the Authorization Code Flow by storing and refreshing access
    tokens.

    Spotify Reference: https://developer.spotify.com/documentation/general/guides/authorization/code-flow/

    Parameters
    ----------
    access_token : str
        An access token that can be used in API calls.
    token_type : str
        How the access token may be used.
    expires_in : datetime.timedelta
        The time period for which the access token is valid.
    scopes : list[enums.Scope]
        A list of scopes which have been granted for the access token.
    refresh_token : str
        Used to refresh the access token once it has expired.
    client_id : str
        The client's ID.
    client_secret : str, optional
        The client's secret. **Only required for *NON*-PKCE.**
    """

    @typing.overload
    def __init__(
        self,
        access_token: str,
        token_type: str,
        expires_in: datetime.timedelta,
        scopes: list[enums.Scope],
        refresh_token: str,
        *,
        client_id: str,
    ) -> None: ...

    @typing.overload
    def __init__(
        self,
        access_token: str,
        token_type: str,
        expires_in: datetime.timedelta,
        scopes: list[enums.Scope],
        refresh_token: str,
        *,
        client_id: str,
        client_secret: str,
    ) -> None: ...

    def __init__(
        self,
        access_token: str,
        token_type: str,
        expires_in: datetime.timedelta,
        scopes: list[enums.Scope],
        refresh_token: str,
        *,
        client_id: str,
        client_secret: str | None = None,
    ) -> None:
        self.access_token = access_token
        self.token_type = token_type
        self.scopes = scopes
        self.expires_in = expires_in
        self.refresh_token = refresh_token

        self.client_id = client_id
        self.client_secret = client_secret

        self.expires_at = datetime.datetime.now(datetime.timezone.utc) + expires_in

    # TODO: these should be using MISSING not None
    @typing.overload
    @staticmethod
    def build_url(
        client_id: str,
        redirect_uri: str,
        *,
        state: str | None = None,
        scopes: list[enums.Scope] | None = None,
        show_dialog: bool | None = None,
    ) -> str: ...

    @typing.overload
    @staticmethod
    def build_url(
        client_id: str,
        redirect_uri: str,
        *,
        state: str | None = None,
        scopes: list[enums.Scope] | None = None,
        show_dialog: bool | None = None,
        code_challenge: str,
    ) -> str: ...

    @staticmethod
    def build_url(
        client_id: str,
        redirect_uri: str,
        *,
        state: str | None = None,
        scopes: list[enums.Scope] | None = None,
        show_dialog: bool | None = None,
        code_challenge: str | None = None,
    ) -> str:
        """Build an authorization code flow url from the given parameters.

        Parameters
        ----------
        client_id : str
            The Client ID of your application.
        redirect_uri : str
            The URI to redirect to after the user grants or denies permission.
        state : str, optional
            This provides protection against attacks such as cross-site request forgery.
        scopes : list[enums.Scope], optional
            The scopes to request.
        show_dialog : bool, optional
            Whether or not to force the user to approve the app again if they've already done so.
        code_challenge : str, optional
            Code challenge. **Only required for PKCE.**

        Returns
        -------
        str
            The authorization code flow url.
        """
        query = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": " ".join(scope.value for scope in scopes) if scopes else None,
            "show_dialog": show_dialog,
        }
        if code_challenge:
            query["code_challenge_method"] = "S256"
            query["code_challenge"] = code_challenge

        query = parse.urlencode(utils.process_dict(query))

        return f"https://accounts.spotify.com/authorize?{query}"

    @typing.overload
    @classmethod
    async def build_from_access_token(
        cls,
        code: str,
        redirect_uri: str,
        *,
        client_id: str,
        client_secret: str,
    ) -> typing.Self: ...

    @typing.overload
    @classmethod
    async def build_from_access_token(
        cls,
        code: str,
        redirect_uri: str,
        *,
        client_id: str,
        code_verifier: str,
    ) -> typing.Self: ...

    @classmethod
    async def build_from_access_token(
        cls,
        code: str,
        redirect_uri: str,
        *,
        client_id: str,
        client_secret: str | None = None,
        code_verifier: str | None = None,
    ) -> typing.Self:
        """Request an access token from Spotify.

        Parameters
        ----------
        code : str
            The authorization code returned by Spotify after the user granted permission to access
            their account.
        redirect_uri : str
            The URI Spotify redirected to in the previous request.
        client_id : str
            The client's ID.
        client_secret : str, optional
            The client's secret. **Only required for *NON*-PKCE.**
        code_verifier : str, optional
            Must match the code_challenge passed to oauth.AuthorizationCodeFlow.build_url. **Only
            required for PKCE.**
        """
        if client_secret and code_verifier:
            raise ValueError(
                "Only one of client_secret and code_verifier is required, depending on "
                "whether or not you are implementing PKCE."
            )

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if client_secret:
            headers["Authorization"] = f"Basic {build_auth_token(client_id, client_secret)}"

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
        if code_verifier:
            data["client_id"] = client_id
            data["code_verifier"] = code_verifier

        async with aiohttp.request(
            "POST",
            "https://accounts.spotify.com/api/token",
            headers=headers,
            data=data,
        ) as r:
            r.raise_for_status()
            data = await r.json()

            return cls(
                data["access_token"],
                data["token_type"],
                datetime.timedelta(seconds=data["expires_in"]),
                [enums.Scope(scope) for scope in scopes.split(" ")]
                if (scopes := data.get("scope"))
                else [],
                data["refresh_token"],
                client_id=client_id,
                client_secret=client_secret,
            )

    async def validate_token(self) -> None:
        if datetime.datetime.now(datetime.timezone.utc) > self.expires_at:
            await self.refresh_access_token()

    async def refresh_access_token(self):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        if self.client_secret:
            headers["Authorization"] = (
                f"Basic {build_auth_token(self.client_id, self.client_secret)}"
            )
        else:
            data["client_id"] = self.client_id

        async with aiohttp.request(
            "POST",
            "https://accounts.spotify.com/api/token",
            headers=headers,
            data=data,
        ) as r:
            r.raise_for_status()
            data = await r.json()

            self.access_token = data["access_token"]
            self.token_type = data["token_type"]
            self.scopes = (
                [enums.Scope(scope) for scope in scopes.split(" ")]
                if (scopes := data.get("scope"))
                else [],
            )
            self.expires_in = datetime.timedelta(seconds=data["expires_in"])
            self.expires_at = datetime.datetime.now(datetime.timezone.utc) + self.expires_in
            self.refresh_token = data.get("refresh_token") or self.refresh_token


class ClientCredentialsFlow:
    """Implementation to help with the Client Credentials Flow by storing and refreshing access
    tokens.

    Spotify Reference: https://developer.spotify.com/documentation/general/guides/authorization/client-credentials/

    Parameters
    ----------
    access_token : str
        An access token that can be used in API calls.
    token_type : str
        How the access token may be used.
    expires_in : datetime.timedelta
        The time period for which the access token is valid.
    """

    def __init__(
        self,
        access_token: str,
        token_type: str,
        expires_in: datetime.timedelta,
        *,
        client_id: str,
        client_secret: str,
    ) -> None:
        self.access_token = access_token
        self.token_type = token_type
        self.expires_in = expires_in

        self.client_id = client_id
        self.client_secret = client_secret

        self.expires_at = datetime.datetime.now(datetime.timezone.utc) + expires_in

    @classmethod
    async def build_from_access_token(cls, client_id: str, client_secret: str) -> typing.Self:
        """Request an access token using the code returned by Spotify

        Parameters
        ----------
        client_id : str
            The client's ID.
        client_secret : str
            The client's secret.
        """
        async with aiohttp.request(
            "POST",
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {build_auth_token(client_id, client_secret)}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
            },
        ) as r:
            r.raise_for_status()
            data = await r.json()

            return cls(
                data["access_token"],
                data["token_type"],
                datetime.timedelta(seconds=data["expires_in"]),
                client_id=client_id,
                client_secret=client_secret,
            )

    async def validate_token(self) -> None:
        if datetime.datetime.now(datetime.timezone.utc) > self.expires_at:
            await self.refresh_access_token()

    async def refresh_access_token(self):
        async with aiohttp.request(
            "POST",
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {build_auth_token(self.client_id, self.client_secret)}",
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
            self.expires_at = datetime.datetime.now(datetime.timezone.utc) + self.expires_in
