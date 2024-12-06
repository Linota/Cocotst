from loguru import logger
from richuru import install
from typer import Typer

install()


app = Typer()


@app.command()
def version():
    logger.info("Cocotst CLI\nVersion 0.0.4")


if __name__ == "__main__":
    app()
