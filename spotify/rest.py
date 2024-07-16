from __future__ import annotations


import aiohttp
import typing
import json as json_
import base64
import datetime

import spotify
from spotify import enums, errors, models, utils, internals, types as types_

if typing.TYPE_CHECKING:
    from spotify import oauth


class REST:
    """Implementation to make API calls with.

    Parameters
    ----------
    access_flow : oauth.AuthorizationCodeFlow | oauth.ClientCredentialsFlow
        Access manager to use for requests.
    """

    def __init__(
        self,
        access_flow: oauth.AuthorizationCodeFlow | oauth.ClientCredentialsFlow,
    ) -> None:
        self.access_flow = access_flow

        self._session: aiohttp.ClientSession | None = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = aiohttp.ClientSession()

        return self._session

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, typing.Any] | None = None,
        json: dict[str, typing.Any] | None = None,
        data: bytes | None = None,
    ) -> bytes | None:
        await self.access_flow.validate_token()

        async with self.session.request(
            method,
            f"{spotify.BASE_URL}/{url}",
            params=utils.process_dict(params) if params is not None else None,
            json=utils.process_dict(json) if json is not None else None,
            data=data if data is not None else None,
            headers={
                "Authorization": f"Bearer {self.access_flow.access_token}",
                "Content-Type": "application/json",
            },
        ) as r:
            data = await r.content.read()

            with open("./test.json", "w") as f:
                json_.dump(json_.loads(data), f, indent=4)

            if r.content_type == "application/json" and r.ok:
                return data
            elif r.content_type == "application/json":
                json_data = json_.loads(data)
                if json_data.get("error"):
                    json_data = json_data["error"]
                else:
                    json_data = {"status": r.status, "message": r.reason}
                raise errors.APIError(**json_data)  # pyright: ignore[reportArgumentType]

            # TODO: might be worth raising APIError with the aiohttp error as an attribute?

            r.raise_for_status()

    async def get(
        self,
        url: str,
        *,
        params: dict[str, typing.Any] | None = None,
        json: dict[str, typing.Any] | None = None,
        data: bytes | None = None,
    ) -> bytes | None:
        return await self.request("GET", url, params=params, json=json, data=data)

    async def post(
        self,
        url: str,
        *,
        params: dict[str, typing.Any] | None = None,
        json: dict[str, typing.Any] | None = None,
        data: bytes | None = None,
    ) -> bytes | None:
        return await self.request("POST", url, params=params, json=json, data=data)

    async def put(
        self,
        url: str,
        *,
        params: dict[str, typing.Any] | None = None,
        json: dict[str, typing.Any] | None = None,
        data: bytes | None = None,
    ) -> bytes | None:
        return await self.request("PUT", url, params=params, json=json, data=data)

    async def delete(
        self,
        url: str,
        *,
        params: dict[str, typing.Any] | None = None,
        json: dict[str, typing.Any] | None = None,
        data: bytes | None = None,
    ) -> bytes | None:
        return await self.request("DELETE", url, params=params, json=json, data=data)

    async def get_album(
        self, album_id: str, *, market: str | types_.MissingType = types_.MISSING
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
        album = await self.get(f"albums/{album_id}", params={"market": market})
        assert album is not None
        return models.Album.model_validate_json(album)

    async def get_several_albums(
        self, album_ids: list[str], *, market: str | types_.MissingType = types_.MISSING
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
        albums = await self.get("albums", params={"ids": ",".join(album_ids), "market": market})
        assert albums is not None
        return internals._Albums.model_validate_json(  # pyright: ignore[reportPrivateUsage]
            albums
        ).albums

    async def get_album_tracks(
        self,
        album_id: str,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
        market: str | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.SimpleTrack]:
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
        tracks = await self.get(
            f"albums/{album_id}/tracks",
            params={"limit": limit, "offset": offset, "market": market},
        )
        assert tracks is not None
        return models.Paginator[models.SimpleTrack].model_validate_json(tracks)

    async def get_users_saved_albums(
        self,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
        market: str | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.SavedAlbum]:
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
        models.Paginator[models.SavedAlbum]
            A paginator who's items are a list of albums.
        """
        albums = await self.get(
            "me/albums", params={"limit": limit, "offset": offset, "market": market}
        )
        assert albums is not None
        return models.Paginator[models.SavedAlbum].model_validate_json(albums)

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
        await self.put("me/albums", params={"ids": ",".join(album_ids)})

    async def remove_users_saved_albums(self, album_ids: list[str]) -> None:
        """Remove one or more albums from the current user's 'Your Music' library.

        Parameters
        ----------
        album_ids : list[str]
            The IDs of the albums. Maximum: 50.
        """
        await self.delete("me/albums", params={"ids": ",".join(album_ids)})

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
        albums = await self.get("me/albums/contains", params={"ids": ",".join(album_ids)})
        assert albums is not None
        return json_.loads(albums)

    async def get_new_releases(
        self,
        *,
        country: str | types_.MissingType = types_.MISSING,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.SimpleAlbum]:
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
        models.Paginator[models.SimpleAlbum]
            A paginator who's items are a list of albums.
        """
        albums = await self.get(
            "browse/new-releases",
            params={"country": country, "limit": limit, "offset": offset},
        )
        assert albums is not None
        return internals._SimpleAlbumPaginator.model_validate_json(  # pyright: ignore[reportPrivateUsage]
            albums
        ).paginator

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
        artist = await self.get(f"artists/{artist_id}")
        assert artist is not None
        return models.Artist.model_validate_json(artist)

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
        artists = await self.get("artists", params={"ids": ",".join(artist_ids)})
        assert artists is not None
        return internals._Artists.model_validate_json(  # pyright: ignore[reportPrivateUsage]
            artists
        ).artists

    async def get_artists_albums(
        self,
        artist_id: str,
        *,
        include_groups: list[enums.AlbumGroup] | types_.MissingType = types_.MISSING,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
        market: str | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.ArtistAlbum]:
        """Get Spotify catalog information about an artist's albums.

        Parameters
        ----------
        artist_id : str
            The ID of the artist.
        include_groups : list[enums.AlbumGroup], optional
            Used to filter the type of items returned. If not specified, all album types_ will be returned.
        limit : int, optional
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, optional
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
            Only get content that is available in that market.
            Must be an `ISO 3166-1 alpha-2 country code <https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.

        Returns
        -------
        models.Paginator[models.ArtistAlbum]
            A paginator who's items are a list of albums.
        """
        albums = await self.get(
            f"artists/{artist_id}/albums",
            params={
                "include_groups": ",".join(g.value for g in include_groups)
                if not isinstance(include_groups, types_.MissingType)
                else types_.MISSING,
                "limit": limit,
                "offset": offset,
                "market": market,
            },
        )
        assert albums is not None
        return models.Paginator[models.ArtistAlbum].model_validate_json(albums)

    # NOTE: market is required for this endpoint
    async def get_artists_top_tracks(
        self, artist_id: str, *, market: str
    ) -> list[models.TrackWithSimpleArtist]:
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
        tracks = await self.get(f"artists/{artist_id}/top-tracks", params={"market": market})
        assert tracks is not None
        return internals._Tracks.model_validate_json(  # pyright: ignore[reportPrivateUsage]
            tracks
        ).tracks

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
        artists = await self.get(f"artists/{artist_id}/related-artists")
        assert artists is not None
        return internals._Artists.model_validate_json(  # pyright: ignore[reportPrivateUsage]
            artists
        ).artists

    async def get_audiobook(
        self, audiobook_id: str, *, market: str | types_.MissingType = types_.MISSING
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
        audiobook = await self.get(f"audiobooks/{audiobook_id}", params={"market": market})
        assert audiobook is not None
        return models.Audiobook.model_validate_json(audiobook)

    async def get_several_audiobooks(
        self,
        audiobook_ids: list[str],
        *,
        market: str | types_.MissingType = types_.MISSING,
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
        audiobooks = await self.get(
            "audiobooks", params={"ids": ",".join(audiobook_ids), "market": market}
        )
        assert audiobooks is not None
        return internals._Audiobooks.model_validate_json(  # pyright: ignore[reportPrivateUsage]
            audiobooks
        ).audiobooks

    async def get_audiobook_chapters(
        self,
        audiobook_id: str,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
        market: str | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.SimpleChapter]:
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
        models.Paginator[models.SimpleChapter]
            A paginator who's items are a list of chapters.
        """
        chapters = await self.get(
            f"audiobooks/{audiobook_id}/chapters",
            params={"limit": limit, "offset": offset, "market": market},
        )
        assert chapters is not None
        return models.Paginator[models.SimpleChapter].model_validate_json(chapters)

    async def get_users_saved_audiobooks(
        self,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.SimpleAudiobook]:
        """Get a list of the audiobooks saved in the current user's library.

        Parameters
        ----------
        limit : int, optional
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, optional
            The index of the first item to return. Default: 0 (the first item).

        Returns
        -------
        models.Paginator[models.SimpleAudiobook]
            A paginator who's items are a list of audiobooks.
        """
        audiobooks = await self.get("me/audiobooks", params={"limit": limit, "offset": offset})
        assert audiobooks is not None
        return models.Paginator[models.SimpleAudiobook].model_validate_json(audiobooks)

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
        await self.put("me/audiobooks", params={"ids": ",".join(audiobook_ids)})

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
        await self.delete("me/audiobooks", params={"ids": ",".join(audiobook_ids)})

    async def check_users_saved_audiobooks(self, audiobook_ids: list[str]) -> list[bool]:
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
        audiobooks = await self.get(
            "me/audiobooks/contains", params={"ids": ",".join(audiobook_ids)}
        )
        assert audiobooks is not None
        return json_.loads(audiobooks)

    async def get_several_browse_categories(
        self,
        *,
        country: str | types_.MissingType = types_.MISSING,
        locale: str | types_.MissingType = types_.MISSING,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.Category]:
        categories = await self.get(
            "browse/categories",
            params={
                "country": country,
                "locale": locale,
                "limit": limit,
                "offset": offset,
            },
        )
        assert categories is not None
        return internals._CategoryPaginator.model_validate_json(  # pyright: ignore[reportPrivateUsage]
            categories
        ).paginator

    async def get_single_browse_category(
        self,
        category_id: str,
        *,
        country: str | types_.MissingType = types_.MISSING,
        locale: str | types_.MissingType = types_.MISSING,
    ) -> models.Category:
        category = await self.get(
            f"browse/categories/{category_id}",
            params={
                "country": country,
                "locale": locale,
            },
        )
        assert category is not None
        return models.Category.model_validate_json(category)

    async def get_chapter(
        self, chapter_id: str, *, market: str | types_.MissingType = types_.MISSING
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
        chapter = await self.get(f"chapters/{chapter_id}", params={"market": market})
        assert chapter is not None
        return models.Chapter.model_validate_json(chapter)

    async def get_several_chapters(
        self,
        chapter_ids: list[str],
        *,
        market: str | types_.MissingType = types_.MISSING,
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
        chapters = await self.get(
            "chapters", params={"ids": ",".join(chapter_ids), "market": market}
        )
        assert chapters is not None
        return internals._Chapters.model_validate_json(  # pyright: ignore[reportPrivateUsage]
            chapters
        ).chapters

    # NOTE: market is required on this endpoint when not using a user token I think
    async def get_episode(
        self, episode_id: str, *, market: str | types_.MissingType = types_.MISSING
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
        episode = await self.get(f"episodes/{episode_id}", params={"market": market})
        assert episode is not None
        return models.Episode.model_validate_json(episode)

    # NOTE: market is required on this endpoint when not using a user token I think
    # otherwise a list of null is returned
    async def get_several_episodes(
        self,
        episode_ids: list[str],
        *,
        market: str | types_.MissingType = types_.MISSING,
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
        episodes = await self.get(
            "episodes", params={"ids": ",".join(episode_ids), "market": market}
        )
        assert episodes is not None
        return internals._Episodes.model_validate_json(  # pyright: ignore[reportPrivateUsage]
            episodes
        ).episodes

    async def get_users_saved_episodes(
        self,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
        market: str | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.SavedEpisode]:
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
        models.Paginator[models.SavedEpisode]
            A paginator who's items are a list of episodes.
        """
        episodes = await self.get(
            "me/episodes", params={"limit": limit, "offset": offset, "market": market}
        )
        assert episodes is not None
        return models.Paginator[models.SavedEpisode].model_validate_json(episodes)

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
        await self.put("me/episodes", params={"ids": ",".join(episode_ids)})

    async def remove_users_saved_episodes(self, episode_ids: list[str]) -> None:
        """Remove one or more episodes from the current user's library.

        .. warning::

            This API endpoint is in **beta** and could change without warning.

        Parameters
        ----------
        episode_ids : list[str]
            The IDs of the episodes. Maximum: 50.
        """
        await self.delete("me/episodes", params={"ids": ",".join(episode_ids)})

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
        episodes = await self.get("me/episodes/contains", params={"ids": ",".join(episode_ids)})
        assert episodes is not None
        return json_.loads(episodes)

    async def get_available_genre_seeds(self) -> list[str]:
        genres = await self.get("recommendations/available-genre-seeds")
        assert genres is not None

        return internals._AvailableGenreSeeds.model_validate_json(  # pyright: ignore[reportPrivateUsage]
            genres
        ).genres

    async def get_available_markets(self) -> list[str]:
        markets = await self.get("markets")
        assert markets is not None
        return internals._AvailableMarkets.model_validate_json(  # pyright: ignore[reportPrivateUsage]
            markets
        ).markets

    async def get_playback_state(
        self, *, market: str | types_.MissingType = types_.MISSING
    ) -> models.Player | None:
        player = await self.get(
            "me/player", params={"market": market, "additional_types": "track,episode"}
        )
        return models.Player.model_validate_json(player) if player is not None else None

    async def transfer_playback(
        self,
        device_id: str,
        *,
        play: bool | types_.MissingType = types_.MISSING,
    ) -> None:
        await self.put("me/player", json={"device_ids": [device_id], "play": play})

    async def get_available_devices(self) -> list[models.Device]:
        devices = await self.get("me/player/devices")
        assert devices is not None
        return internals._Devices.model_validate_json(devices).devices  # pyright: ignore[reportPrivateUsage]

    async def get_currently_playing_track(
        self, *, market: str | types_.MissingType = types_.MISSING
    ) -> models.PlayerTrack | None:
        player = await self.get(
            "me/player/currently-playing",
            params={"market": market, "additional_types": "track,episode"},
        )
        return models.PlayerTrack.model_validate_json(player) if player is not None else None

    @typing.overload
    async def start_or_resume_playback(
        self,
        *,
        device_id: str | types_.MissingType = types_.MISSING,
        context_uri: str | types_.MissingType = types_.MISSING,
        offset: int | str | types_.MissingType = types_.MISSING,
        position: datetime.timedelta | types_.MissingType = types_.MISSING,
    ) -> None: ...

    @typing.overload
    async def start_or_resume_playback(
        self,
        *,
        device_id: str | types_.MissingType = types_.MISSING,
        uris: list[str] | types_.MissingType = types_.MISSING,
        position: datetime.timedelta | types_.MissingType = types_.MISSING,
    ) -> None: ...

    async def start_or_resume_playback(
        self,
        *,
        device_id: str | types_.MissingType = types_.MISSING,
        context_uri: str | types_.MissingType = types_.MISSING,
        uris: list[str] | types_.MissingType = types_.MISSING,
        offset: int | str | types_.MissingType = types_.MISSING,
        position: datetime.timedelta | types_.MissingType = types_.MISSING,
    ) -> None:
        final_offset = types_.MISSING
        if not isinstance(offset, types_.MissingType):
            if isinstance(offset, int):
                final_offset = {"position": offset}
            else:
                assert isinstance(offset, str)
                final_offset = {"uri": offset}

        await self.put(
            "me/player/play",
            params={
                "device_id": device_id,
            },
            json={
                "context_uri": context_uri,
                "uris": uris,
                "offset": final_offset,
                "position_ms": position.total_seconds() * 1000
                if not isinstance(position, types_.MissingType)
                else types_.MISSING,
            },
        )

    async def pause_playback(
        self, *, device_id: str | types_.MissingType = types_.MISSING
    ) -> None:
        await self.put("me/player/pause", params={"device_id": device_id})

    async def skip_to_next(self, *, device_id: str | types_.MissingType = types_.MISSING) -> None:
        await self.post("me/player/next", params={"device_id": device_id})

    async def skip_to_previous(
        self, *, device_id: str | types_.MissingType = types_.MISSING
    ) -> None:
        await self.post("me/player/previous", params={"device_id": device_id})

    async def seek_to_position(
        self,
        position: datetime.timedelta,
        *,
        device_id: str | types_.MissingType = types_.MISSING,
    ) -> None:
        await self.put(
            "me/player/seek",
            params={
                "position_ms": position.total_seconds() * 1000,
                "device_id": device_id,
            },
        )

    async def set_repeat_mode(
        self,
        state: enums.RepeatState,
        *,
        device_id: str | types_.MissingType = types_.MISSING,
    ) -> None:
        await self.put("me/player/repeat", params={"state": state.value, "device_id": device_id})

    async def set_playback_volume(
        self,
        volume_percent: int,
        *,
        device_id: str | types_.MissingType = types_.MISSING,
    ) -> None:
        await self.put(
            "me/player/volume",
            params={"volume_percent": volume_percent, "device_id": device_id},
        )

    async def set_playback_shuffle(
        self, state: bool, *, device_id: str | types_.MissingType = types_.MISSING
    ) -> None:
        await self.put("me/player/shuffle", params={"state": state, "device_id": device_id})

    @typing.overload
    async def get_recently_played_tracks(
        self,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        after: datetime.datetime | types_.MissingType = types_.MISSING,
    ) -> models.CursorPaginator[models.PlayHistory]: ...

    @typing.overload
    async def get_recently_played_tracks(
        self,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        before: datetime.datetime | types_.MissingType = types_.MISSING,
    ) -> models.CursorPaginator[models.PlayHistory]: ...

    async def get_recently_played_tracks(
        self,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        after: datetime.datetime | types_.MissingType = types_.MISSING,
        before: datetime.datetime | types_.MissingType = types_.MISSING,
    ) -> models.CursorPaginator[models.PlayHistory]:
        if not isinstance(after, types_.MissingType) and not isinstance(
            before, types_.MissingType
        ):
            raise ValueError("only one of `after` and `before` may be supplied")

        played = await self.get(
            "me/player/recently-played",
            params={
                "limit": limit,
                "after": int(after.timestamp() * 1000)
                if not isinstance(after, types_.MissingType)
                else types_.MISSING,
                "before": int(before.timestamp() * 1000)
                if not isinstance(before, types_.MissingType)
                else types_.MISSING,
            },
        )
        assert played is not None
        return models.CursorPaginator[models.PlayHistory].model_validate_json(played)

    async def get_users_queue(self) -> models.Queue:
        queue = await self.get("me/player/queue")
        assert queue is not None
        return models.Queue.model_validate_json(queue)

    async def add_item_to_playback_queue(
        self,
        uri: str,
        *,
        device_id: str | types_.MissingType = types_.MISSING,
    ) -> None:
        await self.post("me/player/queue", params={"uri": uri, "device_id": device_id})

    async def get_playlist(
        self,
        playlist_id: str,
        *,
        market: str | types_.MissingType = types_.MISSING,
        fields: str | types_.MissingType = types_.MISSING,
    ) -> models.Playlist:
        playlist = await self.get(
            f"playlists/{playlist_id}",
            params={
                "market": market,
                "fields": fields,
                "additional_types_": "track,episode",
            },
        )
        assert playlist is not None
        return models.Playlist.model_validate_json(playlist)

    async def change_playlist_details(
        self,
        playlist_id: str,
        *,
        name: str | types_.MissingType = types_.MISSING,
        public: bool | types_.MissingType = types_.MISSING,
        collaborative: bool | types_.MissingType = types_.MISSING,
        description: str | types_.MissingType = types_.MISSING,
    ) -> None:
        # NOTE
        # Add to documentation when complete:
        # "The Spotify Web API is bugged, and does not allow you to clear the description field through the API.
        # Setting it to `None`, `""` or even `False` will have no effect."
        await self.put(
            f"playlists/{playlist_id}",
            json={
                "name": name,
                "public": public,
                "collaborative": collaborative,
                "description": description,
            },
        )

    async def get_playlist_items(
        self,
        playlist_id: str,
        *,
        market: str | types_.MissingType = types_.MISSING,
        fields: str | types_.MissingType = types_.MISSING,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.PlaylistItem]:
        items = await self.get(
            f"playlists/{playlist_id}/tracks",
            params={
                "market": market,
                "fields": fields,
                "limit": limit,
                "offset": offset,
                "additional_types_": "track,episode",
            },
        )
        assert items is not None
        return models.Paginator[models.PlaylistItem].model_validate_json(items)

    async def update_playlist_items(
        self,
        playlist_id: str,
        uris: list[str] | types_.MissingType = types_.MISSING,
        *,
        range_start: int | types_.MissingType = types_.MISSING,
        insert_before: int | types_.MissingType = types_.MISSING,
        range_length: int | types_.MissingType = types_.MISSING,
        snapshot_id: str | types_.MissingType = types_.MISSING,
    ) -> str:
        snapshot_id_ = await self.put(
            f"playlists/{playlist_id}/tracks",
            params={
                "uris": uris,
            },
            json={
                "range_start": range_start,
                "insert_before": insert_before,
                "range_length": range_length,
                "snapshot_id": snapshot_id,
            },
        )
        assert snapshot_id_ is not None
        return internals._SnapshotID.model_validate_json(snapshot_id_).snapshot_id  # pyright: ignore[reportPrivateUsage]

    async def add_items_to_playlist(
        self,
        playlist_id: str,
        *,
        uris: list[str],
        position: int | types_.MissingType = types_.MISSING,
    ) -> str:
        snapshot_id = await self.post(
            f"playlists/{playlist_id}/tracks",
            json={
                "position": position,
                "uris": uris,
            },
        )
        assert snapshot_id is not None
        return internals._SnapshotID.model_validate_json(snapshot_id).snapshot_id  # pyright: ignore[reportPrivateUsage]

    async def remove_playlist_items(
        self,
        playlist_id: str,
        *,
        uris: list[str],
        snapshot_id: str | types_.MissingType = types_.MISSING,
    ) -> str:
        tracks = [{"uri": uri} for uri in uris]
        snapshot_id_ = await self.delete(
            f"playlists/{playlist_id}/tracks",
            json={"tracks": tracks, "snapshot_id": snapshot_id},
        )
        assert snapshot_id_ is not None
        return internals._SnapshotID.model_validate_json(snapshot_id_).snapshot_id  # pyright: ignore[reportPrivateUsage]

    async def get_current_users_playlists(
        self,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.SimplePlaylist]:
        playlists = await self.get(
            "me/playlists",
            params={
                "limit": limit,
                "offset": offset,
            },
        )
        assert playlists is not None
        return models.Paginator[models.SimplePlaylist].model_validate_json(playlists)

    async def get_users_playlists(
        self,
        user_id: str,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.SimplePlaylist]:
        playlists = await self.get(
            f"users/{user_id}/playlists",
            params={
                "limit": limit,
                "offset": offset,
            },
        )
        assert playlists is not None
        return models.Paginator[models.SimplePlaylist].model_validate_json(playlists)

    async def create_playlist(
        self,
        user_id: str,
        *,
        name: str,
        public: bool | types_.MissingType = types_.MISSING,
        collaborative: bool | types_.MissingType = types_.MISSING,
        description: str | types_.MissingType = types_.MISSING,
    ) -> models.Playlist:
        playlist = await self.post(
            f"users/{user_id}/playlists",
            params={
                "user_id": user_id,
            },
            json={
                "name": name,
                "public": public,
                "collaborative": collaborative,
                "description": description,
            },
        )
        assert playlist is not None
        return models.Playlist.model_validate_json(playlist)

    async def get_featured_playlists(
        self,
        *,
        locale: str | types_.MissingType = types_.MISSING,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
    ) -> models.Playlists:
        playlists = await self.get(
            "browse/featured-playlists",
            params={
                "locale": locale,
                "limit": limit,
                "offset": offset,
            },
        )
        assert playlists is not None
        return models.Playlists.model_validate_json(playlists)

    async def get_categorys_playlists(
        self,
        category_id: str,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
    ) -> models.Playlists:
        playlists = await self.get(
            f"browse/categories/{category_id}/playlists",
            params={
                "limit": limit,
                "offset": offset,
            },
        )
        assert playlists is not None
        return models.Playlists.model_validate_json(playlists)

    async def get_playlist_cover_image(
        self,
        playlist_id: str,
    ) -> list[models.Image]:
        images = await self.get(f"playlists/{playlist_id}/images")
        assert images is not None
        img_list: list[dict[str, str | int]] = json_.loads(images)
        return [models.Image(**img) for img in img_list]  # pyright: ignore[reportArgumentType]

    async def add_custom_playlist_cover_image(
        self,
        playlist_id: str,
        *,
        image: bytes,
    ) -> None:
        image = base64.encodebytes(image).replace(b"\n", b"")
        await self.put(
            f"playlists/{playlist_id}/images",
            data=image,
        )

    # TODO: create builder class for this
    async def search_for_item(
        self,
        *,
        types: list[enums.SearchType],
        query: str | types_.MissingType = types_.MISSING,
        album: str | types_.MissingType = types_.MISSING,
        artist: str | types_.MissingType = types_.MISSING,
        track: str | types_.MissingType = types_.MISSING,
        start_year: int | types_.MissingType = types_.MISSING,
        end_year: int | types_.MissingType = types_.MISSING,
        upc: str | types_.MissingType = types_.MISSING,
        hipster: bool | types_.MissingType = types_.MISSING,
        new: bool | types_.MissingType = types_.MISSING,
        isrc: str | types_.MissingType = types_.MISSING,
        genres: list[str] | types_.MissingType = types_.MISSING,
        market: str | types_.MissingType = types_.MISSING,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
        include_external: bool | types_.MissingType = types_.MISSING,
    ) -> models.SearchResult:
        # NOTE: upon testing, searching for shows and episodes is broken on spotify's side.
        if len(types) < 1:
            raise ValueError("`types` may not be empty")

        if isinstance(start_year, types_.MissingType) and not isinstance(
            end_year, types_.MissingType
        ):
            raise ValueError("end_year cannot be provided without start_year")

        if not isinstance(start_year, types_.MissingType) and not isinstance(
            end_year, types_.MissingType
        ):
            final_year = f"year:{start_year}-{end_year}"
        elif not isinstance(start_year, types_.MissingType):
            final_year = f"year:{start_year}"
        else:
            final_year = types_.MISSING

        final_album = (
            f"album:{album}" if not isinstance(album, types_.MissingType) else types_.MISSING
        )
        final_artist = (
            f"artist:{artist}" if not isinstance(artist, types_.MissingType) else types_.MISSING
        )
        final_track = (
            f"track:{track}" if not isinstance(track, types_.MissingType) else types_.MISSING
        )
        final_upc = f"upc:{upc}" if not isinstance(upc, types_.MissingType) else types_.MISSING
        final_hipster = (
            "tag:hipster"
            if not isinstance(hipster, types_.MissingType) and hipster is True
            else types_.MISSING
        )
        final_new = (
            "tag:new"
            if not isinstance(new, types_.MissingType) and new is True
            else types_.MISSING
        )
        final_isrc = f"isrc:{isrc}" if not isinstance(isrc, types_.MissingType) else types_.MISSING
        final_genre = (
            f"genre:{' '.join(genres)}"
            if not isinstance(genres, types_.MissingType) and len(genres) > 0
            else types_.MISSING
        )

        final_query = " ".join(
            [
                item
                for item in [
                    query,
                    final_album,
                    final_artist,
                    final_track,
                    final_upc,
                    final_hipster,
                    final_new,
                    final_isrc,
                    final_genre,
                    final_year,
                ]
                if not isinstance(item, types_.MissingType)
            ]
        )

        if not final_query.strip():
            raise ValueError(
                "one of `query`, `album`, `artist`, `track`, `start_year`, `upc`, `hipster`, `new`, `isrc` or `genres` must be provided"
            )

        results = await self.get(
            "search",
            params={
                "q": final_query,
                "type": ",".join([t.value for t in types]),
                "market": market,
                "limit": limit,
                "offset": offset,
                "include_external": "audio"
                if include_external is not isinstance(include_external, types_.MissingType)
                and include_external is True
                else types_.MISSING,
            },
        )
        assert results is not None
        return models.SearchResult.model_validate_json(results)

    async def get_show(
        self, show_id: str, *, market: str | types_.MissingType = types_.MISSING
    ) -> models.Show:
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
        show = await self.get(f"shows/{show_id}", params={"market": market})
        assert show is not None
        return models.Show.model_validate_json(show)

    async def get_several_shows(
        self, show_ids: list[str], *, market: str | types_.MissingType = types_.MISSING
    ) -> list[models.SimpleShow]:
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
        list[models.SimpleShow]
            The requested shows.
        """
        shows = await self.get("shows", params={"ids": ",".join(show_ids), "market": market})
        assert shows is not None
        return internals._Shows.model_validate_json(  # pyright: ignore[reportPrivateUsage]
            shows
        ).shows

    async def get_show_episodes(
        self,
        show_id: str,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
        market: str | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.SimpleEpisode]:
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
        models.Paginator[models.SimpleEpisode]
            A paginator who's items are a list of episodes.
        """
        episodes = await self.get(
            f"shows/{show_id}/episodes",
            params={"limit": limit, "offset": offset, "market": market},
        )
        assert episodes is not None
        return models.Paginator[models.SimpleEpisode].model_validate_json(episodes)

    async def get_users_saved_shows(
        self,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
        market: str | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.SavedShow]:
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
        models.Paginator[models.SavedShow]
            A paginator who's items are a list of shows.
        """
        shows = await self.get(
            "me/shows",
            params={"limit": limit, "offset": offset, "market": market},
        )
        assert shows is not None
        return models.Paginator[models.SavedShow].model_validate_json(shows)

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
        await self.put("me/shows", params={"ids": ",".join(show_ids)})

    async def remove_users_saved_shows(
        self, show_ids: list[str], *, market: str | types_.MissingType = types_.MISSING
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
        await self.delete("me/shows", params={"ids": ",".join(show_ids), "market": market})

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
        shows = await self.get("me/shows/contains", params={"ids": ",".join(show_ids)})
        assert shows is not None
        return json_.loads(shows)

    async def get_track(
        self, track_id: str, *, market: str | types_.MissingType = types_.MISSING
    ) -> models.TrackWithSimpleArtist:
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
        track = await self.get(f"tracks/{track_id}", params={"market": market})
        assert track is not None
        return models.TrackWithSimpleArtist.model_validate_json(track)

    async def get_several_tracks(
        self, track_ids: list[str], *, market: str | types_.MissingType = types_.MISSING
    ) -> list[models.TrackWithSimpleArtist]:
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
        tracks = await self.get("tracks", params={"ids": ",".join(track_ids), "market": market})
        assert tracks is not None
        return internals._Tracks.model_validate_json(tracks).tracks  # pyright: ignore[reportPrivateUsage]

    async def get_users_saved_tracks(
        self,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
        market: str | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.SavedTrack]:
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
        models.Paginator[models.SavedTrack]
            A paginator who's items are a list of tracks.
        """
        tracks = await self.get(
            "me/tracks", params={"limit": limit, "offset": offset, "market": market}
        )
        assert tracks is not None
        return models.Paginator[models.SavedTrack].model_validate_json(tracks)

    async def save_tracks_for_current_user(
        self,
        track_ids: list[str],
    ) -> None:
        """Save one or more tracks to the current user's 'Your Music' library.

        Parameters
        ----------
        track_ids : list[str]
            The IDs of the tracks. Maximum: 50.
        """
        await self.put("me/tracks", params={"ids": ",".join(track_ids)})

    async def remove_users_saved_tracks(self, track_ids: list[str]) -> None:
        """Remove one or more tracks from the current user's 'Your Music' library.

        Parameters
        ----------
        track_ids : list[str]
            The IDs of the tracks. Maximum: 50.
        """
        await self.delete("me/tracks", params={"ids": ",".join(track_ids)})

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
        tracks = await self.get("me/tracks/contains", params={"ids": ",".join(track_ids)})
        assert tracks is not None
        return json_.loads(tracks)

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
        features = await self.get(f"audio-features/{track_id}")
        assert features is not None
        return models.AudioFeatures.model_validate_json(features)

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
        features = await self.get("audio-features", params={"ids": ",".join(track_ids)})
        assert features is not None
        return internals._AudioFeatures.model_validate_json(features).audio_features  # pyright: ignore[reportPrivateUsage]

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
        analysis = await self.get(f"audio-analysis/{track_id}")
        assert analysis is not None
        return models.AudioAnalysis.model_validate_json(analysis)

    async def get_recommendations(
        self,
        seed_artists: list[str] | types_.MissingType = types_.MISSING,
        seed_genres: list[str] | types_.MissingType = types_.MISSING,
        seed_tracks: list[str] | types_.MissingType = types_.MISSING,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        market: str | types_.MissingType = types_.MISSING,
        min_acousticness: float | types_.MissingType = types_.MISSING,
        max_acousticness: float | types_.MissingType = types_.MISSING,
        target_acousticness: float | types_.MissingType = types_.MISSING,
        min_danceability: float | types_.MissingType = types_.MISSING,
        max_danceability: float | types_.MissingType = types_.MISSING,
        target_danceability: float | types_.MissingType = types_.MISSING,
        # TODO: this should be duration, not duration_ms
        min_duration_ms: int | types_.MissingType = types_.MISSING,
        max_duration_ms: int | types_.MissingType = types_.MISSING,
        target_duration_ms: int | types_.MissingType = types_.MISSING,
        min_energy: float | types_.MissingType = types_.MISSING,
        max_energy: float | types_.MissingType = types_.MISSING,
        target_energy: float | types_.MissingType = types_.MISSING,
        min_instrumentalness: float | types_.MissingType = types_.MISSING,
        max_instrumentalness: float | types_.MissingType = types_.MISSING,
        target_instrumentalness: float | types_.MissingType = types_.MISSING,
        min_key: int | types_.MissingType = types_.MISSING,
        max_key: int | types_.MissingType = types_.MISSING,
        target_key: int | types_.MissingType = types_.MISSING,
        min_liveness: float | types_.MissingType = types_.MISSING,
        max_liveness: float | types_.MissingType = types_.MISSING,
        target_liveness: float | types_.MissingType = types_.MISSING,
        min_loudness: float | types_.MissingType = types_.MISSING,
        max_loudness: float | types_.MissingType = types_.MISSING,
        target_loudness: float | types_.MissingType = types_.MISSING,
        min_mode: int | types_.MissingType = types_.MISSING,
        max_mode: int | types_.MissingType = types_.MISSING,
        target_mode: int | types_.MissingType = types_.MISSING,
        min_popularity: int | types_.MissingType = types_.MISSING,
        max_popularity: int | types_.MissingType = types_.MISSING,
        target_popularity: int | types_.MissingType = types_.MISSING,
        min_speechiness: float | types_.MissingType = types_.MISSING,
        max_speechiness: float | types_.MissingType = types_.MISSING,
        target_speechiness: float | types_.MissingType = types_.MISSING,
        min_tempo: float | types_.MissingType = types_.MISSING,
        max_tempo: float | types_.MissingType = types_.MISSING,
        target_tempo: float | types_.MissingType = types_.MISSING,
        min_time_signature: int | types_.MissingType = types_.MISSING,
        max_time_signature: int | types_.MissingType = types_.MISSING,
        target_time_signature: int | types_.MissingType = types_.MISSING,
        min_valence: float | types_.MissingType = types_.MISSING,
        max_valence: float | types_.MissingType = types_.MISSING,
        target_valence: float | types_.MissingType = types_.MISSING,
    ) -> models.Recommendations:
        recommendations = await self.get(
            "recommendations",
            params={
                "seed_artists": seed_artists,
                "seed_genres": seed_genres,
                "seed_tracks": seed_tracks,
                "limit": limit,
                "market": market,
                "min_acousticness": min_acousticness,
                "max_acousticness": max_acousticness,
                "target_acousticness": target_acousticness,
                "min_danceability": min_danceability,
                "max_danceability": max_danceability,
                "target_danceability": target_danceability,
                "min_duration_ms": min_duration_ms,
                "max_duration_ms": max_duration_ms,
                "target_duration_ms": target_duration_ms,
                "min_energy": min_energy,
                "max_energy": max_energy,
                "target_energy": target_energy,
                "min_instrumentalness": min_instrumentalness,
                "max_instrumentalness": max_instrumentalness,
                "target_instrumentalness": target_instrumentalness,
                "min_key": min_key,
                "max_key": max_key,
                "target_key": target_key,
                "min_liveness": min_liveness,
                "max_liveness": max_liveness,
                "target_liveness": target_liveness,
                "min_loudness": min_loudness,
                "max_loudness": max_loudness,
                "target_loudness": target_loudness,
                "min_mode": min_mode,
                "max_mode": max_mode,
                "target_mode": target_mode,
                "min_popularity": min_popularity,
                "max_popularity": max_popularity,
                "target_popularity": target_popularity,
                "min_speechiness": min_speechiness,
                "max_speechiness": max_speechiness,
                "target_speechiness": target_speechiness,
                "min_tempo": min_tempo,
                "max_tempo": max_tempo,
                "target_tempo": target_tempo,
                "min_time_signature": min_time_signature,
                "max_time_signature": max_time_signature,
                "target_time_signature": target_time_signature,
                "min_valence": min_valence,
                "max_valence": max_valence,
                "target_valence": target_valence,
            },
        )
        assert recommendations is not None
        return models.Recommendations.model_validate_json(recommendations)

    async def get_current_users_profile(self) -> models.OwnUser:
        user = await self.get("me")
        assert user is not None
        return models.OwnUser.model_validate_json(user)

    @typing.overload
    async def get_users_top_items(
        self,
        type: typing.Literal[enums.TopItemType.ARTISTS] = enums.TopItemType.ARTISTS,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
        time_range: enums.TimeRange | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.Artist]: ...

    @typing.overload
    async def get_users_top_items(
        self,
        type: typing.Literal[enums.TopItemType.TRACKS] = enums.TopItemType.TRACKS,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
        time_range: enums.TimeRange | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.TrackWithSimpleArtist]: ...

    async def get_users_top_items(
        self,
        type: enums.TopItemType = enums.TopItemType.ARTISTS,
        *,
        limit: int | types_.MissingType = types_.MISSING,
        offset: int | types_.MissingType = types_.MISSING,
        time_range: enums.TimeRange | types_.MissingType = types_.MISSING,
    ) -> models.Paginator[models.Artist] | models.Paginator[models.TrackWithSimpleArtist]:
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
        items = await self.get(
            f"me/top/{type.value}",
            params={
                "limit": limit,
                "offset": offset,
                "time_range": time_range.value
                if not isinstance(time_range, types_.MissingType)
                else types_.MISSING,
            },
        )
        assert items is not None
        if type is enums.TopItemType.ARTISTS:
            return models.Paginator[models.Artist].model_validate_json(items)
        else:
            assert type is enums.TopItemType.TRACKS
            return models.Paginator[models.TrackWithSimpleArtist].model_validate_json(items)

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
        user = await self.get(f"users/{user_id}")
        assert user is not None
        return models.User.model_validate_json(user)

    async def follow_playlist(
        self,
        playlist_id: str,
        public: bool | types_.MissingType = types_.MISSING,
    ) -> None:
        """Add the current user as a follower of a playlist.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.
        public : bool, optional
            Whether or not the playlist will be included in the user's public playlists. Default: ``True``
        """
        await self.put(f"playlists/{playlist_id}/followers", json={"public": public})

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
        await self.delete(f"playlists/{playlist_id}/followers")

    async def get_followed_artists(
        self,
        after: str | types_.MissingType = types_.MISSING,
        limit: int | types_.MissingType = types_.MISSING,
    ) -> models.CursorPaginator[models.Artist]:
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
        followed = await self.get(
            "me/following", params={"type": "artist", "after": after, "limit": limit}
        )
        assert followed is not None
        return internals._ArtistsPaginator.model_validate_json(followed).paginator  # pyright: ignore[reportPrivateUsage]

    async def follow_artists_or_users(
        self,
        ids: list[str],
        type: enums.UserType,
    ) -> None:
        """Add the current user as a follower of one or more artists.

        Parameters
        ----------
        artist_ids : list[str]
            The IDs of the artists. Maximum: 50.
        """
        await self.put("me/following", params={"ids": ",".join(ids), "type": type.value})

    async def unfollow_artists_or_users(self, ids: list[str], type: enums.UserType) -> None:
        """Remove the current user as a follower of one or more artists.

        Parameters
        ----------
        artist_ids : list[str]
            The IDs of the artists. Maximum: 50.
        """
        await self.delete("me/following", params={"ids": ",".join(ids), "type": type.value})

    async def check_if_user_follows_artists_or_users(
        self,
        ids: list[str],
        type: enums.UserType,
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
        follows = await self.get(
            "me/following/contains", params={"ids": ",".join(ids), "type": type.value}
        )
        assert follows is not None
        return json_.loads(follows)

    async def check_if_current_user_follows_playlist(
        self,
        playlist_id: str,
    ) -> bool:
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
        follows = await self.get(
            f"playlists/{playlist_id}/followers/contains",
        )
        assert follows is not None
        return json_.loads(follows)[0]
