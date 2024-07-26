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
    if not session.get("state"):
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

    if state != session.get("state") or error or not code:
        return redirect("/")

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
