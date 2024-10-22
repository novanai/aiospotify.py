# aiospotify.py

An asynchronous Python 3.10+ Spotify Web API wrapper.

* **GitHub:** <https://github.com/novanai/aiospotify.py>
* **Documentation:** <https://aiospotifypy.readthedocs.io/en/stable/>
* **Examples**: <https://github.com/novanai/aiospotify.py/tree/master/examples>

## Installation

```bash
pip install -U aiospotify.py
```

Or to install the latest development version:
```bash
pip install -U git+https://github.com/novanai/aiospotify.py
```

## Getting Started

```py
import asyncio
import spotify

async def main():
    # Setup an API client
    auth = await spotify.ClientCredentialsFlow.build_from_access_token(
        "CLIENT_ID",
        "CLIENT_SECRET",
    )
    api = spotify.API(auth)

    # Get details about a Spotify artist
    artist = await api.get_artist("0e86yPdC41PGRkLp2Q1Bph")
    print(artist.name)  # "Mother Mother"


asyncio.run(main())
```
