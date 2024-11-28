from typer import Typer
from richuru import install
from loguru import logger

install()


app = Typer()


@app.command()
def version():
    logger.info("Cocotst CLI\nVersion 0.0.4")


if __name__ == "__main__":
    app()
