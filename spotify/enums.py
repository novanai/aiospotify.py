from __future__ import annotations

import enum


@enum.unique
class AlbumGroup(enum.Enum):
    """The relationship between the artist and album."""

    ALBUM = "album"
    SINGLE = "single"
    COMPILATION = "compilation"
    APPEARS_ON = "appears_on"


@enum.unique
class AlbumType(enum.Enum):
    """The type of album."""

    ALBUM = "album"
    """An album."""
    SINGLE = "single"
    """A single."""
    COMPILATION = "compilation"
    """A compilation."""


@enum.unique
class CopyrightType(enum.Enum):
    """The type of copyright."""

    COPYRIGHT = "C"
    """The copyright."""
    PERFORMANCE_COPYRIGHT = "P"
    """The sound recording (performance) copyright."""


@enum.unique
class ReleaseDatePrecision(enum.Enum):
    """Precision of a release date."""

    YEAR = "year"
    """Precise to the release year."""
    MONTH = "month"
    """Precise to the release month."""
    DAY = "day"
    """Precise to the release day."""


@enum.unique
class Reason(enum.Enum):
    """Restriction reason."""

    MARKET = "market"
    """Content not available in given market."""
    PRODUCT = "product"
    """Content not available for user's subscription type."""
    EXPLICIT = "explicit"
    """User's account is set to not play explicit content."""
    UNKNOWN = "unknown"
    """The restriction reason is unknown."""

    @classmethod
    def from_payload(cls, text: str) -> Reason:
        if text in {"market", "product", "explicit"}:
            return cls(text)
        else:
            return cls("unknown")


@enum.unique
class Scope(enum.Enum):
    """Authorization Scopes."""

    UGC_IMAGE_UPLOAD = "ugc-image-upload"
    """Write access to user-provided images."""
    USER_READ_PLAYBACK_STATE = "user-read-playback-state"
    """Read access to a user's player state."""
    APP_REMOTE_CONTROL = "app-remote-control"
    """Remote control playback of Spotify. This scope is currently available to Spotify iOS and
    Android SDKs."""
    USER_MODIFY_PLAYBACK_STATE = "user-modify-playback-state"
    """Write access to a user's playback state"""
    PLAYLIST_READ_PRIVATE = "playlist-read-private"
    """Read access to user's private playlists."""
    USER_FOLLOW_MODIFY = "user-follow-modify"
    """Write/delete access to the list of artists and other users that the user follows."""
    PLAYLIST_READ_COLLABORATIVE = "playlist-read-collaborative"
    """Include collaborative playlists when requesting a user's playlists."""
    USER_FOLLOW_READ = "user-follow-read"
    """Read access to the list of artists and other users that the user follows."""
    USER_READ_CURRENTLY_PLAYING = "user-read-currently-playing"
    """Read access to a user's currently playing content."""
    USER_READ_PLAYBACK_POSITION = "user-read-playback-position"
    """Read access to a user's playback position in a content."""
    USER_LIBRARY_MODIFY = "user-library-modify"
    """Write/delete access to a user's library."""
    PLAYLIST_MODIFY_PRIVATE = "playlist-modify-private"
    """Write access to a user's private playlists."""
    PLAYLIST_MODIFY_PUBLIC = "playlist-modify-public"
    """Write access to a user's public playlists."""
    USER_READ_EMAIL = "user-read-email"
    """Read access to user's email address."""
    USER_TOP_READ = "user-top-read"
    """Read access to a user's top artists and tracks."""
    STREAMING = "streaming"
    """Control playback of a Spotify track. This scope is currently available to the Web Playback SDK.
    The user must have a Spotify Premium account."""
    USER_READ_RECENTLY_PLAYED = "user-read-recently-played"
    """Read access to a user's recently played tracks."""
    USER_READ_PRIVATE = "user-read-private"
    """Read access to user's subscription details (type of user account)."""
    USER_LIBRARY_READ = "user-library-read"
    """Read access to a user's library."""


@enum.unique
class TimeRange(enum.Enum):
    """Time range."""

    SHORT_TERM = "short_term"
    """Approximately 4 weeks."""
    MEDIUM_TERM = "medium_term"
    """Approximately 6 months."""
    LONG_TERM = "long_term"
    """Several years."""


@enum.unique
class TopItemType(enum.Enum):
    """Type of top item."""

    ARTISTS = "artists"
    """Top artists."""
    TRACKS = "tracks"
    """Top tracks."""


@enum.unique
class TrackMode(enum.IntEnum):
    """Modality of a track."""

    MINOR = 0
    """Minor mode."""
    MAJOR = 1
    """Major mode."""
