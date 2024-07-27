from __future__ import annotations

import typing

import pydantic

from spotify import models

if typing.TYPE_CHECKING:
    from spotify import api



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

    @classmethod
    def from_payload(cls, data: bytes, api_class: api.API) -> typing.Self:
        obj = cls.model_validate_json(data)
        obj.paginator._api = api_class  # pyright: ignore[reportPrivateUsage]
        obj.paginator._item_type = models.Artist  # pyright: ignore[reportPrivateUsage]
        return obj


class Devices(pydantic.BaseModel):
    devices: list[models.Device]


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
