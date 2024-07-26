import nox


@nox.session
def format(session: nox.Session) -> None:
    session.install(".[dev.ruff]")
    session.run("ruff", "check", "spotify", "--select", "I", "--fix")
    session.run("ruff", "format", "spotify")


@nox.session
def typing(session: nox.Session) -> None:
    session.install(".[dev.typecheck]")
    session.run("pyright", "spotify")


@nox.session
def docs_build(session: nox.Session) -> None:
    session.install(".[dev.docs]")
    session.run("mkdocs", "build")


@nox.session(default=False)
def docs_serve(session: nox.Session) -> None:
    session.install(".[dev.docs]")
    session.run("mkdocs", "serve")
