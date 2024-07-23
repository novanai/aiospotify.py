from __future__ import annotations

import enum
import typing

__all__: typing.Sequence[str] = (
    "AlbumGroup",
    "AlbumType",
    "ContextType",
    "CopyrightType",
    "PlayingType",
    "Reason",
    "RecommendationSeedType",
    "ReleaseDatePrecision",
    "RepeatState",
    "Scope",
    "SearchType",
    "StatusCode",
    "SubscriptionLevel",
    "TimeRange",
    "TopItemType",
    "TrackMode",
    "UserType",
)


@enum.unique
class AlbumGroup(enum.Enum):
    """The relationship between the artist and album."""

    ALBUM = "album"
    """ALbum by the artist."""
    SINGLE = "single"
    """Single by the artist."""
    COMPILATION = "compilation"
    """Compilation by the artist."""
    APPEARS_ON = "appears_on"
    """Artist is featured in the album/single/compilation."""


@enum.unique
class AlbumType(enum.Enum):
    """The type of an album."""

    ALBUM = "album"
    """An album."""
    SINGLE = "single"
    """A single."""
    COMPILATION = "compilation"
    """A compilation."""
    EP = "ep"
    """An EP.
    
    !!! note
        This value is not documented, but is returned frequently in the API so I have included it
        anyway.
    """


@enum.unique
class ContextType(enum.Enum):
    """A context's item type."""

    ARTIST = "artist"
    """An artist."""
    PLAYLIST = "playlist"
    """A playlist."""
    ALBUM = "album"
    """An album."""
    SHOW = "show"
    """A show."""


@enum.unique
class CopyrightType(enum.Enum):
    """The type of copyright."""

    COPYRIGHT = "C"
    """The copyright."""
    PERFORMANCE_COPYRIGHT = "P"
    """The sound recording (performance) copyright."""


@enum.unique
class PlayingType(enum.Enum):
    """The type of the currently playing item."""

    TRACK = "track"
    """A track."""
    EPISODE = "episode"
    """An episode."""
    AD = "ad"
    """An ad."""
    UNKNOWN = "unknown"
    """Unknown."""


@enum.unique
class Reason(enum.Enum):
    """Restriction reason."""

    MARKET = "market"
    """Content not available in given market."""
    PRODUCT = "product"
    """Content not available for user's subscription type."""
    EXPLICIT = "explicit"
    """User's account is set to not play explicit content."""
    PAYMENT_REQUIRED = "payment_required"
    """Payment is required to play the content item."""
    UNKNOWN = "unknown"
    """The restriction reason is unknown."""


@enum.unique
class RecommendationSeedType(enum.Enum):
    """The type of a recommendation seed."""

    ARTIST = "artist"
    """An artist."""
    TRACK = "track"
    """A track."""
    GENRE = "genre"
    """A genre."""


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
class RepeatState(enum.Enum):
    """playback repeat state."""

    OFF = "off"
    """No repeat."""
    TRACK = "track"
    """Repeating the track."""
    CONTEXT = "context"
    """Repeating the context."""


@enum.unique
class Scope(enum.Enum):
    """Authorization Scopes."""

    UGC_IMAGE_UPLOAD = "ugc-image-upload"
    """Write access to user-provided images."""
    USER_READ_PLAYBACK_STATE = "user-read-playback-state"
    """Read access to a user's player state."""
    USER_MODIFY_PLAYBACK_STATE = "user-modify-playback-state"
    """Write access to a user's playback state."""
    USER_READ_CURRENTLY_PLAYING = "user-read-currently-playing"
    """Read access to a user's currently playing content."""
    APP_REMOTE_CONTROL = "app-remote-control"
    """Remote control playback of Spotify. This scope is currently available to Spotify iOS and
    Android SDKs.
    """
    STREAMING = "streaming"
    """Control playback of a Spotify track. This scope is currently available to the Web Playback
    SDK. The user must have a Spotify Premium account.
    """
    PLAYLIST_READ_PRIVATE = "playlist-read-private"
    """Read access to user's private playlists."""
    PLAYLIST_READ_COLLABORATIVE = "playlist-read-collaborative"
    """Include collaborative playlists when requesting a user's playlists."""
    PLAYLIST_MODIFY_PRIVATE = "playlist-modify-private"
    """Write access to a user's private playlists."""
    PLAYLIST_MODIFY_PUBLIC = "playlist-modify-public"
    """Write access to a user's public playlists."""
    USER_FOLLOW_MODIFY = "user-follow-modify"
    """Write/delete access to the list of artists and other users that the user follows."""
    USER_FOLLOW_READ = "user-follow-read"
    """Read access to the list of artists and other users that the user follows."""
    USER_READ_PLAYBACK_POSITION = "user-read-playback-position"
    """Read access to a user's playback position in a content."""
    USER_TOP_READ = "user-top-read"
    """Read access to a user's top artists and tracks."""
    USER_READ_RECENTLY_PLAYED = "user-read-recently-played"
    """Read access to a user's recently played tracks."""
    USER_LIBRARY_MODIFY = "user-library-modify"
    """Write/delete access to a user's "Your Music" library."""
    USER_LIBRARY_READ = "user-library-read"
    """Read access to a user's library."""
    USER_READ_EMAIL = "user-read-email"
    """Read access to user's email address."""
    USER_READ_PRIVATE = "user-read-private"
    """Read access to user's subscription details (type of user account)."""
    USER_SOA_LINK = "user-soa-link"
    """Link a partner user account to a Spotify user account."""
    USER_SOA_UNLINK = "user-soa-unlink"
    """Unlink a partner user account from a Spotify account."""
    USER_MANAGE_ENTITLEMENTS = "user-manage-entitlements"
    """Modify entitlements for linked users."""
    USER_MANAGE_PARTNER = "user-manage-partner"
    """Update partner information."""
    USER_CREATE_PARTNER = "user-create-partner"
    """Create new partners, platform partners only."""


@enum.unique
class SearchType(enum.Enum):
    """Search result type."""

    ALBUM = "album"
    """An album."""
    ARTIST = "artist"
    """An artist."""
    PLAYLIST = "playlist"
    """A playlist."""
    TRACK = "track"
    """A track."""
    SHOW = "show"
    """A show."""
    EPISODE = "episode"
    """AN episode."""
    AUDIOBOOK = "audiobook"
    """An audiobook."""


@enum.unique
class StatusCode(enum.Enum):
    """Audio analysis metadata status code."""

    SUCCESSFUL = 0
    """Analysis was successful."""
    ERRORS = 1
    """Analysis errored and was unsuccessful."""


@enum.unique
class SubscriptionLevel(enum.Enum):
    """A user's Spotify subscription level."""

    PREMIUM = "premium"
    """Premium subscription."""
    FREE = "free"
    """Free subscription."""


@enum.unique
class TimeRange(enum.Enum):
    """Time range."""

    SHORT_TERM = "short_term"
    """Approximately 4 weeks."""
    MEDIUM_TERM = "medium_term"
    """Approximately 6 months."""
    LONG_TERM = "long_term"
    """Approximately 1 year."""


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
    UNKNOWN = -1
    """Mode is unknown."""


@enum.unique
class UserType(enum.StrEnum):
    """Type of a user."""

    ARTIST = "artist"
    """An artist."""
    USER = "user"
    """A user."""
