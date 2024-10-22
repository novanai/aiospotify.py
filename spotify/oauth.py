from __future__ import annotations

import base64
import datetime
import typing
import urllib.parse as parse

import aiohttp

from spotify import enums, errors, utils

__all__: typing.Sequence[str] = (
    "build_auth_token",
    "AuthorizationCodeFlow",
    "ClientCredentialsFlow",
)


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

    Spotify Reference: <https://developer.spotify.com/documentation/web-api/tutorials/code-flow>

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
        self.access_token: str = access_token
        self.token_type: str = token_type
        self.expires_in: datetime.timedelta = expires_in
        self.scopes: list[enums.Scope] = scopes
        self.refresh_token: str = refresh_token

        self.client_id: str = client_id
        self.client_secret: str | None = client_secret

        self.expires_at: datetime.datetime = (
            datetime.datetime.now(datetime.timezone.utc) + expires_in
        )

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
                "Only one of client_secret and code_verifier may be provided, depending on "
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
            if not r.ok:
                raise errors.APIError(r.status, r.reason)

            data = await r.json()

            if client_secret:
                return cls(
                    access_token=data["access_token"],
                    token_type=data["token_type"],
                    expires_in=datetime.timedelta(seconds=data["expires_in"]),
                    scopes=[enums.Scope(scope) for scope in scopes.split(" ")]
                    if (scopes := data.get("scope"))
                    else [],
                    refresh_token=data["refresh_token"],
                    client_id=client_id,
                    client_secret=client_secret,
                )
            else:
                return cls(
                    access_token=data["access_token"],
                    token_type=data["token_type"],
                    expires_in=datetime.timedelta(seconds=data["expires_in"]),
                    scopes=[enums.Scope(scope) for scope in scopes.split(" ")]
                    if (scopes := data.get("scope"))
                    else [],
                    refresh_token=data["refresh_token"],
                    client_id=client_id,
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
            if not r.ok:
                raise errors.APIError(r.status, r.reason)

            data = await r.json()

            self.access_token = data["access_token"]
            self.token_type = data["token_type"]
            self.scopes = (
                [enums.Scope(scope) for scope in scopes.split(" ")]
                if (scopes := data.get("scope"))
                else []
            )
            self.expires_in = datetime.timedelta(seconds=data["expires_in"])
            self.expires_at = datetime.datetime.now(datetime.timezone.utc) + self.expires_in
            self.refresh_token = data.get("refresh_token") or self.refresh_token


class ClientCredentialsFlow:
    """Implementation to help with the Client Credentials Flow by storing and refreshing access
    tokens.

    Spotify Reference: <https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow>

    Parameters
    ----------
    access_token : str
        An access token that can be used in API calls.
    token_type : str
        How the access token may be used.
    expires_in : datetime.timedelta
        The time period for which the access token is valid.
    client_id : str
        The client's ID.
    client_secret : str
        The client's secret.
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
        self.access_token: str = access_token
        self.token_type: str = token_type
        self.expires_in: datetime.timedelta = expires_in

        self.client_id: str = client_id
        self.client_secret: str = client_secret

        self.expires_at: datetime.datetime = (
            datetime.datetime.now(datetime.timezone.utc) + expires_in
        )

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
        data = await cls.request_access_token(client_id, client_secret)

        return cls(
            access_token=data["access_token"],
            token_type=data["token_type"],
            expires_in=datetime.timedelta(seconds=data["expires_in"]),
            client_id=client_id,
            client_secret=client_secret,
        )

    async def validate_token(self) -> None:
        if datetime.datetime.now(datetime.timezone.utc) > self.expires_at:
            await self.refresh_access_token()

    async def refresh_access_token(self):
        data = await self.request_access_token(self.client_id, self.client_secret)

        self.access_token = data["access_token"]
        self.token_type = data["token_type"]
        self.expires_in = datetime.timedelta(seconds=data["expires_in"])
        self.expires_at = datetime.datetime.now(datetime.timezone.utc) + self.expires_in

    @classmethod
    async def request_access_token(
        cls, client_id: str, client_secret: str
    ) -> dict[str, typing.Any]:
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
            if not r.ok:
                raise errors.APIError(r.status, r.reason)

            return await r.json()


# MIT License
#
# Copyright (c) 2022-present novanai
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
