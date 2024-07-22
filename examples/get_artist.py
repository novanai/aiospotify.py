import asyncio
import spotify


async def main():
    auth = await spotify.ClientCredentialsFlow.build_from_access_token(
        "CLIENT_ID",
        "CLIENT_SECRET",
    )
    api = spotify.API(auth)

    artist = await api.get_artist("0e86yPdC41PGRkLp2Q1Bph")
    print(artist.name)

asyncio.run(main())
