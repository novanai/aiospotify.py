from __future__ import annotations

import abc
import datetime
import typing

import attrs

from spotify import enums, utils


class ModelBase(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> ModelBase:
        ...


ModelT = typing.TypeVar("ModelT", bound=ModelBase)


@attrs.frozen
class Album(ModelBase):
    """An album."""

    album_type: enums.AlbumType
    """The type of the album."""
    total_tracks: int
    """The number of tracks in the album."""
    available_markets: list[str] | None
    """The markets in which the album is available (`ISO 3166-1 alpha-2 country codes <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_).
    Returns ``None`` if a market was specified in the request.
    
    .. note::
        An album is considered available in a market when at least 1 of its tracks is available in that market."""
    external_urls: ExternalURLs
    """Known external URLs for this album."""
    href: str
    """A link to the Web API endpoint providing full details of the album."""
    id: str
    """The Spotify ID for the album."""
    images: list[Image]
    """The cover art for the album in various sizes, widest first."""
    name: str
    """The name of the album."""
    release_date: datetime.datetime
    """The date the album was first released."""
    release_date_precision: enums.ReleaseDatePrecision
    """The precision with which ``release_date`` is known."""
    restrictions: Restrictions | None
    """Present when a content restriction is applied."""
    uri: str
    """The Spotify URI for the album."""
    artists: list[Artist]
    """The artists of the album."""
    album_group: enums.AlbumGroup | None
    """Represents the relationship between the artist and the album. 
    Present when getting an artist's albums."""
    tracks: Paginator[Track] | None
    """The tracks of the album."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Album:
        return cls(
            enums.AlbumType(payload["album_type"]),
            payload["total_tracks"],
            payload.get("available_markets"),
            ExternalURLs.from_payload(payload["external_urls"]),
            payload["href"],
            payload["id"],
            [Image.from_payload(im) for im in payload["images"]],
            payload["name"],
            utils.datetime_from_timestamp(payload["release_date"]),
            enums.ReleaseDatePrecision(payload["release_date_precision"]),
            Restrictions.from_payload(res)
            if (res := payload.get("restrictions"))
            else None,
            payload["uri"],
            [Artist.from_payload(ar) for ar in payload["artists"]],
            payload.get("album_group"),
            Paginator.from_payload(tra, Track)
            if (tra := payload.get("tracks"))
            else None,
        )


@attrs.frozen
class Artist(ModelBase):
    """An artist."""

    external_urls: ExternalURLs
    """Known external URLs for this artist."""
    followers: Followers | None
    """Information about the followers of the artist."""
    genres: list[str]  # list[Genre] if I can find list of all possible genres
    """A list of the genres the artist is associated with. If not yet classified, the list is empty."""
    href: str
    """A link to the Web API endpoint providing full details of the artist."""
    id: str
    """The Spotify ID for the artist."""
    images: list[Image]
    """Images of the artist in various sizes, widest first."""
    name: str
    """The name of the artist."""
    popularity: int | None
    """The popularity of the artist. The value will be between 0 and 100, with 100 being the most popular.
    The artist's popularity is calculated from the popularity of all the artist's tracks."""
    uri: str
    """The Spotify URI for the artist."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Artist:
        return cls(
            ExternalURLs.from_payload(payload["external_urls"]),
            Followers.from_payload(fol) if (fol := payload.get("followers")) else None,
            payload.get("genres", []),
            payload["href"],
            payload["id"],
            [Image.from_payload(im) for im in payload.get("images", [])],
            payload["name"],
            payload.get("popularity"),
            payload["uri"],
        )


@attrs.frozen
class ExternalIDs(ModelBase):
    """External IDs."""

    isrc: str
    """`International Standard Recording Code <http://en.wikipedia.org/wiki/International_Standard_Recording_Code/>`_"""
    ean: str | None
    """`International Article Number <https://en.wikipedia.org/wiki/International_Article_Number_%28EAN%29>`_"""
    upc: str | None
    """`Universal Product Code <http://en.wikipedia.org/wiki/Universal_Product_Code>`_"""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> ExternalIDs:
        return cls(
            payload["isrc"],
            payload.get("ean"),
            payload.get("upc"),
        )


@attrs.frozen
class ExternalURLs(ModelBase):
    """External URLs"""

    spotify: str
    """The Spotify URL for the object."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> ExternalURLs:
        return cls(payload["spotify"])


@attrs.frozen
class Followers(ModelBase):
    """Information about followers."""

    href: str
    """This will always be set to ``None``, as the Web API does not support it at the moment."""
    total: int
    """The total number of followers."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Followers:
        return cls(
            payload["href"],
            payload["total"],
        )


@attrs.frozen
class Image(ModelBase):
    """An image."""

    url: str
    """The source URL of the image."""
    height: int
    """The image height in pixels."""
    width: int
    """The image width in pixels."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Image:
        return cls(
            payload["url"],
            payload["height"],
            payload["width"],
        )


@attrs.frozen
class Restrictions(ModelBase):
    """Content restrictions."""

    reason: enums.Reason
    """The reason for the restriction."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Restrictions:
        return cls(
            payload["reason"],
        )


@attrs.frozen
class Paginator(
    ModelBase,
    typing.Generic[ModelT],
):
    """A paginator with helpful methods to paginate
    through large amounts of content.

    TODO: make those 'helpful methods'"""

    href: str
    """A link to the Web API endpoint returning the full result of the request."""
    items: list[ModelT]
    """The requested content."""
    limit: int
    """The maximum number of items in the response."""
    next: str | None
    """URL to the next page of items."""
    offset: int
    """The offset of the items returned."""
    previous: str | None
    """URL to the previous page of items."""
    total: int
    """The total number of items available to return."""

    @classmethod
    def from_payload(
        cls, payload: dict[str, typing.Any], item_type: typing.Type[ModelT]
    ) -> Paginator[ModelT]:
        return cls(
            payload["href"],
            [item_type.from_payload(itm) for itm in payload["items"]],
            payload["limit"],
            payload["next"],
            payload["offset"],
            payload["previous"],
            payload["total"],
        )


@attrs.frozen
class Track(ModelBase):
    """A track."""

    album: Album | None
    """The album on which the track appears. Will be ``None`` when fetching an album's tracks."""
    artists: list[Artist]
    """The artists who performed the track."""
    available_markets: list[str] | None
    """A list of the countries in which the track can be played, identified by their `ISO 3166-1 alpha-2 code <http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2>`_.
    Returns ``None`` if a market was specified in the request."""
    disc_number: int
    """The disc number (usually ``1`` unless the album consists of more than one disc)."""
    duration: datetime.timedelta
    """The track length."""
    explicit: bool
    """Whether or not the track has explicit lyrics."""
    external_ids: ExternalIDs | None
    """Known external IDs for the track."""
    external_urls: ExternalURLs
    """Known external URLs for this track."""
    href: str
    """A link to the Web API endpoint providing full details of the track."""
    id: str
    """The Spotify ID for the track."""
    is_playable: bool | None
    """Whether or not the track is playable in the given market.
    Present when `Track Relinking <https://developer.spotify.com/documentation/general/guides/track-relinking-guide/>`_ is applied."""
    linked_from: Track | None
    """Present when `Track Relinking <https://developer.spotify.com/documentation/general/guides/track-relinking-guide/>`_ is applied, and the requested track has been replaced with a different track.
    The track in the linked_from object contains information about the originally requested track."""
    restrictions: Restrictions | None
    """Present when restrictions are applied to the track."""
    name: str
    """The name of the track."""
    popularity: int | None
    """The popularity of the track. The value will be between 0 and 100, with 100 being the most popular."""
    preview_url: str | None
    """A link to a 30 second preview (MP3 format) of the track. Can be ``None``"""
    track_number: int
    """The number of the track. If an album has several discs, the track number is the number on the specified disc."""
    uri: str
    """The Spotify URI for the track."""
    is_local: bool
    """Whether or not the track is from a local file."""

    @classmethod
    def from_payload(cls, payload: dict[str, typing.Any]) -> Track:
        return cls(
            Album.from_payload(alb) if (alb := payload.get("album")) else None,
            [Artist.from_payload(art) for art in payload["artists"]],
            payload.get("available_markets"),
            payload["disc_number"],
            datetime.timedelta(milliseconds=payload["duration_ms"]),
            payload["explicit"],
            ExternalIDs.from_payload(ext)
            if (ext := payload.get("external_ids"))
            else None,
            ExternalURLs.from_payload(payload["external_urls"]),
            payload["href"],
            payload["id"],
            payload.get("is_playable"),
            Track.from_payload(tra) if (tra := payload.get("linked_from")) else None,
            Restrictions.from_payload(res)
            if (res := payload.get("restrictions"))
            else None,
            payload["name"],
            payload.get("popularity"),
            payload["preview_url"],
            payload["track_number"],
            payload["uri"],
            payload["is_local"],
        )
