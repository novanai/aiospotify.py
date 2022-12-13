from __future__ import annotations

import typing as t

import aiohttp

import spotify
from spotify import enums, errors, models, utils

if t.TYPE_CHECKING:
    from spotify import oauth

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
            data = await r.json() if r.content_type == "application/json" else None

            if not r.ok:
                if data and data.get("error"):
                    data = data["error"]
                else:
                    data = {"status": r.status, "message": r.reason}
                raise errors.APIError.from_payload(data)

            if data:
                json.dump(data, open("./samples/sample.json", "w"), indent=4)
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
            The IDs of the albums.
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
    ) -> None:
        """Save one or more albums to the current user's 'Your Music' library.

        Parameters
        ----------
        album_ids : list[str]
            The IDs of the albums. Maximum: 50.
        """
        await self.put("me/albums", {"ids": album_ids})

    async def remove_users_saved_albums(self, album_ids: list[str]) -> None:
        """Remove one or more albums from the current user's 'Your Music' library.

        Parameters
        ----------
        album_ids : list[str]
            The IDs of the albums. Maximum: 50.
        """
        await self.delete("me/albums", {"ids": album_ids})

    async def check_users_saved_albums(self, album_ids: list[str]) -> list[bool]:
        """Check if one or more albums is already saved in the current user's 'Your Music' library.

        Parameters
        ----------
        album_ids : list[str]
            The IDs of the albums. Maximum: 20.

        Returns
        -------
        list[bool]
            A list of booleans dictating whether or not the corresponding albums are already saved.
        """
        return await self.get("me/albums/contains", {"ids": album_ids})

    async def get_new_releases(
        self,
        *,
        country: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> models.Paginator[models.Album]:
        """Get a list of new album releases featured in Spotify (shown, for example, on a Spotify
        player's "Browse" tab).

        Parameters
        ----------
        country : str, optional
            Only get content relevant to that country.
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
            The IDs of the artists.

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
            The requested tracks.
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
            The requested artists.
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
            The IDs of the shows.
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
        models.Paginator[models.Episode]
            A paginator who's items are a list of episodes.
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
            The IDs of the shows. Maximum: 50.
        """
        await self.put("me/shows", {"ids": ",".join(show_ids)})

    async def remove_users_saved_shows(
        self, show_ids: list[str], *, market: str | None = None
    ) -> None:
        """Remove one or more shows from the current user's library.

        Parameters
        ----------
        show_ids : list[str]
            The IDs of the shows. Maximum: 50.
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
            The IDs of the shows. Maximum: 20.

        Returns
        -------
        list[bool]
            A list of booleans dictating whether or not the corresponding shows are already saved.
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
            The IDs of the episodes. Maximum: 50.
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

        Parameters
        ----------
        episode_ids : list[str]
            The IDs of the episodes. Maximum: 50.
        """
        await self.put("me/episodes", {"ids": ",".join(episode_ids)})

    async def remove_users_saved_episodes(self, episode_ids: list[str]) -> None:
        """Remove one or more episodes from the current user's library.

        .. warning::

            This API endpoint is in **beta** and could change without warning.

        Parameters
        ----------
        episode_ids : list[str]
            The IDs of the episodes. Maximum: 50.
        """
        await self.delete("me/episodes", {"ids": ",".join(episode_ids)})

    async def check_users_saved_episodes(self, episode_ids: list[str]) -> list[bool]:
        """Check if one or more episodes is already saved in the current user's library.

        .. warning::

            This API endpoint is in **beta** and could change without warning.

        Parameters
        ----------
        episode_ids : list[str]
            The IDs of the episodes. Maximum: 50.

        Returns
        -------
        list[bool]
            A list of booleans dictating whether or not the corresponding episodes are already saved.
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
            The IDs of the audiobooks. Maximum: 50.
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
            The IDs of the audiobooks. Maximum: 50.
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
            The IDs of the audiobooks. Maximum: 50.
        """
        await self.delete("me/audiobooks", {"ids": ",".join(audiobook_ids)})

    async def check_users_saved_audiobooks(
        self, audiobook_ids: list[str]
    ) -> list[bool]:
        """Check if one or more audiobooks is already saved in the current user's library.

        Parameters
        ----------
        audiobook_ids : list[str]
            The IDs of the audiobooks. Maximum: 50.

        Returns
        -------
        list[bool]
            A list of booleans dictating whether or not the corresponding audiobooks are already saved.
        """
        return await self.get(
            "me/audiobooks/contains", {"ids": ",".join(audiobook_ids)}
        )

    async def get_chapter(
        self, chapter_id: str, *, market: str | None = None
    ) -> models.Chapter:
        """Get Spotify catalog information for a single chapter.

        .. note ::

            Chapters are only available for the US, UK, Ireland, New Zealand and Australia markets.

        Parameters
        ----------
        chapter_id : str
            The ID of the chapter.
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Chapter
            The requested chapter.
        """
        return models.Chapter.from_payload(
            await self.get(f"chapters/{chapter_id}", {"market": market})
        )

    async def get_several_chapters(
        self, chapter_ids: list[str], *, market: str | None = None
    ) -> list[models.Chapter]:
        """Get Spotify catalog information for several chapters.

        .. note ::

            Chapters are only available for the US, UK, Ireland, New Zealand and Australia markets.

        Parameters
        ----------
        chapter_ids : list[str]
            The IDs of the chapters. Maximum: 50.
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        list[models.Chapter]
            The requested chapters.
        """
        return [
            models.Chapter.from_payload(cha)
            for cha in (
                await self.get(
                    "chapters", {"ids": ",".join(chapter_ids), "market": market}
                )
            )["chapters"]
        ]

    async def get_track(
        self, track_id: str, *, market: str | None = None
    ) -> models.Track:
        """Get Spotify catalog information for a single track.

        Parameters
        ----------
        track_id : str
            The ID of the track.
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Track
            The requested track.
        """
        return models.Track.from_payload(
            await self.get(f"tracks/{track_id}", {"market": market})
        )

    async def get_several_tracks(
        self, track_ids: list[str], *, market: str | None = None
    ) -> list[models.Track]:
        """Get Spotify catalog information for several tracks.

        Parameters
        ----------
        track_ids : list[str]
            The IDs of the tracks. Maximum: 50.
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        list[models.Track]
            The requested tracks.
        """
        return [
            models.Track.from_payload(tra)
            for tra in (
                await self.get("tracks", {"ids": ",".join(track_ids), "market": market})
            )["tracks"]
        ]

    async def get_users_saved_tracks(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        market: str | None = None,
    ) -> models.Paginator[models.Track]:
        """Get a list of the tracks saved in the current user's 'Your Music' library.

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
        models.Paginator[models.Track]
            A paginator who's items are a list of tracks.
        """
        return models.Paginator.from_payload(
            await self.get(
                "me/tracks", {"limit": limit, "offset": offset, "market": market}
            ),
            models.Track,
        )

    async def save_tracks_for_user(
        self,
        track_ids: list[str],
    ) -> None:
        """Save one or more tracks to the current user's 'Your Music' library.

        Parameters
        ----------
        track_ids : list[str]
            The IDs of the tracks. Maximum: 50.
        """
        await self.put("me/tracks", {"ids": track_ids})

    async def remove_users_saved_tracks(self, track_ids: list[str]) -> None:
        """Remove one or more tracks from the current user's 'Your Music' library.

        Parameters
        ----------
        track_ids : list[str]
            The IDs of the tracks. Maximum: 50.
        """
        await self.delete("me/tracks", {"ids": track_ids})

    async def check_users_saved_tracks(self, track_ids: list[str]) -> list[bool]:
        """Check if one or more tracks is already saved in the current user's 'Your Music' library.

        Parameters
        ----------
        track_ids : list[str]
            The IDs of the tracks. Maximum: 50.

        Returns
        -------
        list[bool]
            A list of booleans dictating whether or not the corresponding tracks are already saved.
        """
        return await self.get("me/tracks/contains", {"ids": track_ids})

    async def get_tracks_audio_features(self, track_id: str) -> models.AudioFeatures:
        """Get audio feature information for a single track.

        Parameters
        ----------
        track_id : str
            The ID of the track.

        Returns
        -------
        models.AudioFeatures
            The track's audio features.
        """
        return models.AudioFeatures.from_payload(
            await self.get(f"audio-features/{track_id}", {})
        )

    async def get_several_tracks_audio_features(
        self, track_ids: list[str]
    ) -> list[models.AudioFeatures]:
        """Get audio features for several tracks.

        Parameters
        ----------
        track_ids : list[str]
            The IDs of the tracks. Maximum: 100.

        Returns
        -------
        list[AudioFeatures]
            The tracks' audio features.
        """
        return [
            models.AudioFeatures.from_payload(aud)
            for aud in (await self.get("audio-features", {"ids": ",".join(track_ids)}))[
                "audio_features"
            ]
        ]

    async def get_tracks_audio_analysis(self, track_id: str) -> models.AudioAnalysis:
        """Get a low-level audio analysis for a track in the Spotify catalog.
        The audio analysis describes the track's structure and musical content,
        including rhythm, pitch, and timbre.

        Parameters
        ----------
        track_id : str
            The ID of the track.

        Returns
        -------
        models.AudioAnalysis
            The track's audio analysis.
        """

        return models.AudioAnalysis.from_payload(
            await self.get(f"audio-analysis/{track_id}", {})
        )

    async def get_recommendations(
        self,
        seed_artists: list[str],
        seed_genres: list[str],
        seed_tracks: list[str],
        *,
        limit: int | None = None,
        market: str | None = None,
        max_acousticness: float | None = None,
        max_danceability: float | None = None,
        max_duration_ms: int | None = None,
        max_energy: float | None = None,
        max_instrumentalness: float | None = None,
        max_key: int | None = None,
        max_liveness: float | None = None,
        max_loudness: float | None = None,
        max_mode: int | None = None,
        max_popularity: int | None = None,
        max_speechiness: float | None = None,
        max_tempo: float | None = None,
        max_time_signature: int | None = None,
        max_valence: float | None = None,
        min_acousticness: float | None = None,
        min_danceability: float | None = None,
        min_duration_ms: int | None = None,
        min_energy: float | None = None,
        min_instrumentalness: float | None = None,
        min_key: int | None = None,
        min_liveness: float | None = None,
        min_loudness: float | None = None,
        min_mode: int | None = None,
        min_popularity: int | None = None,
        min_speechiness: float | None = None,
        min_tempo: float | None = None,
        min_time_signature: int | None = None,
        min_valence: float | None = None,
        target_acousticness: float | None = None,
        target_danceability: float | None = None,
        target_duration_ms: int | None = None,
        target_energy: float | None = None,
        target_instrumentalness: float | None = None,
        target_key: int | None = None,
        target_liveness: float | None = None,
        target_loudness: float | None = None,
        target_mode: int | None = None,
        target_popularity: int | None = None,
        target_speechiness: float | None = None,
        target_tempo: float | None = None,
        target_time_signature: int | None = None,
        target_valence: float | None = None,
    ) -> models.Recommendation:
        """Recommendations are generated based on the available information for a given seed entity
        and matched against similar artists and tracks. If there is sufficient information about the
        provided seeds, a list of tracks will be returned together with pool size details.

        For artists and tracks that are very new or obscure there might not be enough data to generate
        a list of tracks.

        Parameters
        ----------
        seed_artists : list[str]
            A list of artist IDs for seed artists. Up to 5 seed values may be provided in any
            combination of ``seed_artists``, ``seed_tracks`` and ``seed_genres``.
        seed_genres : list[str]
            A list of any genres in the set of available genre seeds. Up to 5 seed values may be
            provided in any combination of ``seed_artists``, ``seed_tracks`` and ``seed_genres``.
            # TODO: link to available_genre_seeds endpoint.
        seed_tracks : list[str]
            A list of track IDs for seed tracks. Up to 5 seed values may be provided in any combination
            of ``seed_artists``, ``seed_tracks`` and ``seed_genres``.
        limit : int, optional
            The target size of the list of recommended tracks. For seeds with unusually small pools or
            when highly restrictive filtering is applied, it may be impossible to generate the requested
            number of recommended tracks. Debugging information for such cases is available in the
            response. Default: 20. Minimum: 1. Maximum: 100.
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.
        max_acousticness : float, optional
        max_danceability : float, optional
        max_duration_ms : int, optional
        max_energy : float, optional
        max_instrumentalness : float, optional
        max_key : int, optional
        max_liveness : float, optional
        max_loudness : float, optional
        max_mode : int, optional
        max_popularity : int, optional
        max_speechiness : float, optional
        max_tempo : float, optional
        max_time_signature : int, optional
        max_valence : float, optional
        min_acousticness : float, optional
        min_danceability : float, optional
        min_duration_ms : int, optional
        min_energy : float, optional
        min_instrumentalness : float, optional
        min_key : int, optional
        min_liveness : float, optional
        min_loudness : float, optional
        min_mode : int, optional
        min_popularity : int, optional
        min_speechiness : float, optional
        min_tempo : float, optional
        min_time_signature : int, optional
        min_valence : float, optional
        target_acousticness : float, optional
        target_danceability : float, optional
        target_duration_ms : int, optional
        target_energy : float, optional
        target_instrumentalness : float, optional
        target_key : int, optional
        target_liveness : float, optional
        target_loudness : float, optional
        target_mode : int, optional
        target_popularity : int, optional
        target_speechiness : float, optional
        target_tempo : float, optional
        target_time_signature : int, optional
        target_valence : float, optional

        Returns
        -------
        models.Recommendation
            The recommended tracks.
        """
        # TODO: Use TypedDict (https://peps.python.org/pep-0692/)
        return models.Recommendation.from_payload(
            await self.get(
                "recommendations",
                {
                    "seed_artists": ",".join(seed_artists),
                    "seed_genres": ",".join(seed_genres),
                    "seed_tracks": ",".join(seed_tracks),
                    "limit": limit,
                    "market": market,
                    "max_acousticness": max_acousticness,
                    "max_danceability": max_danceability,
                    "max_duration_ms": max_duration_ms,
                    "max_energy": max_energy,
                    "max_instrumentalness": max_instrumentalness,
                    "max_key": max_key,
                    "max_liveness": max_liveness,
                    "max_loudness": max_loudness,
                    "max_mode": max_mode,
                    "max_popularity": max_popularity,
                    "max_speechiness": max_speechiness,
                    "max_tempo": max_tempo,
                    "max_time_signature": max_time_signature,
                    "max_valence": max_valence,
                    "min_acousticness": min_acousticness,
                    "min_danceability": min_danceability,
                    "min_duration_ms": min_duration_ms,
                    "min_energy": min_energy,
                    "min_instrumentalness": min_instrumentalness,
                    "min_key": min_key,
                    "min_liveness": min_liveness,
                    "min_loudness": min_loudness,
                    "min_mode": min_mode,
                    "min_popularity": min_popularity,
                    "min_speechiness": min_speechiness,
                    "min_tempo": min_tempo,
                    "min_time_signature": min_time_signature,
                    "min_valence": min_valence,
                    "target_acousticness": target_acousticness,
                    "target_danceability": target_danceability,
                    "target_duration_ms": target_duration_ms,
                    "target_energy": target_energy,
                    "target_instrumentalness": target_instrumentalness,
                    "target_key": target_key,
                    "target_liveness": target_liveness,
                    "target_loudness": target_loudness,
                    "target_mode": target_mode,
                    "target_popularity": target_popularity,
                    "target_speechiness": target_speechiness,
                    "target_tempo": target_tempo,
                    "target_time_signature": target_time_signature,
                    "target_valence": target_valence,
                },
            )
        )

    async def get_current_users_profile(self) -> models.User:
        """Get detailed profile information about the current user.

        Returns
        -------
        models.User
            The current user.
        """
        return models.User.from_payload(await self.get("me", {}))

    @t.overload
    async def get_users_top_items(
        self,
        type: t.Literal[enums.TopItemType.ARTISTS] = enums.TopItemType.ARTISTS,
        *,
        limit: int | None = None,
        offset: int | None = None,
        time_range: enums.TimeRange | None = None,
    ) -> models.Paginator[models.Artist]:
        ...

    @t.overload
    async def get_users_top_items(
        self,
        type: t.Literal[enums.TopItemType.TRACKS] = enums.TopItemType.TRACKS,
        *,
        limit: int | None = None,
        offset: int | None = None,
        time_range: enums.TimeRange | None = None,
    ) -> models.Paginator[models.Track]:
        ...

    async def get_users_top_items(
        self,
        type: enums.TopItemType = enums.TopItemType.ARTISTS,
        *,
        limit: int | None = None,
        offset: int | None = None,
        time_range: enums.TimeRange | None = None,
    ) -> models.Paginator:
        """Get the current user's top artists or tracks based on calculated affinity.

        Parameters
        ----------
        type : enums.TopItemType, optional
            The type of entity to return. Default: enums.TopItemType.ARTISTS
        limit : int, optional
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, optional
            The index of the first item to return. Default: 0 (the first item)
        time_range : enums.TimeRange, optional
            Over what time frame the affinities are computed. Default: ``enums.TimeRange.MEDIUM_TERM``

        Returns
        -------
        models.Paginator
            A paginator who's items are a list of tracks or artists.
        """
        return models.Paginator.from_payload(
            await self.get(
                f"me/top/{type.value}",
                {
                    "limit": limit,
                    "offset": offset,
                    "time_range": time_range.value if time_range else None,
                },
            ),
            models.Artist if type == enums.TopItemType.ARTISTS else models.Track,
        )

    async def get_users_profile(
        self,
        user_id: str,
    ) -> models.User:
        """Get public profile information about a Spotify user.

        Parameters
        ----------
        user_id : str
            The ID of the user.

        Returns
        -------
        models.User
            The requested user.
        """
        return models.User.from_payload(await self.get(f"users/{user_id}", {}))

    async def follow_playlist(
        self,
        playlist_id: str,
        public: bool | None = None,
    ) -> None:
        """Add the current user as a follower of a playlist.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.
        public : bool, optional
            Whether or not the playlist will be included in the user's public playlists. Default: ``True``
        """
        await self.put(f"playlists/{playlist_id}/followers", {"public": public})

    async def unfollow_playlist(
        self,
        playlist_id: str,
    ) -> None:
        """Remove the current user as a follower of a playlist.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.
        """
        await self.delete(f"playlists/{playlist_id}/followers", {})

    async def get_followed_artists(
        self,
        after: str | None = None,
        limit: int | None = None,
    ) -> models.Paginator[models.Artist]:
        """Get the current user's followed artists.

        Parameters
        ----------
        after : str, optional
            The last artist ID retrieved from the previous request.
        limit : int, optional
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.

        Returns
        -------
        models.Paginator[models.Artist]
            A paginator who's items are a list of artists.
        """
        return models.Paginator.from_payload(
            await self.get("me/following", {"after": after, "limit": limit}),
            models.Artist,
        )

    async def follow_artists(
        self,
        artist_ids: list[str],
    ) -> None:
        """Add the current user as a follower of one or more artists.

        Parameters
        ----------
        artist_ids : list[str]
            The IDs of the artists. Maximum: 50.
        """
        await self.put("me/following", {"ids": ",".join(artist_ids), "type": "artist"})

    async def follow_users(
        self,
        user_ids: list[str],
    ) -> None:
        """Add the current user as a follower of one or more Spotify users.

        Parameters
        ----------
        user_ids : list[str]
            The IDs of the users. Maximum: 50.
        """
        await self.put("me/following", {"ids": ",".join(user_ids), "type": "user"})

    async def unfollow_artists(
        self,
        artist_ids: list[str],
    ) -> None:
        """Remove the current user as a follower of one or more artists.

        Parameters
        ----------
        artist_ids : list[str]
            The IDs of the artists. Maximum: 50.
        """
        await self.delete(
            "me/following", {"ids": ",".join(artist_ids), "type": "artist"}
        )

    async def unfollow_users(
        self,
        user_ids: list[str],
    ) -> None:
        """Remove the current user as a follower of one or more Spotify users.

        Parameters
        ----------
        user_ids : list[str]
            The IDs of the users. Maximum: 50.
        """
        await self.delete("me/following", {"ids": ",".join(user_ids), "type": "user"})

    async def check_if_user_follows_artists(
        self,
        artist_ids: list[str],
    ) -> list[bool]:
        """Check to see if the current user is following one or more artists.

        Parameters
        ----------
        artist_ids : list[str]
            The IDs of the artists. Maximum: 50.

        Returns
        -------
        list[bool]
            A list of booleans dictating whether or not the current user has followed the corresponding artists.
        """
        return await self.get(
            "me/following/contains", {"ids": ",".join(artist_ids), "type": "artist"}
        )

    async def check_if_user_follows_users(
        self,
        user_ids: list[str],
    ) -> list[bool]:
        """Check to see if the current user is following one or more Spotify users.

        Parameters
        ----------
        user_ids : list[str]
            The IDs of the users. Maximum: 50.

        Returns
        -------
        list[bool]
            A list of booleans dictating whether or not the current user has followed the corresponding users.
        """
        return await self.get(
            "me/following/contains", {"ids": ",".join(user_ids), "type": "user"}
        )

    async def check_if_users_follow_playlist(
        self,
        playlist_id: str,
        user_ids: list[str],
    ) -> list[bool]:
        """Check to see if one or more Spotify users are following a specified playlist.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.
        user_ids : list[str]
            The IDs of the users. Maximum: 5.

        Returns
        -------
        list[bool]
            A list of booleans dictating whether or not the corresponding users have followed the playlist.
        """
        return await self.get(
            f"playlists/{playlist_id}/followers/contains", {"ids": ",".join(user_ids)}
        )
