from __future__ import annotations

import pydantic
from spotify import models
# NOTE: check if it's necessary to import all of these
from spotify.models import (
    ExternalURLs,
    Image,
    Restrictions,
    SimpleArtist,
    Paginator,
    SimpleTrack,
    Copyright,
    ExternalIDs,
    Author,
    Narrator,
    SimpleChapter,
    ResumePoint,
    SimpleShow,
)
import typing

class _Albums(pydantic.BaseModel):
    albums: list[models.Album]

class _SimpleAlbumPaginator(pydantic.BaseModel):
    paginator: models.Paginator[models.SimpleAlbum] = pydantic.Field(alias="albums")

class _Artists(pydantic.BaseModel):
    artists: list[models.Artist]

class _Tracks(pydantic.BaseModel):
    tracks: list[models.TrackWithSimpleArtist]

class _Audiobooks(pydantic.BaseModel):
    audiobooks: list[models.Audiobook]

class _CategoryPaginator(pydantic.BaseModel):
    paginator: models.Paginator[models.Category] = pydantic.Field(alias="categories")

class _Chapters(pydantic.BaseModel):
    chapters: list[models.Chapter]

class _Episodes(pydantic.BaseModel):
    episodes: list[models.Episode]

class _AvailableGenreSeeds(pydantic.BaseModel):
    genres: list[str]

class _AvailableMarkets(pydantic.BaseModel):
    markets: list[str]

class _SnapshotID(pydantic.BaseModel):
    snapshot_id: str

class _Shows(pydantic.BaseModel):
    shows: list[models.SimpleShow]

class _AudioFeatures(pydantic.BaseModel):
    audio_features: list[models.AudioFeatures]

class _ArtistsPaginator(pydantic.BaseModel):
    paginator: models.CursorPaginator[models.Artist] = pydantic.Field(alias="artists")

class _Devices(pydantic.BaseModel):
    devices: list[models.Device]