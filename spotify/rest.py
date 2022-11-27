from __future__ import annotations

import typing as t

import aiohttp

import spotify
from spotify import models, utils

if t.TYPE_CHECKING:
    from spotify import enums, oauth

import json


class REST:
    """An implementation to make API calls with.

    Parameters
    ----------
    access_manager : oauth.AuthorizationCodeFlowAccessManager | oauth.ClientCredentialsFlowAccessManager
        Access manager to use for requests.
    """

    def __init__(
        self,
        access_manager: oauth.AuthorizationCodeFlowAccessManager
        | oauth.ClientCredentialsFlowAccessManager,
    ) -> None:
        self.access = access_manager

    async def get(self, url: str, query: dict[str, t.Any]) -> dict[str, t.Any]:
        if not hasattr(self, "access"):
            raise RuntimeError("Didn't request an access token, did you? Idot.")
        async with aiohttp.request(
            "GET",
            f"{spotify.BASE_URL}/{url}",
            params=utils.dict_work(query),
            headers={
                "Authorization": f"Bearer {self.access.access_token}",
                "Content-Type": "application/json",
            },
        ) as r:
            r.raise_for_status()
            json.dump(await r.json(), open("./samples/sample.json", "w"), indent=4)
            return await r.json()

    async def get_album(
        self, album_id: str, *, market: str | None = None
    ) -> models.Album:
        """Get Spotify catalog information for a single album.

        Parameters
        ----------
        album_id : str
            The ID of the album.
        market : str | None
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Album
            The requested album.
        """
        return models.Album.from_payload(
            await self.get(f"albums/{album_id}", {"market": market})
        )

    async def get_several_albums(
        self, album_ids: list[str], *, market: str | None = None
    ) -> list[models.Album]:
        """Get Spotify catalog information for multiple albums.

        Parameters
        ----------
        album_ids : list[str]
            A list of albums IDs.
        market : str | None
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        list[models.Album]
            The requested albums.
        """
        return [
            models.Album.from_payload(alb)
            for alb in (
                await self.get("albums", {"ids": ",".join(album_ids), "market": market})
            )["albums"]
        ]

    async def get_album_tracks(
        self,
        album_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
        market: str | None = None,
    ) -> models.Paginator[models.Track]:
        """Get Spotify catalog information about an album's tracks.

        Parameters
        ----------
        album_id : str
            The ID of the album.
        limit : int | None
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int | None
            The index of the first item to return. Default: 0 (the first item).
        market : int | None
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Paginator[models.Track]
            A paginator who's items are a list of tracks.
        """
        return models.Paginator.from_payload(
            await self.get(
                f"albums/{album_id}/tracks",
                {"limit": limit, "offset": offset, "market": market},
            ),
            models.Track,
        )

    async def get_users_saved_albums(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        market: str | None = None,
    ) -> models.Paginator[models.Album]:
        """Get a list of the albums saved in the current Spotify user's 'Your Music' library.

        Parameters
        ----------
        limit : int | None
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int | None
            The index of the first item to return. Default: 0 (the first item).
        market : int | None
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Paginator[models.Album]
            A paginator who's items are a list of albums.
        """
        return models.Paginator.from_payload(
            await self.get(
                "me/albums", {"limit": limit, "offset": offset, "market": market}
            ),
            models.Album,
        )
