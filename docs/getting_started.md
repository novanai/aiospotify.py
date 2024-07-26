## Authorization

There are 3 ways to authenticate with the Spotify Web API:

| Flow | Access User Resources | Requires Secret Key (Server-Side) |
|------|-----------------------|-----------------------------------|
| [Client Credentials](#client-credentials) | No | Yes |
| [Authorization Code](#authorization-code) | Yes | Yes |
| [Authorization Code with PKCE](#authorization-code-with-pkce) | Yes | No |

In the following examples, replace `"CLIENT_ID"` and `"CLIENT_SECRET"` with your [Spotify Application's](https://developer.spotify.com/dashboard) client ID and secret.

## Client Credentials

[`ClientCredentialsFlow`][spotify.oauth.ClientCredentialsFlow] provides access to all **non-user** resources.

```py
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
```

<br>

For the following two authorization code examples:

* [quart](https://pypi.org/project/Quart/) must be installed
* In the example redirect URI `"https://example.com/account"` replace `example.com` with your own domain. For developing locally, `http://localhost` is a valid redirect domain.
* The redirect URI must be added to your [Spotify Application](https://developer.spotify.com/dashboard)

## Authorization Code

[`AuthorizationCodeFlow`][spotify.oauth.AuthorizationCodeFlow] provides access to **all resources** (including user resources), and should be used when it is safe to store the client's secret key.

```py
import random
import secrets

from quart import Quart, redirect, request, session

import spotify
from spotify import Scope

app = Quart(__name__)
app.secret_key = "SECRET_KEY"


def generate_state() -> str:
    possible = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-~"
    state = [secrets.choice(possible) for _ in range(random.randint(43, 128))]
    return "".join(state)


@app.get("/")
async def index():
    return redirect("/login")


@app.get("/login")
async def login():
    session["state"] = generate_state()

    url = spotify.AuthorizationCodeFlow.build_url(
        client_id="CLIENT_ID",
        redirect_uri="https://example.com/account",
        state=session["state"],
        scopes=[Scope.USER_TOP_READ],
    )
    return redirect(url)


@app.get("/account")
async def account():
    state = request.args.get("state")
    error = request.args.get("error")
    code = request.args.get("code")

    if session.get("state") is None or state != session["state"] or error or not code:
        return redirect("/")

    session.pop("state")

    auth = await spotify.AuthorizationCodeFlow.build_from_access_token(
        code,
        "https://example.com/account",
        client_id="CLIENT_ID",
        client_secret="CLIENT_SECRET",
    )
    api = spotify.API(auth)
    top = await api.get_users_top_items(type=spotify.TopItemType.TRACKS)

    await api.session.close()

    return (
        "<ol>"
        + "\n".join(f"<li>{track.name} - {track.artists[0].name}</li>" for track in top.items)
        + "</ol>"
    )


app.run()
```

## Authorization Code with PKCE

[`AuthorizationCodeFlow` (with PKCE)][spotify.oauth.AuthorizationCodeFlow] provides access to **all resources** (including user resources), and should be used when it is **not** safe to store the client's secret key.

```py
import base64
import hashlib
import random
import secrets

from quart import Quart, redirect, request, session

import spotify
from spotify import Scope

app = Quart(__name__)
app.secret_key = "SECRET_KEY"


def generate_code() -> str:
    possible = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-~"
    code = [secrets.choice(possible) for _ in range(random.randint(43, 128))]
    return "".join(code)


def safe_sha256(text: str) -> str:
    _text = hashlib.sha256(text.encode("ascii"), usedforsecurity=True).digest()
    _text = base64.urlsafe_b64encode(_text).decode("ascii")
    _text = _text.replace("=", "").replace("+", "-").replace("/", "_")
    return _text


@app.get("/")
async def index():
    return redirect("/login")


@app.get("/login")
async def login():
    session["state"] = generate_code()
    session["verifier"] = generate_code()
    challenge = safe_sha256(session["verifier"])

    url = spotify.AuthorizationCodeFlow.build_url(
        client_id="CLIENT_ID",
        redirect_uri="https://example.com/account",
        state=session["state"],
        scopes=[Scope.USER_TOP_READ],
        code_challenge=challenge,
    )
    return redirect(url)


@app.get("/account")
async def account():
    state = request.args.get("state")
    error = request.args.get("error")
    code = request.args.get("code")

    if (
        session.get("state") is None
        or state != session["state"]
        or error
        or not code
        or not session.get("verifier")
    ):
        return redirect("/")
    
    session.pop("state")
    verifier = session.pop("verifier")

    auth = await spotify.AuthorizationCodeFlow.build_from_access_token(
        code,
        "https://example.com/account",
        client_id="CLIENT_ID",
        code_verifier=verifier,
    )
    api = spotify.API(auth)
    top = await api.get_users_top_items(type=spotify.TopItemType.TRACKS)

    await api.session.close()

    return (
        "<ol>"
        + "\n".join(f"<li>{track.name} - {track.artists[0].name}</li>" for track in top.items)
        + "</ol>"
    )


app.run()
```
