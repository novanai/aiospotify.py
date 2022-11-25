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
