import uvicorn

from settings import settings
from api import app


def main():
    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)


if __name__ == "__main__":
    main()
