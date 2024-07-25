from __future__ import annotations

import base64
import datetime
import json as json_
import typing

import aiohttp
import pydantic

import spotify
from spotify import enums, errors, internals, models, utils
from spotify.types import MISSING, MissingOr

if typing.TYPE_CHECKING:
    from spotify import oauth

__all__: typing.Sequence[str] = ("API",)

P = typing.ParamSpec("P")
T = typing.TypeVar("T")


def validator(
    func: typing.Callable[P, typing.Awaitable[T]],
) -> typing.Callable[P, typing.Awaitable[T]]:
    async def inner(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            result = await func(*args, **kwargs)
        except pydantic.ValidationError as e:
            raise errors.InvalidPayloadError("invalid JSON payload received") from e
        return result

    return inner


# TODO: rename file to api.py
class API:
    """Implementation to make API calls with.

    Parameters
    ----------
    access_flow : oauth.AuthorizationCodeFlow | oauth.ClientCredentialsFlow
        Access flow to use for api requests.
    """

    def __init__(
        self,
        access_flow: oauth.AuthorizationCodeFlow | oauth.ClientCredentialsFlow,
    ) -> None:
        self.access_flow = access_flow

        self._session: aiohttp.ClientSession | None = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """The [aiohttp `ClientSession`][aiohttp.ClientSession] to use for requests.

        Must be closed after all requests have been completed.
        """
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
                    raise errors.APIError(**json_data["error"])

            raise errors.APIError(
                status=r.status,
                message=r.reason,
            )

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

    @validator
    async def get_album(self, album_id: str, *, market: MissingOr[str] = MISSING) -> models.Album:
        """Get Spotify catalog information for a single album.

        Parameters
        ----------
        album_id : str
            The ID of the album.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        models.Album
            The requested album.
        """
        album = await self.get(f"albums/{album_id}", params={"market": market})
        assert album is not None
        return models.Album.model_validate_json(album)

    @validator
    async def get_several_albums(
        self, album_ids: list[str], *, market: MissingOr[str] = MISSING
    ) -> list[models.Album]:
        """Get Spotify catalog information for several albums.

        Parameters
        ----------
        album_ids : list[str]
            The IDs of the albums.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        list[models.Album]
            The requested albums.
        """
        albums = await self.get("albums", params={"ids": ",".join(album_ids), "market": market})
        assert albums is not None
        return internals.Albums.model_validate_json(albums).albums

    @validator
    async def get_album_tracks(
        self,
        album_id: str,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
        market: MissingOr[str] = MISSING,
    ) -> models.Paginator[models.SimpleTrack]:
        """Get Spotify catalog information about an album's tracks.

        Parameters
        ----------
        album_id : str
            The ID of the album.
        limit : int, default 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

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

    @validator
    async def get_users_saved_albums(
        self,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
        market: MissingOr[str] = MISSING,
    ) -> models.Paginator[models.SavedAlbum]:
        """Get a list of the albums saved in the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_READ`][spotify.enums.Scope.USER_LIBRARY_READ]

        Parameters
        ----------
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        models.Paginator[models.SavedAlbum]
            A paginator who's items are a list of albums.
        """
        albums = await self.get(
            "me/albums",
            params={"limit": limit, "offset": offset, "market": market},
        )
        assert albums is not None
        return models.Paginator[models.SavedAlbum].model_validate_json(albums)

    @validator
    async def save_albums_for_current_user(
        self,
        album_ids: list[str],
    ) -> None:
        """Save one or more albums to the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_MODIFY`][spotify.enums.Scope.USER_LIBRARY_MODIFY]

        Parameters
        ----------
        album_ids : list[str]
            The IDs of the albums. Maximum: 50.
        """
        await self.put("me/albums", json={"ids": album_ids})

    @validator
    async def remove_users_saved_albums(self, album_ids: list[str]) -> None:
        """Remove one or more albums from the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_MODIFY`][spotify.enums.Scope.USER_LIBRARY_MODIFY]

        Parameters
        ----------
        album_ids : list[str]
            The IDs of the albums. Maximum: 50.
        """
        await self.delete("me/albums", json={"ids": album_ids})

    @validator
    async def check_users_saved_albums(self, album_ids: list[str]) -> list[bool]:
        """Check if one or more albums is already saved in the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_READ`][spotify.enums.Scope.USER_LIBRARY_READ]

        Parameters
        ----------
        album_ids : list[str]
            The IDs of the albums. Maximum: 20.

        Returns
        -------
        list[bool]
            A list of booleans dictating whether or not the corresponding albums are saved.
        """
        albums = await self.get("me/albums/contains", params={"ids": ",".join(album_ids)})
        assert albums is not None
        return json_.loads(albums)

    @validator
    async def get_new_releases(
        self,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
    ) -> models.Paginator[models.SimpleAlbum]:
        """Get a list of new album releases featured in Spotify (shown, for example, on a Spotify
        player's 'Browse' tab).

        Parameters
        ----------
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).

        Returns
        -------
        models.Paginator[models.SimpleAlbum]
            A paginator who's items are a list of albums.
        """
        albums = await self.get(
            "browse/new-releases",
            params={"limit": limit, "offset": offset},
        )
        assert albums is not None
        return internals.SimpleAlbumPaginator.model_validate_json(albums).paginator

    @validator
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

    @validator
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
        return internals.Artists.model_validate_json(artists).artists

    @validator
    async def get_artists_albums(
        self,
        artist_id: str,
        *,
        include_groups: MissingOr[list[enums.AlbumGroup]] = MISSING,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
        market: MissingOr[str] = MISSING,
    ) -> models.Paginator[models.ArtistAlbum]:
        """Get Spotify catalog information about an artist's albums.

        Parameters
        ----------
        artist_id : str
            The ID of the artist.
        include_groups : list[enums.AlbumGroup], default: all album types
            Used to filter the type of items returned. If not specified, all album types_ will be returned.
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        models.Paginator[models.ArtistAlbum]
            A paginator who's items are a list of albums.
        """
        albums = await self.get(
            f"artists/{artist_id}/albums",
            params={
                "include_groups": ",".join(g.value for g in include_groups)
                if include_groups is not MISSING
                else MISSING,
                "limit": limit,
                "offset": offset,
                "market": market,
            },
        )
        assert albums is not None
        return models.Paginator[models.ArtistAlbum].model_validate_json(albums)

    @validator
    async def get_artists_top_tracks(
        self, artist_id: str, *, market: MissingOr[str] = MISSING
    ) -> list[models.TrackWithSimpleArtist]:
        """Get Spotify catalog information about an artist's top tracks.

        Parameters
        ----------
        artist_id : str
            The ID of the artist.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        list[models.TrackWithSimpleArtist]
            The requested tracks.
        """
        tracks = await self.get(f"artists/{artist_id}/top-tracks", params={"market": market})
        assert tracks is not None
        return internals.Tracks.model_validate_json(tracks).tracks

    @validator
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
        return internals.Artists.model_validate_json(artists).artists

    @validator
    async def get_audiobook(
        self, audiobook_id: str, *, market: MissingOr[str] = MISSING
    ) -> models.Audiobook:
        """Get Spotify catalog information for a single audiobook.

        Parameters
        ----------
        audiobook_id : str
            The ID of the audiobook.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        models.Audiobook
            The requested audiobook.
        """
        audiobook = await self.get(f"audiobooks/{audiobook_id}", params={"market": market})
        assert audiobook is not None
        return models.Audiobook.model_validate_json(audiobook)

    @validator
    async def get_several_audiobooks(
        self,
        audiobook_ids: list[str],
        *,
        market: MissingOr[str] = MISSING,
    ) -> list[models.Audiobook]:
        """Get Spotify catalog information for several audiobooks.

        Parameters
        ----------
        audiobook_ids : list[str]
            The IDs of the audiobooks. Maximum: 50.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        list[models.Audiobook]
            The requested audiobooks.
        """
        audiobooks = await self.get(
            "audiobooks",
            params={"ids": ",".join(audiobook_ids), "market": market},
        )
        assert audiobooks is not None
        return internals.Audiobooks.model_validate_json(audiobooks).audiobooks

    @validator
    async def get_audiobook_chapters(
        self,
        audiobook_id: str,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
        market: MissingOr[str] = MISSING,
    ) -> models.Paginator[models.SimpleChapter]:
        """Get Spotify catalog information about an audiobooks's chapters.

        Parameters
        ----------
        audiobook_id : str
            The ID of the audiobook.
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

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

    @validator
    async def get_users_saved_audiobooks(
        self,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
    ) -> models.Paginator[models.SimpleAudiobook]:
        """Get a list of the audiobooks saved in the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_READ`][spotify.enums.Scope.USER_LIBRARY_READ]

        Parameters
        ----------
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).

        Returns
        -------
        models.Paginator[models.SimpleAudiobook]
            A paginator who's items are a list of audiobooks.
        """
        audiobooks = await self.get("me/audiobooks", params={"limit": limit, "offset": offset})
        assert audiobooks is not None
        return models.Paginator[models.SimpleAudiobook].model_validate_json(audiobooks)

    @validator
    async def save_audiobooks_for_user(
        self,
        audiobook_ids: list[str],
    ) -> None:
        """Save one or more audiobooks to the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_MODIFY`][spotify.enums.Scope.USER_LIBRARY_MODIFY]

        Parameters
        ----------
        audiobook_ids : list[str]
            The IDs of the audiobooks. Maximum: 50.
        """
        await self.put("me/audiobooks", params={"ids": ",".join(audiobook_ids)})

    @validator
    async def remove_users_saved_audiobooks(
        self,
        audiobook_ids: list[str],
    ) -> None:
        """Remove one or more audiobooks from the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_MODIFY`][spotify.enums.Scope.USER_LIBRARY_MODIFY]

        Parameters
        ----------
        audiobook_ids : list[str]
            The IDs of the audiobooks. Maximum: 50.
        """
        await self.delete("me/audiobooks", params={"ids": ",".join(audiobook_ids)})

    @validator
    async def check_users_saved_audiobooks(self, audiobook_ids: list[str]) -> list[bool]:
        """Check if one or more audiobooks are already saved in the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_READ`][spotify.enums.Scope.USER_LIBRARY_READ]

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

    @typing.overload
    async def get_several_browse_categories(
        self,
        *,
        country: str,
        locale: str,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
    ) -> models.Paginator[models.Category]: ...

    @typing.overload
    async def get_several_browse_categories(
        self,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
    ) -> models.Paginator[models.Category]: ...

    @validator
    async def get_several_browse_categories(
        self,
        *,
        country: MissingOr[str] = MISSING,
        locale: MissingOr[str] = MISSING,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
    ) -> models.Paginator[models.Category]:
        """Get a list of categories used to tag items in Spotify (on, for example, the Spotify player's 'Browse' tab).

        Parameters
        ----------
        country : str, optional
            Desired country to get content for.
        locale : str, optional
            Desired language to get content in. Default: American English

            !!! note
                Both or neither of the `country` and `locale` parameters must be provided.

        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).

        Returns
        -------
        models.Paginator[models.Category]
            A paginator who's items are a list of categories.
        """
        if (country is MISSING and locale is not MISSING) or (
            country is not MISSING and locale is MISSING
        ):
            raise ValueError("both or neither of `country` and `locale` must be provided")
        elif country is not MISSING and locale is not MISSING:
            locale = f"{locale}-{country}"
        else:
            locale = MISSING

        categories = await self.get(
            "browse/categories",
            params={
                "locale": locale,
                "limit": limit,
                "offset": offset,
            },
        )
        assert categories is not None
        return internals.CategoryPaginator.model_validate_json(categories).paginator

    @typing.overload
    async def get_single_browse_category(
        self,
        category_id: str,
    ) -> models.Category: ...

    @typing.overload
    async def get_single_browse_category(
        self,
        category_id: str,
        *,
        country: str,
        locale: str,
    ) -> models.Category: ...

    @validator
    async def get_single_browse_category(
        self,
        category_id: str,
        *,
        country: MissingOr[str] = MISSING,
        locale: MissingOr[str] = MISSING,
    ) -> models.Category:
        """Get a single category used to tag items in Spotify (on, for example, the Spotify player's 'Browse' tab).

        Parameters
        ----------
        category_id : str
            The ID of the category.
        country : str, optional
            Desired country to get content for.
        locale : str, optional
            Desired language to get content in. Default: American English

            !!! note
                Both or neither of the `country` and `locale` parameters must be provided.
        Returns
        -------
        models.Category
            The requested category.
        """
        if (country is MISSING and locale is not MISSING) or (
            country is not MISSING and locale is MISSING
        ):
            raise ValueError("both or neither of `country` and `locale` must be provided")
        elif country is not MISSING and locale is not MISSING:
            locale = f"{locale}-{country}"
        else:
            locale = MISSING

        category = await self.get(
            f"browse/categories/{category_id}",
            params={
                "locale": locale,
            },
        )
        assert category is not None
        return models.Category.model_validate_json(category)

    @validator
    async def get_chapter(
        self, chapter_id: str, *, market: MissingOr[str] = MISSING
    ) -> models.Chapter:
        """Get Spotify catalog information for a single chapter.

        Parameters
        ----------
        chapter_id : str
            The ID of the chapter.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        models.Chapter
            The requested chapter.
        """
        chapter = await self.get(f"chapters/{chapter_id}", params={"market": market})
        assert chapter is not None
        return models.Chapter.model_validate_json(chapter)

    @validator
    async def get_several_chapters(
        self,
        chapter_ids: list[str],
        *,
        market: MissingOr[str] = MISSING,
    ) -> list[models.Chapter]:
        """Get Spotify catalog information for several chapters.

        Parameters
        ----------
        chapter_ids : list[str]
            The IDs of the chapters. Maximum: 50.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        list[models.Chapter]
            The requested chapters.
        """
        chapters = await self.get(
            "chapters", params={"ids": ",".join(chapter_ids), "market": market}
        )
        assert chapters is not None
        return internals.Chapters.model_validate_json(chapters).chapters

    @validator
    async def get_episode(
        self, episode_id: str, *, market: MissingOr[str] = MISSING
    ) -> models.Episode:
        """Get Spotify catalog information for a single episode.

        !!! warning
            When not using a user token for auth, `market` is required. Otherwise you will receive a 404.

        Parameters
        ----------
        episode_id : str
            The ID of the episode.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        models.Episode
            The requested episode.
        """
        episode = await self.get(f"episodes/{episode_id}", params={"market": market})
        assert episode is not None
        return models.Episode.model_validate_json(episode)

    @validator
    async def get_several_episodes(
        self,
        episode_ids: list[str],
        *,
        market: MissingOr[str] = MISSING,
    ) -> list[models.Episode]:
        """Get Spotify catalog information for several episodes.

        !!! warning
            When not using a user token for auth, `market` is required. Otherwise you will receive an error.

        Parameters
        ----------
        episode_ids : list[str]
            The IDs of the episodes. Maximum: 50.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        list[models.Episode]
            The requested episodes.
        """
        episodes = await self.get(
            "episodes", params={"ids": ",".join(episode_ids), "market": market}
        )
        assert episodes is not None
        return internals.Episodes.model_validate_json(episodes).episodes

    @validator
    async def get_users_saved_episodes(
        self,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
        market: MissingOr[str] = MISSING,
    ) -> models.Paginator[models.SavedEpisode]:
        """Get a list of the episodes saved in the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_READ`][spotify.enums.Scope.USER_LIBRARY_READ]

        !!! warning
            This API endpoint is in **beta** and could break without warning.

        Parameters
        ----------
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        models.Paginator[models.SavedEpisode]
            A paginator who's items are a list of episodes.
        """
        episodes = await self.get(
            "me/episodes",
            params={"limit": limit, "offset": offset, "market": market},
        )
        assert episodes is not None
        return models.Paginator[models.SavedEpisode].model_validate_json(episodes)

    @validator
    async def save_episodes_for_current_user(
        self,
        episode_ids: list[str],
    ) -> None:
        """Save one or more episodes to the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scopes"
            [`USER_LIBRARY_MODIFY`][spotify.enums.Scope.USER_LIBRARY_MODIFY]

        !!! warning
            This API endpoint is in **beta** and could break without warning.

        Parameters
        ----------
        episode_ids : list[str]
            The IDs of the episodes. Maximum: 50.
        """
        await self.put("me/episodes", params={"ids": ",".join(episode_ids)})

    @validator
    async def remove_users_saved_episodes(self, episode_ids: list[str]) -> None:
        """Remove one or more episodes from the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_MODIFY`][spotify.enums.Scope.USER_LIBRARY_MODIFY]

        !!! warning
            This API endpoint is in **beta** and could break without warning.

        Parameters
        ----------
        episode_ids : list[str]
            The IDs of the episodes. Maximum: 50.
        """
        await self.delete("me/episodes", params={"ids": ",".join(episode_ids)})

    @validator
    async def check_users_saved_episodes(self, episode_ids: list[str]) -> list[bool]:
        """Check if one or more episodes are already saved in the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_READ`][spotify.enums.Scope.USER_LIBRARY_READ]

        !!! warning
            This API endpoint is in **beta** and could break without warning.

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

    @validator
    async def get_available_genre_seeds(self) -> list[str]:
        """Retrieve a list of available genres seed parameter values for recommendations.

        Returns
        -------
        list[str]
            The available genre seeds.
        """
        genres = await self.get("recommendations/available-genre-seeds")
        assert genres is not None

        return internals.AvailableGenreSeeds.model_validate_json(genres).genres

    @validator
    async def get_available_markets(self) -> list[str]:
        """Get the list of markets where Spotify is available.

        Returns
        -------
        list[str]
            The markets where Spotify is available.
        """
        markets = await self.get("markets")
        assert markets is not None
        return internals.AvailableMarkets.model_validate_json(markets).markets

    @validator
    async def get_playback_state(
        self, *, market: MissingOr[str] = MISSING
    ) -> models.Player | None:
        """Get information about the user's current playback state, including track or episode, progress, and active device.

        !!! scopes "Required Authorization Scope"
            [`USER_READ_PLAYBACK_STATE`][spotify.enums.Scope.USER_READ_PLAYBACK_STATE]

        Parameters
        ----------
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        models.Player
            Player information.
        None
            If there is no playback state.
        """
        player = await self.get(
            "me/player",
            params={"market": market, "additional_types": "track,episode"},
        )
        return models.Player.model_validate_json(player) if player is not None else None

    @validator
    async def transfer_playback(
        self,
        device_id: str,
        *,
        play: MissingOr[bool] = MISSING,
    ) -> None:
        """Transfer playback to a new device and optionally begin playback.

        !!! scopes "Required Authorization Scope"
            [`USER_MODIFY_PLAYBACK_STATE`][spotify.enums.Scope.USER_MODIFY_PLAYBACK_STATE]

        !!! premium
            This endpoint only works for users who have Spotify Premium.

        Parameters
        ----------
        device_id : str
            The ID of the device on which playback should be started/transferred.
        play : bool, default False
            Whether or not to ensure playback happens on the specified device.
        """
        await self.put("me/player", json={"device_ids": [device_id], "play": play})

    @validator
    async def get_available_devices(self) -> list[models.Device]:
        """Get information about a user's available Spotify Connect devices.
        Some device models are not supported and will not be listed in the response.

        !!! scopes "Required Authorization Scope"
            [`USER_READ_PLAYBACK_STATE`][spotify.enums.Scope.USER_READ_PLAYBACK_STATE]

        Returns
        -------
        list[models.Device]
            The available devices.
        """
        devices = await self.get("me/player/devices")
        assert devices is not None
        return internals.Devices.model_validate_json(devices).devices

    @validator
    async def get_currently_playing_track(
        self, *, market: MissingOr[str] = MISSING
    ) -> models.PlayerTrack | None:
        """Get the item currently being played on the user's Spotify account.

        !!! scopes "Required Authorization Scope"
            [`USER_READ_CURRENTLY_PLAYING`][spotify.enums.Scope.USER_READ_CURRENTLY_PLAYING]

        Parameters
        ----------
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        models.PlayerTrack
            The currently playing item.
        None
            If nothing is playing.
        """
        player = await self.get(
            "me/player/currently-playing",
            params={"market": market, "additional_types": "track,episode"},
        )
        return models.PlayerTrack.model_validate_json(player) if player is not None else None

    @typing.overload
    async def start_or_resume_playback(
        self,
        *,
        device_id: MissingOr[str] = MISSING,
        context_uri: MissingOr[str] = MISSING,
        offset: MissingOr[int | str] = MISSING,
        position: MissingOr[datetime.timedelta] = MISSING,
    ) -> None: ...

    @typing.overload
    async def start_or_resume_playback(
        self,
        *,
        device_id: MissingOr[str] = MISSING,
        track_uris: MissingOr[list[str]] = MISSING,
        position: MissingOr[datetime.timedelta] = MISSING,
    ) -> None: ...

    @validator
    async def start_or_resume_playback(
        self,
        *,
        device_id: MissingOr[str] = MISSING,
        context_uri: MissingOr[str] = MISSING,
        track_uris: MissingOr[list[str]] = MISSING,
        offset: MissingOr[int | str] = MISSING,
        position: MissingOr[datetime.timedelta] = MISSING,
    ) -> None:
        """Start a new context or resume current playback on the user's active device.

        !!! scopes "Required Authorization Scope"
            [`USER_MODIFY_PLAYBACK_STATE`][spotify.enums.Scope.USER_MODIFY_PLAYBACK_STATE]

        !!! premium
            This endpoint only works for users who have Spotify Premium.

        Parameters
        ----------
        device_id : str, optional
            The ID of the device this command is targeting. Default: currently active device.

            !!! note
                Only one of `context_uri` and `track_uris` may be supplied.
        context_uri : str, optional
            URI of an **album**, **artist** or **playlist** to play.
        track_uris : list[str], optional
            URIs of **track(s)** to play
        offset : int | str, optional
            Indicates where playback should start.

            * [int][] - position where playback should start, 0 being the first item.
            * [str][] - URI of the item to start at.

            !!! note
                `offset` can only be used when `context_uri` is an **album** or **playlist**.
        position : datetime.timedelta, optional
            The position in the (first) item at which to start playback.
        """
        final_offset = MISSING
        if offset is not MISSING:
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
                "uris": track_uris,
                "offset": final_offset,
                "position_ms": position.total_seconds() * 1000
                if position is not MISSING
                else MISSING,
            },
        )

    @validator
    async def pause_playback(self, *, device_id: MissingOr[str] = MISSING) -> None:
        """Pause playback on the user's account.

        !!! scopes "Required Authorization Scope"
            [`USER_MODIFY_PLAYBACK_STATE`][spotify.enums.Scope.USER_MODIFY_PLAYBACK_STATE]

        !!! premium
            This endpoint only works for users who have Spotify Premium.

        Parameters
        ----------
        device_id : str, optional
            The ID of the device this command is targeting. Default: currently active device.
        """
        await self.put("me/player/pause", params={"device_id": device_id})

    @validator
    async def skip_to_next(self, *, device_id: MissingOr[str] = MISSING) -> None:
        """Skip to the next item in the user's queue.

        !!! scopes "Required Authorization Scope"
            [`USER_MODIFY_PLAYBACK_STATE`][spotify.enums.Scope.USER_MODIFY_PLAYBACK_STATE]

        !!! premium
            This endpoint only works for users who have Spotify Premium.

        Parameters
        ----------
        device_id : str, optional
            The ID of the device this command is targeting. Default: currently active device.
        """
        await self.post("me/player/next", params={"device_id": device_id})

    @validator
    async def skip_to_previous(self, *, device_id: MissingOr[str] = MISSING) -> None:
        """Skip to the previous item in the user's queue.

        !!! scopes "Required Authorization Scope"
            [`USER_MODIFY_PLAYBACK_STATE`][spotify.enums.Scope.USER_MODIFY_PLAYBACK_STATE]

        !!! premium
            This endpoint only works for users who have Spotify Premium.

        Parameters
        ----------
        device_id : str, optional
            The ID of the device this command is targeting. Default: currently active device.
        """
        await self.post("me/player/previous", params={"device_id": device_id})

    @validator
    async def seek_to_position(
        self,
        position: datetime.timedelta,
        *,
        device_id: MissingOr[str] = MISSING,
    ) -> None:
        """Seeks to the given position in the user's currently playing track.

        !!! scopes "Required Authorization Scope"
            [`USER_MODIFY_PLAYBACK_STATE`][spotify.enums.Scope.USER_MODIFY_PLAYBACK_STATE]

        !!! premium
            This endpoint only works for users who have Spotify Premium.

        Parameters
        ----------
        position : datetime.timedelta
            The position to seek to. If this value is longer than the length of the current item, the next item will be played.
        device_id : str, optional
            The ID of the device this command is targeting. Default: currently active device.
        """
        await self.put(
            "me/player/seek",
            params={
                "position_ms": position.total_seconds() * 1000,
                "device_id": device_id,
            },
        )

    @validator
    async def set_repeat_mode(
        self,
        state: enums.RepeatState,
        *,
        device_id: MissingOr[str] = MISSING,
    ) -> None:
        """Set the repeat mode for the user's playback.

        !!! scopes "Required Authorization Scope"
            [`USER_MODIFY_PLAYBACK_STATE`][spotify.enums.Scope.USER_MODIFY_PLAYBACK_STATE]

        !!! premium
            This endpoint only works for users who have Spotify Premium.

        Parameters
        ----------
        state : enums.RepeatState
            The repeat state (off/track/context).
        device_id : str, optional
            The ID of the device this command is targeting. Default: currently active device.
        """
        await self.put(
            "me/player/repeat",
            params={"state": state.value, "device_id": device_id},
        )

    @validator
    async def set_playback_volume(
        self,
        volume_percent: int,
        *,
        device_id: MissingOr[str] = MISSING,
    ) -> None:
        """Set the volume for the user's current playback device.

        !!! scopes "Required Authorization Scope"
            [`USER_MODIFY_PLAYBACK_STATE`][spotify.enums.Scope.USER_MODIFY_PLAYBACK_STATE]

        !!! premium
            This endpoint only works for users who have Spotify Premium.

        Parameters
        ----------
        volume_percent : int
            The volume to set. Must be a value from 0 to 100 inclusive.
        device_id : str, optional
            The ID of the device this command is targeting. Default: currently active device.
        """
        await self.put(
            "me/player/volume",
            params={"volume_percent": volume_percent, "device_id": device_id},
        )

    @validator
    async def set_playback_shuffle(
        self, state: bool, *, device_id: MissingOr[str] = MISSING
    ) -> None:
        """Set shuffle mode for user's playback.

        !!! scopes "Required Authorization Scope"
            [`USER_MODIFY_PLAYBACK_STATE`][spotify.enums.Scope.USER_MODIFY_PLAYBACK_STATE]

        !!! premium
            This endpoint only works for users who have Spotify Premium.

        Parameters
        ----------
        state : bool
            Whether or not to shuffle the user's playback.
        device_id : str, optional
            The ID of the device this command is targeting. Default: currently active device.
        """
        await self.put(
            "me/player/shuffle",
            params={"state": state, "device_id": device_id},
        )

    @typing.overload
    async def get_recently_played_tracks(
        self,
        *,
        limit: MissingOr[int] = MISSING,
        after: MissingOr[datetime.datetime] = MISSING,
    ) -> models.CursorPaginator[models.PlayHistory]: ...

    @typing.overload
    async def get_recently_played_tracks(
        self,
        *,
        limit: MissingOr[int] = MISSING,
        before: MissingOr[datetime.datetime] = MISSING,
    ) -> models.CursorPaginator[models.PlayHistory]: ...

    @validator
    async def get_recently_played_tracks(
        self,
        *,
        limit: MissingOr[int] = MISSING,
        after: MissingOr[datetime.datetime] = MISSING,
        before: MissingOr[datetime.datetime] = MISSING,
    ) -> models.CursorPaginator[models.PlayHistory]:
        """Get tracks from the current user's recently played tracks.

        !!! scopes "Required Authorization Scope"
            [`USER_READ_RECENTLY_PLAYED`][spotify.enums.Scope.USER_READ_RECENTLY_PLAYED]

        !!! note
            Currently doesn't support podcast episodes.

        Parameters
        ----------
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.

            !!! note
                Only one of `after` and `before` may be provided.
        after : datetime.datetime
            Return all items **after** (but not including) this time.
        before : datetime.datetime
            Returns all items **before** (but not including) this time.
        """
        if after is not MISSING and before is not MISSING:
            raise ValueError("only one of `after` and `before` may be supplied")

        played = await self.get(
            "me/player/recently-played",
            params={
                "limit": limit,
                "after": int(after.timestamp() * 1000) if after is not MISSING else MISSING,
                "before": int(before.timestamp() * 1000) if before is not MISSING else MISSING,
            },
        )
        assert played is not None
        return models.CursorPaginator[models.PlayHistory].model_validate_json(played)

    @validator
    async def get_users_queue(self) -> models.Queue:
        """Get the items in the user's queue.

        !!! scopes "Required Authorization Scopes"
            [`USER_READ_CURRENTLY_PLAYING`][spotify.enums.Scope.USER_READ_CURRENTLY_PLAYING]
            & [`USER_READ_PLAYBACK_STATE`][spotify.enums.Scope.USER_READ_PLAYBACK_STATE]

        Returns
        -------
        models.Queue
            The queue.
        """
        queue = await self.get("me/player/queue")
        assert queue is not None
        return models.Queue.model_validate_json(queue)

    @validator
    async def add_item_to_playback_queue(
        self,
        uri: str,
        *,
        device_id: MissingOr[str] = MISSING,
    ) -> None:
        """Add an item to the end of the user's current playback queue.

        !!! scopes "Required Authorization Scope"
            [`USER_MODIFY_PLAYBACK_STATE`][spotify.enums.Scope.USER_MODIFY_PLAYBACK_STATE]

        !!! premium
            This endpoint only works for users who have Spotify Premium.

        Parameters
        ----------
        uri : str
            URI of a **track** or **episode** to add to the queue.
        device_id : str, optional
            The ID of the device this command is targeting. Default: currently active device.
        """
        await self.post("me/player/queue", params={"uri": uri, "device_id": device_id})

    # TODO: create a helper object for the query field
    @validator
    async def get_playlist(
        self,
        playlist_id: str,
        *,
        market: MissingOr[str] = MISSING,
        fields: MissingOr[str] = MISSING,
    ) -> models.Playlist:
        """Get a playlist.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).
        fields : str, optional
            Filters for the query. If omitted, all fields are returned.

            !!! info
                * The value for this field should be a comma-separated list of the fields to return.
                * **Example:** `description,uri`
                * A dot separator can be used to specify non-reoccurring fields.
                * Parentheses can be used to specify reoccurring fields within objects.
                * **Example:** `tracks.items(added_at,added_by.id)`
                * **Example:** `tracks.items(track(name,href,album(name,href)))`
                * Fields can be excluded by prefixing them with an exclamation mark (`!`).
                * **Example:** `tracks.items(track(name,href,album(!name,href)))`
                * **Example:** `tracks.items(added_by.id,track(name,href,album(name,href)))`

        Returns
        -------
        models.Playlist
            The requested playlist.
        """
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

    @validator
    async def change_playlist_details(
        self,
        playlist_id: str,
        *,
        name: MissingOr[str] = MISSING,
        public: MissingOr[bool] = MISSING,
        collaborative: MissingOr[bool] = MISSING,
        description: MissingOr[str] = MISSING,
    ) -> None:
        """Change details for a playlist the current user owns.

        !!! scopes "Authorization Scopes"
            * [`PLAYLIST_MODIFY_PUBLIC`][spotify.enums.Scope.PLAYLIST_MODIFY_PUBLIC] - required to
                modify the current user's public playlists.
            * [`PLAYLIST_MODIFY_PRIVATE`][spotify.enums.Scope.PLAYLIST_MODIFY_PRIVATE] - required to
                modify the current user's private playlists.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.
        name : str, optional
            The new name for the playlist.
        public : bool, optional
            Whether or not the playlist should be made public.
        collaborative : bool, optional
            Whether or not the playlist should be made collaborative.

            !!! note
                This can only be set to `True` on **non-public** playlists
        description : str, optional
            The new description for the playlist.

            !!! note
                The Spotify Web API is bugged, and does not allow you to clear the description field
                through the API. Setting it to `None`, `""` or even `False` will have no effect.
        """
        await self.put(
            f"playlists/{playlist_id}",
            json={
                "name": name,
                "public": public,
                "collaborative": collaborative,
                "description": description,
            },
        )

    # TODO: create a helper object for the query field
    @validator
    async def get_playlist_items(
        self,
        playlist_id: str,
        *,
        market: MissingOr[str] = MISSING,
        fields: MissingOr[str] = MISSING,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
    ) -> models.Paginator[models.PlaylistItem]:
        """Get full details of the items of a playlist.

        !!! scopes "Optional Authorization Scope"
            [`PLAYLIST_READ_PRIVATE`][spotify.enums.Scope.PLAYLIST_READ_PRIVATE] - required to
            access a private playlist belonging to the current user.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).
        fields : str, optional
            Filters for the query. If omitted, all fields are returned.

            !!! info
                * The value for this field should be a comma-separated list of the fields to return.
                * **Example:** `total,limit`
                * A dot separator can be used to specify non-reoccurring fields.
                * Parentheses can be used to specify reoccurring fields within objects.
                * **Example:** `items(added_at,added_by.id)`
                * **Example:** `items(track(name,href,album(name,href)))`
                * Fields can be excluded by prefixing them with an exclamation mark (`!`).
                * **Example:** `items.track.album(!external_urls,images)`
                * **Example:** `items(added_by.id,track(name,href,album(name,href)))`
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).
        """
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

    # TODO: split replace and reorder into their own overloads
    @validator
    async def update_playlist_items(
        self,
        playlist_id: str,
        *,
        uris: MissingOr[list[str]] = MISSING,
        range_start: MissingOr[int] = MISSING,
        insert_before: MissingOr[int] = MISSING,
        range_length: MissingOr[int] = MISSING,
        snapshot_id: MissingOr[str] = MISSING,
    ) -> str:
        """Reorder or replace playlist items.

        !!! scopes "Optional Authorization Scopes"
            * [`PLAYLIST_MODIFY_PUBLIC`][spotify.enums.Scope.PLAYLIST_MODIFY_PUBLIC] - required to
            modify the current user's public playlists.
            * [`PLAYLIST_MODIFY_PRIVATE`][spotify.enums.Scope.PLAYLIST_MODIFY_PRIVATE] - required to
            modify the current user's private playlists.

        !!! note
            Replace and reorder are mutually exclusive operations which cannot be applied together in
            the same request.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.
        uris : list[str], optional
            URIs of **tracks** or **episodes** to add to the playlist. Maximum: 100.
        range_start : int, optional
            The position of the first item to be reordered.
        insert_before : int, optional
            The position where the items should be inserted.
        range_length : int, default: 1
            The amount of items to be reordered.
        snapshot_id : str, optional
            The playlist's snapshot ID against which you want to make the changes.

        Returns
        -------
        str
            A snapshot ID for the new playlist version.

        Examples
        --------
        * To reorder the first item to the end of a playlist with 10 items:
            Set `range_start` to `0` and `insert_before` to `10`
        * To reorder the last item to the start in a playlist with 10 items:
            Set `range_start` to `9` and `insert_before` to `0`
        * To move the items at index 9-10 to the start of the playlist:
            Set `range_start` to `9`, `range_length` to `2` and `insert_before` to `0`
        """
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
        return internals.SnapshotID.model_validate_json(snapshot_id_).snapshot_id

    @validator
    async def add_items_to_playlist(
        self,
        playlist_id: str,
        *,
        uris: list[str],
        position: MissingOr[int] = MISSING,
    ) -> str:
        """Add items to a playlist.

        !!! scopes "Optional Authorization Scopes"
            * [`PLAYLIST_MODIFY_PUBLIC`][spotify.enums.Scope.PLAYLIST_MODIFY_PUBLIC] - required to
            modify the current user's public playlists.
            * [`PLAYLIST_MODIFY_PRIVATE`][spotify.enums.Scope.PLAYLIST_MODIFY_PRIVATE] - required to
            modify the current user's private playlists.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.
        uris : list[str]
            URIs of **tracks** or **episodes** to add to the playlist. Maximum: 100.
        position : int, optional
            The position at which to insert the items (position 0 being the start).

        Returns
        -------
        str
            A snapshot ID for the new playlist version.
        """
        snapshot_id = await self.post(
            f"playlists/{playlist_id}/tracks",
            json={
                "position": position,
                "uris": uris,
            },
        )
        assert snapshot_id is not None
        return internals.SnapshotID.model_validate_json(snapshot_id).snapshot_id

    @validator
    async def remove_playlist_items(
        self,
        playlist_id: str,
        *,
        uris: list[str],
        snapshot_id: MissingOr[str] = MISSING,
    ) -> str:
        """Remove items from a playlist.

        !!! scopes "Optional Authorization Scopes"
            * [`PLAYLIST_MODIFY_PUBLIC`][spotify.enums.Scope.PLAYLIST_MODIFY_PUBLIC] - required to
            modify the current user's public playlists.
            * [`PLAYLIST_MODIFY_PRIVATE`][spotify.enums.Scope.PLAYLIST_MODIFY_PRIVATE] - required to
            modify the current user's private playlists.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.
        uris : list[str]
            URIs of **tracks** or **episodes** to remove from the playlist. Maximum: 100.
        snapshot_id : str, optional
            The playlist's snapshot ID against which you want to make the changes.

        Returns
        -------
        str
            A snapshot ID for the new playlist version.
        """
        tracks = [{"uri": uri} for uri in uris]
        snapshot_id_ = await self.delete(
            f"playlists/{playlist_id}/tracks",
            json={"tracks": tracks, "snapshot_id": snapshot_id},
        )
        assert snapshot_id_ is not None
        return internals.SnapshotID.model_validate_json(snapshot_id_).snapshot_id

    @validator
    async def get_current_users_playlists(
        self,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
    ) -> models.Paginator[models.SimplePlaylist]:
        """Get a list of the playlists owned or followed by the current user.

        !!! scopes "Optional Authorization Scope"
            [`PLAYLIST_READ_PRIVATE`][spotify.enums.Scope.PLAYLIST_READ_PRIVATE] - required to
            access the current user's private playlists.

        Parameters
        ----------
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).

        Returns
        -------
        models.Paginator[models.SimplePlaylist]
            The requested playlists.
        """
        playlists = await self.get(
            "me/playlists",
            params={
                "limit": limit,
                "offset": offset,
            },
        )
        assert playlists is not None
        return models.Paginator[models.SimplePlaylist].model_validate_json(playlists)

    @validator
    async def get_users_playlists(
        self,
        user_id: str,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
    ) -> models.Paginator[models.SimplePlaylist]:
        """Get a list of the playlists owned or followed by a user.

        !!! scopes "Optional Authorization Scopes"
            * [`PLAYLIST_READ_PRIVATE`][spotify.enums.Scope.PLAYLIST_READ_PRIVATE] - required to
            access the current user's private playlists.
            * [`PLAYLIST_READ_COLLABORATIVE`][spotify.enums.Scope.PLAYLIST_READ_COLLABORATIVE] -
            required to access the current user's collaborative playlists.

        Parameters
        ----------
        user_id : str
            The ID of the user.
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).

        Returns
        -------
        models.Paginator[models.SimplePlaylist]
            The requested playlists.
        """
        playlists = await self.get(
            f"users/{user_id}/playlists",
            params={
                "limit": limit,
                "offset": offset,
            },
        )
        assert playlists is not None
        return models.Paginator[models.SimplePlaylist].model_validate_json(playlists)

    @validator
    async def create_playlist(
        self,
        user_id: str,
        *,
        name: str,
        public: MissingOr[bool] = MISSING,
        collaborative: MissingOr[bool] = MISSING,
        description: MissingOr[str] = MISSING,
    ) -> models.Playlist:
        """Create a playlist for a Spotify user.

        !!! scopes "Optional Authorization Scopes"
            * [`PLAYLIST_MODIFY_PUBLIC`][spotify.enums.Scope.PLAYLIST_MODIFY_PUBLIC] - required to
            add to the current user's public playlists.
            * [`PLAYLIST_MODIFY_PRIVATE`][spotify.enums.Scope.PLAYLIST_MODIFY_PRIVATE] - required to
            add to the current user's private playlists.

        Parameters
        ----------
        user_id : str
            The ID of the user.
        name : str
            The name for the new playlist.
        public : bool, default: True
            Whether or not the playlist will be public.

            !!! note
                To set `public` to `False`, the user must have granted the `playlist-modify-private` scope.
        collaborative : bool, default: False
            Whether or not the playlist will be collaborative.

            !!! note
                To set `collaborative` to `True`, `public` must be set to `False` and the user must
                have granted the `playlist-modify-private` and `playlist-modify-public` scopes.
        description : str, optional
            The playlist's description.

        Returns
        -------
        models.Playlist
            The newly created playlist.
        """
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

    @validator
    async def get_featured_playlists(
        self,
        *,
        locale: MissingOr[str] = MISSING,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
    ) -> models.Playlists:
        """Get a list of Spotify featured playlists (shown, for example, on a Spotify player's 'Browse' tab).

        Parameters
        ----------
        locale : str, optional
            Desired language to get content in. Default: American English
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).

        Returns
        -------
        models.Playlists
            The requested playlists.
        """
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

    @validator
    async def get_categorys_playlists(
        self,
        category_id: str,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
    ) -> models.Playlists:
        """Get a list of Spotify playlists tagged with a particular category.

        Parameters
        ----------
        category_id : str
            The ID of the category.
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).

        Returns
        -------
        models.Playlists
            The requested playlists.
        """
        playlists = await self.get(
            f"browse/categories/{category_id}/playlists",
            params={
                "limit": limit,
                "offset": offset,
            },
        )
        assert playlists is not None
        return models.Playlists.model_validate_json(playlists)

    @validator
    async def get_playlist_cover_image(
        self,
        playlist_id: str,
    ) -> list[models.Image]:
        """Get the current image associated with a specific playlist.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.

        Returns
        -------
        list[models.Image]
            The playlist cover image, potentially in different sizes.
        """
        images = await self.get(f"playlists/{playlist_id}/images")
        assert images is not None
        img_list: list[dict[str, str | int]] = json_.loads(images)
        return [models.Image(**img) for img in img_list]  # pyright: ignore[reportArgumentType]

    @validator
    async def add_custom_playlist_cover_image(
        self,
        playlist_id: str,
        *,
        image: bytes,
    ) -> None:
        """Replace the image used to represent a specific playlist.

        !!! scopes "Required Authorization Scope"
            * [`UGC_IMAGE_UPLOAD`][spotify.enums.Scope.UGC_IMAGE_UPLOAD] - required to
            upload images to Spotify on the current user's behalf.

        !!! scopes "Optional Authorization Scopes"
            * [`PLAYLIST_MODIFY_PUBLIC`][spotify.enums.Scope.PLAYLIST_MODIFY_PUBLIC] - required to
            modify the current user's public playlists.
            * [`PLAYLIST_MODIFY_PRIVATE`][spotify.enums.Scope.PLAYLIST_MODIFY_PRIVATE] - required to
            modify the current user's private playlists.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.
        image : bytes
            JPEG image data, in bytes. Maximum size is 256 KB.
        """
        image = base64.encodebytes(image).replace(b"\n", b"")
        await self.put(
            f"playlists/{playlist_id}/images",
            data=image,
        )

    # TODO: create builder class for this
    @validator
    async def search_for_item(
        self,
        *,
        types: list[enums.SearchType],
        query: MissingOr[str] = MISSING,
        album: MissingOr[str] = MISSING,
        artist: MissingOr[str] = MISSING,
        track: MissingOr[str] = MISSING,
        start_year: MissingOr[int] = MISSING,
        end_year: MissingOr[int] = MISSING,
        upc: MissingOr[str] = MISSING,
        hipster: MissingOr[bool] = MISSING,
        new: MissingOr[bool] = MISSING,
        isrc: MissingOr[str] = MISSING,
        genres: MissingOr[list[str]] = MISSING,
        market: MissingOr[str] = MISSING,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
        include_external: MissingOr[bool] = MISSING,
    ) -> models.SearchResult:
        """Get Spotify catalog information about albums, artists, playlists, tracks, shows, episodes or audiobooks
        that match the search query.

        Parameters
        ----------
        types : list[enums.SearchType]
            Type of items to search for.
        query : str, optional
            The search query.
        album : str, optional
            The album. Can be used while searching **albums** and **tracks**.
        artist : str, optional
            The artist. Can be used while searching **albums**, **artists** and **tracks**.
        track : str, optional
            The track. Can be used while searching **tracks**.

            !!! note
                start_year and end_year can be used to create a range of years to search across.
        start_year : int, optional
            The year, or start year if also using `end_year`. Can be used while searching **albums**, **artists**
            and **tracks**.
        end_year : int, optional
            The end year. If supplied, `start_year` must also be supplied. Can be used while searching **albums**,
            **artists** and **tracks**.
        upc : str, optional
            The [Universal Product Code](http://en.wikipedia.org/wiki/Universal_Product_Code) for the item.
            Can be used while searching **albums**.
        hipster : bool, optional
            If `True`, get **albums** with the lowest 10% popularity.
            Can be used while searching **albums**.
        new : bool, optional
            If `True`, get **albums** released within the past 2 weeks.
            Can be used while searching **albums**.
        isrc : str, optional
            The [International Standard Recording Code](http://en.wikipedia.org/wiki/International_Standard_Recording_Code)
            for the item. Can be used while searching **tracks**.
        genres : list[str], optional
            The genre(s). Can be used while searching **artists** and **tracks**.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).
        limit : int, default: 20
            The maximum number of results to return in each item type. Default: 20. Minimum: 0. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).
        include_external : bool, optional
            If set to `True` it signals that the client can play externally hosted audio content, and marks the content as
            playable in the response.

        Returns
        -------
        models.SearchResult
            The search result.
        """
        if len(types) < 1:
            raise ValueError("`types` may not be empty")

        if start_year is MISSING and end_year is not MISSING:
            raise ValueError("end_year cannot be provided without start_year")

        if start_year is not MISSING and end_year is not MISSING:
            final_year = f"year:{start_year}-{end_year}"
        elif start_year is not MISSING:
            final_year = f"year:{start_year}"
        else:
            final_year = MISSING

        final_album = f"album:{album}" if album is not MISSING else MISSING
        final_artist = f"artist:{artist}" if artist is not MISSING else MISSING
        final_track = f"track:{track}" if track is not MISSING else MISSING
        final_upc = f"upc:{upc}" if upc is not MISSING else MISSING
        final_hipster = "tag:hipster" if hipster is not MISSING and hipster is True else MISSING
        final_new = "tag:new" if new is not MISSING and new is True else MISSING
        final_isrc = f"isrc:{isrc}" if isrc is not MISSING else MISSING
        final_genre = (
            f"genre:{' '.join(genres)}" if genres is not MISSING and len(genres) > 0 else MISSING
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
                if item is not MISSING
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
                if include_external is not MISSING and include_external is True
                else MISSING,
            },
        )
        assert results is not None
        return models.SearchResult.model_validate_json(results)

    @validator
    async def get_show(self, show_id: str, *, market: MissingOr[str] = MISSING) -> models.Show:
        """Get Spotify catalog information for a single show.

        Parameters
        ----------
        show_id : str
            The ID of the show.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        models.Show
            The requested show.
        """
        show = await self.get(f"shows/{show_id}", params={"market": market})
        assert show is not None
        return models.Show.model_validate_json(show)

    @validator
    async def get_several_shows(
        self, show_ids: list[str], *, market: MissingOr[str] = MISSING
    ) -> list[models.SimpleShow]:
        """Get Spotify catalog information for several shows.

        Parameters
        ----------
        show_ids : list[str]
            The IDs of the shows.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        list[models.SimpleShow]
            The requested shows.
        """
        shows = await self.get("shows", params={"ids": ",".join(show_ids), "market": market})
        assert shows is not None
        return internals.Shows.model_validate_json(shows).shows

    @validator
    async def get_show_episodes(
        self,
        show_id: str,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
        market: MissingOr[str] = MISSING,
    ) -> models.Paginator[models.SimpleEpisode]:
        """Get Spotify catalog information about a shows's episodes.

        Parameters
        ----------
        show_id : str
            The ID of the show.
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

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

    @validator
    async def get_users_saved_shows(
        self,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
    ) -> models.Paginator[models.SavedShow]:
        """Get a list of the shows saved in the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_READ`][spotify.enums.Scope.USER_LIBRARY_READ]

        Parameters
        ----------
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).

        Returns
        -------
        models.Paginator[models.SavedShow]
            A paginator who's items are a list of shows.
        """
        shows = await self.get(
            "me/shows",
            params={"limit": limit, "offset": offset},
        )
        assert shows is not None
        return models.Paginator[models.SavedShow].model_validate_json(shows)

    @validator
    async def save_shows_for_current_user(
        self,
        show_ids: list[str],
    ) -> None:
        """Save one or more shows to the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_MODIFY`][spotify.enums.Scope.USER_LIBRARY_MODIFY]

        Parameters
        ----------
        show_ids : list[str]
            The IDs of the shows. Maximum: 50.
        """
        await self.put("me/shows", params={"ids": ",".join(show_ids)})

    @validator
    async def remove_users_saved_shows(
        self, show_ids: list[str], *, market: MissingOr[str] = MISSING
    ) -> None:
        """Remove one or more shows from the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_MODIFY`][spotify.enums.Scope.USER_LIBRARY_MODIFY]

        Parameters
        ----------
        show_ids : list[str]
            The IDs of the shows. Maximum: 50.
        market : str, optional
            Only modify content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).
        """
        await self.delete("me/shows", params={"ids": ",".join(show_ids), "market": market})

    @validator
    async def check_users_saved_shows(self, show_ids: list[str]) -> list[bool]:
        """Check if one or more shows is already saved in the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_READ`][spotify.enums.Scope.USER_LIBRARY_READ]

        Parameters
        ----------
        show_ids : list[str]
            The IDs of the shows. Maximum: 50.

        Returns
        -------
        list[bool]
            A list of booleans dictating whether or not the corresponding shows are already saved.
        """
        shows = await self.get("me/shows/contains", params={"ids": ",".join(show_ids)})
        assert shows is not None
        return json_.loads(shows)

    @validator
    async def get_track(
        self, track_id: str, *, market: MissingOr[str] = MISSING
    ) -> models.TrackWithSimpleArtist:
        """Get Spotify catalog information for a single track.

        Parameters
        ----------
        track_id : str
            The ID of the track.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        models.TrackWithSimpleArtist
            The requested track.
        """
        track = await self.get(f"tracks/{track_id}", params={"market": market})
        assert track is not None
        return models.TrackWithSimpleArtist.model_validate_json(track)

    @validator
    async def get_several_tracks(
        self, track_ids: list[str], *, market: MissingOr[str] = MISSING
    ) -> list[models.TrackWithSimpleArtist]:
        """Get Spotify catalog information for several tracks.

        Parameters
        ----------
        track_ids : list[str]
            The IDs of the tracks. Maximum: 50.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        list[models.TrackWithSimpleArtist]
            The requested tracks.
        """
        tracks = await self.get("tracks", params={"ids": ",".join(track_ids), "market": market})
        assert tracks is not None
        return internals.Tracks.model_validate_json(tracks).tracks

    @validator
    async def get_users_saved_tracks(
        self,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
        market: MissingOr[str] = MISSING,
    ) -> models.Paginator[models.SavedTrack]:
        """Get a list of the tracks saved in the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_READ`][spotify.enums.Scope.USER_LIBRARY_READ]

        Parameters
        ----------
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item).
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).

        Returns
        -------
        models.Paginator[models.SavedTrack]
            A paginator who's items are a list of tracks.
        """
        tracks = await self.get(
            "me/tracks",
            params={"limit": limit, "offset": offset, "market": market},
        )
        assert tracks is not None
        return models.Paginator[models.SavedTrack].model_validate_json(tracks)

    @validator
    async def save_tracks_for_current_user(
        self,
        track_ids: list[str],
    ) -> None:
        """Save one or more tracks to the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_MODIFY`][spotify.enums.Scope.USER_LIBRARY_MODIFY]

        Parameters
        ----------
        track_ids : list[str]
            The IDs of the tracks. Maximum: 50.
        """
        await self.put("me/tracks", params={"ids": ",".join(track_ids)})

    @validator
    async def remove_users_saved_tracks(self, track_ids: list[str]) -> None:
        """Remove one or more tracks from the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_MODIFY`][spotify.enums.Scope.USER_LIBRARY_MODIFY]

        Parameters
        ----------
        track_ids : list[str]
            The IDs of the tracks. Maximum: 50.
        """
        await self.delete("me/tracks", params={"ids": ",".join(track_ids)})

    @validator
    async def check_users_saved_tracks(self, track_ids: list[str]) -> list[bool]:
        """Check if one or more tracks is already saved in the current user's 'Your Music' library.

        !!! scopes "Required Authorization Scope"
            [`USER_LIBRARY_READ`][spotify.enums.Scope.USER_LIBRARY_READ]

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

    @validator
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

    @validator
    async def get_several_tracks_audio_features(
        self, track_ids: list[str]
    ) -> list[models.AudioFeatures]:
        """Get audio feature information for several tracks.

        Parameters
        ----------
        track_ids : list[str]
            The IDs of the tracks. Maximum: 100.

        Returns
        -------
        list[models.AudioFeatures]
            The tracks' audio features.
        """
        features = await self.get("audio-features", params={"ids": ",".join(track_ids)})
        assert features is not None
        return internals.AudioFeatures.model_validate_json(features).audio_features

    @validator
    async def get_tracks_audio_analysis(self, track_id: str) -> models.AudioAnalysis:
        """Get a low-level audio analysis for a track in the Spotify catalog.
        The audio analysis describes the track's structure and musical content,
        including rhythm, pitch and timbre.

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

    @validator
    async def get_recommendations(
        self,
        seed_artists: MissingOr[list[str]] = MISSING,
        seed_genres: MissingOr[list[str]] = MISSING,
        seed_tracks: MissingOr[list[str]] = MISSING,
        *,
        limit: MissingOr[int] = MISSING,
        market: MissingOr[str] = MISSING,
        min_acousticness: MissingOr[float] = MISSING,
        max_acousticness: MissingOr[float] = MISSING,
        target_acousticness: MissingOr[float] = MISSING,
        min_danceability: MissingOr[float] = MISSING,
        max_danceability: MissingOr[float] = MISSING,
        target_danceability: MissingOr[float] = MISSING,
        min_duration: MissingOr[datetime.timedelta] = MISSING,
        max_duration: MissingOr[datetime.timedelta] = MISSING,
        target_duration: MissingOr[datetime.timedelta] = MISSING,
        min_energy: MissingOr[float] = MISSING,
        max_energy: MissingOr[float] = MISSING,
        target_energy: MissingOr[float] = MISSING,
        min_instrumentalness: MissingOr[float] = MISSING,
        max_instrumentalness: MissingOr[float] = MISSING,
        target_instrumentalness: MissingOr[float] = MISSING,
        min_key: MissingOr[int] = MISSING,
        max_key: MissingOr[int] = MISSING,
        target_key: MissingOr[int] = MISSING,
        min_liveness: MissingOr[float] = MISSING,
        max_liveness: MissingOr[float] = MISSING,
        target_liveness: MissingOr[float] = MISSING,
        min_loudness: MissingOr[float] = MISSING,
        max_loudness: MissingOr[float] = MISSING,
        target_loudness: MissingOr[float] = MISSING,
        min_mode: MissingOr[int] = MISSING,
        max_mode: MissingOr[int] = MISSING,
        target_mode: MissingOr[int] = MISSING,
        min_popularity: MissingOr[int] = MISSING,
        max_popularity: MissingOr[int] = MISSING,
        target_popularity: MissingOr[int] = MISSING,
        min_speechiness: MissingOr[float] = MISSING,
        max_speechiness: MissingOr[float] = MISSING,
        target_speechiness: MissingOr[float] = MISSING,
        min_tempo: MissingOr[float] = MISSING,
        max_tempo: MissingOr[float] = MISSING,
        target_tempo: MissingOr[float] = MISSING,
        min_time_signature: MissingOr[int] = MISSING,
        max_time_signature: MissingOr[int] = MISSING,
        target_time_signature: MissingOr[int] = MISSING,
        min_valence: MissingOr[float] = MISSING,
        max_valence: MissingOr[float] = MISSING,
        target_valence: MissingOr[float] = MISSING,
    ) -> models.Recommendations:
        """Get recommendations based on other artists, genres and/or tracks.

        !!! note
            One of `seed_artists`, `seed_genres` and `seed_tracks` must be provided.
            Up to 5 seed values may be provided in any combination of `seed_artists`,
            `seed_genres` and `seed_tracks`.

        Parameters
        ----------
        seed_artists : list[str], optional
            IDs of seed artists.
        seed_genres : list[str], optional
            Seed genres.
        seed_tracks : list[str], optional
            IDs of seed tracks.
        limit : int, default: 20
            The target size of the list of recommended tracks. For seeds with unusually small pools or
            when highly restrictive filtering is applied, it may be impossible to generate the requested
            number of recommended tracks. Debugging information for such cases is available in the response.
            Default: 20. Minimum: 1. Maximum: 100.
        market : str, optional
            Only get content available in that market.
            Must be an [ISO 3166-1 alpha-2 country code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).
        min_acousticness : float, optional
            Minimum acousticness. Range: `0.0` - `1.0`.
        max_acousticness : float, optional
            Maximum acousticness. Range: `0.0` - `1.0`.
        target_acousticness : float, optional
            Target acousticness. Range: `0.0` - `1.0`.
        min_danceability : float, optional
            Minimum danceability. Range: `0.0` - `1.0`.
        max_danceability : float, optional
            Maximum danceability. Range: `0.0` - `1.0`.
        target_danceability : float, optional
            Target danceability. Range: `0.0` - `1.0`.
        min_duration : datetime.timedelta, optional
            Minimum duration.
        max_duration : datetime.timedelta, optional
            Maximum duration.
        target_duration : datetime.timedelta, optional
            Target duration.
        min_energy : float, optional
            Minimum energy. Range: `0.0` - `1.0`.
        max_energy : float, optional
            Maximum energy. Range: `0.0` - `1.0`.
        target_energy : float, optional
            Target energy. Range: `0.0` - `1.0`.
        min_instrumentalness : float, optional
            Minimum instrumentalness. Range: `0.0` - `1.0`.
        max_instrumentalness : float, optional
            Maximum instrumentalness. Range: `0.0` - `1.0`.
        target_instrumentalness : float, optional
            Target instrumentalness. Range: `0.0` - `1.0`.
        min_key : int, optional
            Minimum key. Range: `0` - `11`.
        max_key : int, optional
            Maximum instrumentalness. Range: `0` - `11`.
        target_key : int, optional
            Target instrumentalness. Range: `0` - `11`.
        min_liveness : float, optional
            Minimum liveness. Range: `0.0` - `1.0`.
        max_liveness : float, optional
            Maximum liveness. Range: `0.0` - `1.0`.
        target_liveness : float, optional
            Target liveness. Range: `0.0` - `1.0`.
        min_loudness : float, optional
            Minimum loudness. Range: `0.0` - `1.0`.
        max_loudness : float, optional
            Maximum loudness. Range: `0.0` - `1.0`.
        target_loudness : float, optional
            Target loudness. Range: `0.0` - `1.0`.
        min_mode : int, optional
            Minimum mode. Range: `0.0` - `1.0`.
        max_mode : int, optional
            Maximum mode. Range: `0.0` - `1.0`.
        target_mode : int, optional
            Target mode. Range: `0.0` - `1.0`.
        min_popularity : int, optional
            Minimum popularity. Range: `0` - `100`.
        max_popularity : int, optional
            Maximum popularity. Range: `0` - `100`.
        target_popularity : int, optional
            Target popularity. Range: `0` - `100`.
        min_speechiness : float, optional
            Minimum speechiness. Range: `0.0` - `1.0`.
        max_speechiness : float, optional
            Maximum speechiness. Range: `0.0` - `1.0`.
        target_speechiness : float, optional
            Target speechiness. Range: `0.0` - `1.0`.
        min_tempo : float, optional
            Minimum tempo.
        max_tempo : float, optional
            Maximum tempo.
        target_tempo : float, optional
            Target tempo.
        min_time_signature : int, optional
            Minimum time signature. Maximum: `11`.
        max_time_signature : int, optional
            Maximum time signature.
        target_time_signature : int, optional
            Target time signature.
        min_valence : float, optional
            Minimum valence. Range: `0.0` - `1.0`.
        max_valence : float, optional
            Maximum valence. Range: `0.0` - `1.0`.
        target_valence : float, optional
            Target valence. Range: `0.0` - `1.0`.
        """
        if seed_artists is MISSING and seed_genres is MISSING and seed_tracks is MISSING:
            raise ValueError(
                "one of `seed_artists`, `seed_genres` and `seed_tracks` must be provided"
            )

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
                "min_duration_ms": min_duration.total_seconds() * 1000
                if min_duration is not MISSING
                else MISSING,
                "max_duration_ms": max_duration.total_seconds() * 1000
                if max_duration is not MISSING
                else MISSING,
                "target_duration_ms": target_duration.total_seconds() * 1000
                if target_duration is not MISSING
                else MISSING,
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

    @validator
    async def get_current_users_profile(self) -> models.OwnUser:
        """Get detailed profile information about the current user.

        !!! scopes "Optional Authorization Scopes"
            * [`USER_READ_PRIVATE`][spotify.enums.Scope.USER_READ_PRIVATE] - required to access
            the current user's subscription details.
            * [`USER_READ_EMAIL`][spotify.enums.Scope.USER_READ_EMAIL] - required to access
            the current user's email.

        Returns
        -------
        models.OwnUser
            The current user.
        """
        user = await self.get("me")
        assert user is not None
        return models.OwnUser.model_validate_json(user)

    @typing.overload
    async def get_users_top_items(
        self,
        type: typing.Literal[enums.TopItemType.ARTISTS],
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
        time_range: MissingOr[enums.TimeRange] = MISSING,
    ) -> models.Paginator[models.Artist]: ...

    @typing.overload
    async def get_users_top_items(
        self,
        type: typing.Literal[enums.TopItemType.TRACKS],
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
        time_range: MissingOr[enums.TimeRange] = MISSING,
    ) -> models.Paginator[models.TrackWithSimpleArtist]: ...

    @validator
    async def get_users_top_items(
        self,
        type: enums.TopItemType,
        *,
        limit: MissingOr[int] = MISSING,
        offset: MissingOr[int] = MISSING,
        time_range: MissingOr[enums.TimeRange] = MISSING,
    ) -> models.Paginator[models.Artist] | models.Paginator[models.TrackWithSimpleArtist]:
        """Get the current user's top artists or tracks based on calculated affinity.

        !!! scopes "Required Authorization Scope"
            [`USER_TOP_READ`][spotify.enums.Scope.USER_TOP_READ]

        Parameters
        ----------
        type : enums.TopItemType
            The type of entity to return.
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset : int, default: 0
            The index of the first item to return. Default: 0 (the first item)
        time_range : enums.TimeRange, default: Medium Term
            Over what time frame the affinities are computed.

        Returns
        -------
        models.Paginator[models.Artist]
            A paginator who's items are a list of artists.
        models.Paginator[models.TrackWithSimpleArtist]
            A paginator who's items are a list of tracks.
        """
        items = await self.get(
            f"me/top/{type.value}",
            params={
                "limit": limit,
                "offset": offset,
                "time_range": time_range.value if time_range is not MISSING else MISSING,
            },
        )
        assert items is not None
        if type is enums.TopItemType.ARTISTS:
            return models.Paginator[models.Artist].model_validate_json(items)
        else:
            assert type is enums.TopItemType.TRACKS
            return models.Paginator[models.TrackWithSimpleArtist].model_validate_json(items)

    @validator
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

    @validator
    async def follow_playlist(
        self,
        playlist_id: str,
        public: MissingOr[bool] = MISSING,
    ) -> None:
        """Add the current user as a follower of a playlist.

        !!! scopes "Optional Authorization Scopes"
            [`PLAYLIST_MODIFY_PUBLIC`][spotify.enums.Scope.PLAYLIST_MODIFY_PUBLIC] - required to
            add the playlist to the current user's public playlists.
            [`PLAYLIST_MODIFY_PRIVATE`][spotify.enums.Scope.PLAYLIST_MODIFY_PRIVATE] - required to
            add the playlist to the current user's private playlists.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.
        public : bool, default: True
            Whether or not the playlist will be included in the user's public playlists (added to profile).
        """
        await self.put(f"playlists/{playlist_id}/followers", json={"public": public})

    @validator
    async def unfollow_playlist(
        self,
        playlist_id: str,
    ) -> None:
        """Remove the current user as a follower of a playlist.

        !!! scopes "Optional Authorization Scopes"
            * [`PLAYLIST_MODIFY_PUBLIC`][spotify.enums.Scope.PLAYLIST_MODIFY_PUBLIC] - required to
            remove the playlist from the current user's public playlists.
            * [`PLAYLIST_MODIFY_PRIVATE`][spotify.enums.Scope.PLAYLIST_MODIFY_PRIVATE] - required to
            remove the playlist from the current user's private playlists.

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.
        """
        await self.delete(f"playlists/{playlist_id}/followers")

    @validator
    async def get_followed_artists(
        self,
        after: MissingOr[str] = MISSING,
        limit: MissingOr[int] = MISSING,
    ) -> models.CursorPaginator[models.Artist]:
        """Get the current user's followed artists.

        !!! scopes "Required Authorization Scope"
            [`USER_FOLLOW_READ`][spotify.enums.Scope.USER_FOLLOW_READ]

        Parameters
        ----------
        after : str, optional
            The last artist ID retrieved from the previous request.
        limit : int, default: 20
            The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.

        Returns
        -------
        models.CursorPaginator[models.Artist]
            A paginator who's items are a list of artists.
        """
        followed = await self.get(
            "me/following",
            params={"type": "artist", "after": after, "limit": limit},
        )
        assert followed is not None
        return internals.ArtistsPaginator.model_validate_json(followed).paginator

    @validator
    async def follow_artists_or_users(
        self,
        ids: list[str],
        type: enums.UserType,
    ) -> None:
        """Add the current user as a follower of one or more artists or other Spotify users.

        !!! scopes "Required Authorization Scope"
            [`USER_FOLLOW_MODIFY`][spotify.enums.Scope.USER_FOLLOW_MODIFY]

        Parameters
        ----------
        ids : list[str]
            The IDs of the artists. Maximum: 50.
        type : enums.UserType
            The user type (user/artist).
        """
        await self.put("me/following", params={"ids": ",".join(ids), "type": type.value})

    @validator
    async def unfollow_artists_or_users(self, ids: list[str], type: enums.UserType) -> None:
        """Remove the current user as a follower of one or more artists or other Spotify users.

        !!! scopes "Required Authorization Scope"
            [`USER_FOLLOW_MODIFY`][spotify.enums.Scope.USER_FOLLOW_MODIFY]

        Parameters
        ----------
        ids : list[str]
            The IDs of the artists. Maximum: 50.
        type : enums.UserType
            The user type (user/artist).
        """
        await self.delete("me/following", params={"ids": ",".join(ids), "type": type.value})

    @validator
    async def check_if_user_follows_artists_or_users(
        self,
        ids: list[str],
        type: enums.UserType,
    ) -> list[bool]:
        """Check to see if the current user is following one or more artists or other Spotify users.

        !!! scopes "Required Authorization Scope"
            [`USER_FOLLOW_READ`][spotify.enums.Scope.USER_FOLLOW_READ]

        Parameters
        ----------
        ids : list[str]
            The IDs of the artists. Maximum: 50.
        type : enums.UserType
            The user type (user/artist).

        Returns
        -------
        list[bool]
            A list of booleans dictating whether or not the current user has followed the corresponding users or artists.
        """
        follows = await self.get(
            "me/following/contains",
            params={"ids": ",".join(ids), "type": type.value},
        )
        assert follows is not None
        return json_.loads(follows)

    @validator
    async def check_if_current_user_follows_playlist(
        self,
        playlist_id: str,
    ) -> bool:
        """Check to see if the current user is following a specified playlist.

        !!! scopes "Required Authorization Scope"
            [`PLAYLIST_READ_PRIVATE`][spotify.enums.Scope.PLAYLIST_READ_PRIVATE]

        Parameters
        ----------
        playlist_id : str
            The ID of the playlist.

        Returns
        -------
        bool
            Whether or not the current user is following the playlist.
        """
        follows = await self.get(
            f"playlists/{playlist_id}/followers/contains",
        )
        assert follows is not None
        return json_.loads(follows)[0]


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
