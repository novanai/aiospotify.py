import nox

# Dependencies must be set to an absolute version for this to work
project = nox.project.load_toml("pyproject.toml")["project"]

deps: dict[str, dict[str, str]] = {
    group: {dep.split("==")[0]: dep for dep in deps}
    for group, deps in project["optional-dependencies"].items()
}


@nox.session
def format(session: nox.Session) -> None:
    session.install(deps["dev"]["ruff"])
    session.run("ruff", "check", "spotify", "--select", "I", "--fix")
    session.run("ruff", "format", "spotify")


@nox.session
def typing(session: nox.Session) -> None:
    session.install(deps["dev"]["pyright"], *project["dependencies"])
    session.run("pyright", "spotify")


@nox.session
def docs_build(session: nox.Session) -> None:
    session.install(*deps["docs"].values())
    session.run("mkdocs", "build")


@nox.session
def docs_serve(session: nox.Session) -> None:
    session.install(*deps["docs"].values())
    session.run("mkdocs", "serve")
