from __future__ import annotations

import pydantic

from spotify import models


class Albums(pydantic.BaseModel):
    albums: list[models.Album]


class SimpleAlbumPaginator(pydantic.BaseModel):
    paginator: models.Paginator[models.SimpleAlbum] = pydantic.Field(alias="albums")


class Artists(pydantic.BaseModel):
    artists: list[models.Artist]


class Tracks(pydantic.BaseModel):
    tracks: list[models.TrackWithSimpleArtist]


class Audiobooks(pydantic.BaseModel):
    audiobooks: list[models.Audiobook]


class CategoryPaginator(pydantic.BaseModel):
    paginator: models.Paginator[models.Category] = pydantic.Field(alias="categories")


class Chapters(pydantic.BaseModel):
    chapters: list[models.Chapter]


class Episodes(pydantic.BaseModel):
    episodes: list[models.Episode]


class AvailableGenreSeeds(pydantic.BaseModel):
    genres: list[str]


class AvailableMarkets(pydantic.BaseModel):
    markets: list[str]


class SnapshotID(pydantic.BaseModel):
    snapshot_id: str


class Shows(pydantic.BaseModel):
    shows: list[models.SimpleShow]


class AudioFeatures(pydantic.BaseModel):
    audio_features: list[models.AudioFeatures]


class ArtistsPaginator(pydantic.BaseModel):
    paginator: models.CursorPaginator[models.Artist] = pydantic.Field(alias="artists")


class Devices(pydantic.BaseModel):
    devices: list[models.Device]
