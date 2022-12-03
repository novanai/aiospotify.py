from __future__ import annotations

import typing as t

import aiohttp

import spotify
from spotify import errors, models, utils

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

    async def check_access(self) -> None:
        if not hasattr(self, "access"):
            raise RuntimeError("Didn't request an access token, did you? Idot.")
        await self.access.validate_token()

    async def request(self, method: str, url: str, query: dict[str, t.Any]) -> t.Any:
        await self.check_access()

        async with aiohttp.request(
            method,
            f"{spotify.BASE_URL}/{url}",
            params=utils.dict_work(query),
            headers={
                "Authorization": f"Bearer {self.access.access_token}",
                "Content-Type": "application/json",
            },
        ) as r:
            # No data to load, but status 200 OK
            # TODO: make a custom error for this
            try:
                data = await r.json()
            except aiohttp.ContentTypeError:
                return

            # json.dump(data, open("./samples/sample.json", "w"), indent=4)

            if not r.ok:
                raise errors.APIError.from_payload(data["error"])
            return data

    async def get(self, url: str, query: dict[str, t.Any]) -> t.Any:
        return await self.request("GET", url, query)

    async def put(self, url: str, query: dict[str, t.Any]) -> t.Any:
        return await self.request("PUT", url, query)

    async def delete(self, url: str, query: dict[str, t.Any]) -> t.Any:
        return await self.request("DELETE", url, query)

    async def get_album(
        self, album_id: str, *, market: str | None = None
    ) -> models.Album:
        """Get Spotify catalog information for a single album.

        Parameters
        ----------
        album_id : str
            The ID of the album.
        market : str, optional
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
        """Get Spotify catalog information for several albums.

        Parameters
        ----------
        album_ids : list[str]
            A list of album IDs.
        market : str, optional
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
        limit : int, optional
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, optional
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
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
        """Get a list of the albums saved in the current user's 'Your Music' library.

        Parameters
        ----------
        limit : int, optional
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, optional
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
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

    async def save_albums_for_user(
        self,
        album_ids: list[str],
    ) -> None:  # TODO: Maybe return a status code on success?
        """Save one or more albums to the current user's 'Your Music' library.

        Parameters
        ----------
        album_ids : list[str]
            A list of album IDs. Maximum: 50.
        """
        await self.put("me/albums", {"ids": album_ids})

    async def remove_users_saved_albums(self, album_ids: list[str]) -> None:
        """Remove one or more albums from the current user's 'Your Music' library.

        Parameters
        ----------
        album_ids : list[str]
            A list of albums IDs. Maximum: 50.
        """
        await self.delete("me/albums", {"ids": album_ids})

    async def check_users_saved_albums(self, album_ids: list[str]) -> list[bool]:
        """Check if one or more albums is already saved in the current user's 'Your Music' library.

        Parameters
        ----------
        album_ids : list[str]
            A list of albums IDs. Maximum: 20.

        Returns
        -------
        list[bool]
            A list of booleans.
        """
        return await self.get("me/albums/contains", {"ids": album_ids})

    async def get_new_releases(
        self,
        *,
        country: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> models.Paginator[models.Album]:
        """Get a list of new album releases featured in Spotify (shown, for example, on a Spotify player's "Browse" tab).

        Parameters
        ----------
        country : str, optional
            Only get content relevant to this country.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.
        limit : int, optional
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, optional
            The index of the first item to return. Default: 0 (the first item).

        Returns
        -------
        models.Paginator[models.Album]
            A paginator who's items are a list of albums.
        """
        return models.Paginator.from_payload(
            (
                await self.get(
                    "browse/new-releases",
                    {"country": country, "limit": limit, "offset": offset},
                )
            )["albums"],
            models.Album,
        )

    async def get_artist(self, artist_id: str) -> models.Artist:
        """Get Spotify catalog information for a single artist.

        Parameters
        ----------
        artist_id : str
            The ID of the artist.

        Returns
        -------
        models.Artist
            The requested artist.
        """
        return models.Artist.from_payload(await self.get(f"artists/{artist_id}", {}))

    async def get_several_artists(self, artist_ids: list[str]) -> list[models.Artist]:
        """Get Spotify catalog information for several artists.

        Parameters
        ----------
        artist_ids : list[str]
            A list of artist IDs.

        Returns
        -------
        list[models.Artist]
            The requested artists.
        """
        return [
            models.Artist.from_payload(art)
            for art in (await self.get("artists", {"ids": ",".join(artist_ids)}))[
                "artists"
            ]
        ]

    async def get_artists_albums(
        self,
        artist_id: str,
        *,
        include_groups: list[enums.AlbumGroup] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        market: str | None = None,
    ) -> models.Paginator[models.Album]:
        """Get Spotify catalog information about an artist's albums.

        Parameters
        ----------
        artist_id : str
            The ID of the artist.
        include_groups : list[enums.AlbumGroup], optional
            Used to filter the type of items returned. If not specified, all album types will be returned.
        limit : int, optional
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, optional
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Paginator[models.Album]
            A paginator who's items are a list of albums.
        """
        return models.Paginator.from_payload(
            await self.get(
                f"artists/{artist_id}/albums",
                {
                    "include_groups": ",".join(g.value for g in include_groups)
                    if include_groups
                    else None,
                    "limit": limit,
                    "offset": offset,
                    "market": market,
                },
            ),
            models.Album,
        )

    async def get_artists_top_tracks(
        self, artist_id: str, *, market: str
    ) -> list[models.Track]:
        """Get Spotify catalog information about an artist's top tracks.

        Parameters
        ----------
        artist_id : str
            The ID of the artist.
        market : str
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        list[models.Track]
            A list of tracks.
        """
        return [
            models.Track.from_payload(tra)
            for tra in (
                await self.get(f"artists/{artist_id}/top-tracks", {"market": market})
            )["tracks"]
        ]

    async def get_artists_related_artists(self, artist_id: str) -> list[models.Artist]:
        """Get Spotify catalog information about artists similar to a given artist.
        Similarity is based on analysis of the Spotify community's listening history.

        Parameters
        ----------
        artist_id : str
            The ID of the artist.

        Returns
        -------
        list[models.Artist]
            A list of artists.
        """
        return [
            models.Artist.from_payload(art)
            for art in (await self.get(f"artists/{artist_id}/related-artists", {}))[
                "artists"
            ]
        ]

    async def get_show(self, show_id: str, *, market: str | None = None) -> models.Show:
        """Get Spotify catalog information for a single show.

        Parameters
        ----------
        show_id : str
            The ID of the show.
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Show
            The requested show.
        """
        return models.Show.from_payload(
            await self.get(f"shows/{show_id}", {"market": market})
        )

    async def get_several_shows(
        self, show_ids: list[str], *, market: str | None = None
    ) -> list[models.Show]:
        """Get Spotify catalog information for several shows.

        Parameters
        ----------
        show_ids : list[str]
            A list of show IDs.
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        list[models.Show]
            The requested shows.
        """
        return [
            models.Show.from_payload(sho)
            for sho in (
                await self.get("shows", {"ids": ",".join(show_ids), "market": market})
            )["shows"]
        ]

    async def get_show_episodes(
        self,
        show_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
        market: str | None = None,
    ) -> models.Paginator[models.Episode]:
        """Get Spotify catalog information about an shows's episodes.

        Parameters
        ----------
        show_id : str
            The ID of the show.
        limit : int, optional
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, optional
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Paginator[models.Track]
            A paginator who's items are a list of tracks.
        """
        return models.Paginator.from_payload(
            await self.get(
                f"shows/{show_id}/episodes",
                {"limit": limit, "offset": offset, "market": market},
            ),
            models.Episode,
        )

    async def get_users_saved_shows(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        market: str | None = None,
    ) -> models.Paginator[models.Show]:
        """Get a list of the shows saved in the current user's library.

        Parameters
        ----------
        limit : int, optional
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, optional
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Paginator[models.Show]
            A paginator who's items are a list of shows.
        """
        return models.Paginator.from_payload(
            await self.get(
                "me/shows", {"limit": limit, "offset": offset, "market": market}
            ),
            models.Show,
        )

    async def save_shows_for_user(
        self,
        show_ids: list[str],
    ) -> None:
        """Save one or more shows to the current user's library.

        Parameters
        ----------
        show_ids : list[str]
            A list of show IDs. Maximum: 50.
        """
        await self.put("me/shows", {"ids": ",".join(show_ids)})

    async def remove_users_saved_shows(
        self, show_ids: list[str], *, market: str | None = None
    ) -> None:
        """Remove one or more shows from the current user's library.

        Parameters
        ----------
        show_ids : list[str]
            A list of shows IDs. Maximum: 50.
        market : str, optional
            Only modify content that is available in that market (I think, I'm honestly not sure why this field is included here).
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.
        """
        await self.delete("me/shows", {"ids": ",".join(show_ids), "market": market})

    async def check_users_saved_shows(self, show_ids: list[str]) -> list[bool]:
        """Check if one or more shows is already saved in the current user's library.

        Parameters
        ----------
        show_ids : list[str]
            A list of shows IDs. Maximum: 20.

        Returns
        -------
        list[bool]
            A list of booleans.
        """
        return await self.get("me/shows/contains", {"ids": ",".join(show_ids)})

    async def get_episode(
        self, episode_id: str, *, market: str | None = None
    ) -> models.Episode:
        """Get Spotify catalog information for a single episode.

        Parameters
        ----------
        episode_id : str
            The ID of the episode.
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Episode
            The requested episode.
        """
        return models.Episode.from_payload(
            await self.get(f"episodes/{episode_id}", {"market": market})
        )

    async def get_several_episodes(
        self, episode_ids: list[str], *, market: str | None = None
    ) -> list[models.Episode]:
        """Get Spotify catalog information for several episodes.

        Parameters
        ----------
        episode_ids : list[str]
            A list of episode IDs. Maximum: 50.
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        list[models.Episode]
            The requested episodes.
        """
        return [
            models.Episode.from_payload(epi)
            for epi in (
                await self.get(
                    "episodes", {"ids": ",".join(episode_ids), "market": market}
                )
            )["episodes"]
        ]

    async def get_users_saved_episodes(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        market: str | None = None,
    ) -> models.Paginator[models.Episode]:
        """Get a list of the episodes saved in the current user's library.

        .. warning::

            This API endpoint is in **beta** and could change without warning.
            I cannot guarantee that this method will always work.

        Parameters
        ----------
        limit : int, optional
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, optional
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Paginator[models.Episode]
            A paginator who's items are a list of episodes.
        """
        return models.Paginator.from_payload(
            await self.get(
                "me/episodes", {"limit": limit, "offset": offset, "market": market}
            ),
            models.Episode,
        )

    async def save_episodes_for_user(
        self,
        episode_ids: list[str],
    ) -> None:
        """Save one or more episodes to the current user's library.

        .. warning::

            This API endpoint is in **beta** and could change without warning.
            I cannot guarantee that this method will always work.

        Parameters
        ----------
        episode_ids : list[str]
            A list of episode IDs. Maximum: 50.
        """
        await self.put("me/episodes", {"ids": ",".join(episode_ids)})

    async def remove_users_saved_episodes(self, episode_ids: list[str]) -> None:
        """Remove one or more episodes from the current user's library.

        .. warning::

            This API endpoint is in **beta** and could change without warning.
            I cannot guarantee that this method will always work.

        Parameters
        ----------
        episode_ids : list[str]
            A list of episodes IDs. Maximum: 50.
        """
        await self.delete("me/episodes", {"ids": ",".join(episode_ids)})

    async def check_users_saved_episodes(self, episode_ids: list[str]) -> list[bool]:
        """Check if one or more episodes is already saved in the current user's library.

        .. warning::

            This API endpoint is in **beta** and could change without warning.
            I cannot guarantee that this method will always work.

        Parameters
        ----------
        episode_ids : list[str]
            A list of episodes IDs. Maximum: 50.

        Returns
        -------
        list[bool]
            A list of booleans.
        """
        return await self.get("me/episodes/contains", {"ids": ",".join(episode_ids)})

    async def get_audiobook(
        self, audiobook_id: str, *, market: str | None = None
    ) -> models.Audiobook:
        """Get Spotify catalog information for a single audiobook.

        .. note ::

            Audiobooks are only available for the US, UK, Ireland, New Zealand and Australia markets.

        Parameters
        ----------
        audiobook_id : str
            The ID of the audiobook.
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Audiobook
            The requested audiobook.
        """
        return models.Audiobook.from_payload(
            await self.get(f"audiobooks/{audiobook_id}", {"market": market})
        )

    async def get_several_audiobooks(
        self, audiobook_ids: list[str], *, market: str | None = None
    ) -> list[models.Audiobook]:
        """Get Spotify catalog information for several audiobooks.

        .. note ::

            Audiobooks are only available for the US, UK, Ireland, New Zealand and Australia markets.

        Parameters
        ----------
        audiobook_ids : list[str]
            A list of audiobook IDs. Maximum: 50.
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        list[models.Audiobook]
            The requested audiobooks.
        """
        return [
            models.Audiobook.from_payload(aud)
            for aud in (
                await self.get(
                    "audiobooks", {"ids": ",".join(audiobook_ids), "market": market}
                )
            )["audiobooks"]
        ]

    async def get_audiobook_chapters(
        self,
        audiobook_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
        market: str | None = None,
    ) -> models.Paginator[models.Chapter]:
        """Get Spotify catalog information about an audiobooks's chapters.

        .. note ::

            Audiobooks are only available for the US, UK, Ireland, New Zealand and Australia markets.

        Parameters
        ----------
        audiobook_id : str
            The ID of the audiobook.
        limit : int, optional
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, optional
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Paginator[models.Chapter]
            A paginator who's items are a list of chapters.
        """
        return models.Paginator.from_payload(
            await self.get(
                f"audiobooks/{audiobook_id}/chapters",
                {"limit": limit, "offset": offset, "market": market},
            ),
            models.Chapter,
        )

    async def get_users_saved_audiobooks(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> models.Paginator[models.Audiobook]:
        """Get a list of the audiobooks saved in the current user's library.

        Parameters
        ----------
        limit : int, optional
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, optional
            The index of the first item to return. Default: 0 (the first item).

        Returns
        -------
        models.Paginator[models.Audiobook]
            A paginator who's items are a list of audiobooks.
        """
        return models.Paginator.from_payload(
            await self.get("me/audiobooks", {"limit": limit, "offset": offset}),
            models.Audiobook,
        )

    async def save_audiobooks_for_user(
        self,
        audiobook_ids: list[str],
    ) -> None:
        """Save one or more audiobooks to the current user's library.

        Parameters
        ----------
        audiobook_ids : list[str]
            A list of audiobook IDs. Maximum: 50.
        """
        await self.put("me/audiobooks", {"ids": ",".join(audiobook_ids)})

    async def remove_users_saved_audiobooks(
        self,
        audiobook_ids: list[str],
    ) -> None:
        """Remove one or more audiobooks from the current user's library.

        Parameters
        ----------
        audiobook_ids : list[str]
            A list of audiobooks IDs. Maximum: 50.
        """
        await self.delete("me/audiobooks", {"ids": ",".join(audiobook_ids)})

    async def check_users_saved_audiobooks(
        self, audiobook_ids: list[str]
    ) -> list[bool]:
        """Check if one or more audiobooks is already saved in the current user's library.

        Parameters
        ----------
        audiobook_ids : list[str]
            A list of audiobooks IDs. Maximum: 50.

        Returns
        -------
        list[bool]
            A list of booleans.
        """
        return await self.get(
            "me/audiobooks/contains", {"ids": ",".join(audiobook_ids)}
        )
