"""An asynchronous Python 3.10+ Spotify Web API wrapper."""

from spotify import utils
from spotify.enums import *
from spotify.errors import *
from spotify.models import *
from spotify.oauth import *
from spotify.rest import *
from spotify.types import *

__version__ = "1.0.0"

BASE_URL = "https://api.spotify.com/v1"
