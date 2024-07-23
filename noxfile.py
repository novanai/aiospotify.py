import nox


@nox.session
def format(session: nox.Session) -> None:
    session.install("ruff==0.5.4")
    session.run("ruff", "check", "spotify", "--select", "I", "--fix")
    session.run("ruff", "format", "spotify")


@nox.session
def typing(session: nox.Session) -> None:
    session.install("pyright==1.1.372", "-r", "requirements.txt")
    session.run("pyright", "spotify")

@nox.session
def docs(session: nox.Session) -> None:
    session.install("-r", "requirements_docs.txt")
    session.run("mkdocs", "build")
