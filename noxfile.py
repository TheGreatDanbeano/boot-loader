import nox


# ============================================
#                    lint
# ============================================
@nox.session
def lint(session: nox.Session) -> None:
    """
    Runs the code linting suite.
    """
    session.install("poetry")
    session.run("poetry", "install", "--only", "dev")
    session.run("poetry", "run", "black", "./bootloader")
    session.run("poetry", "run", "pylint", "./bootloader")
    session.run("poetry", "run", "mypy", "./bootloader")
