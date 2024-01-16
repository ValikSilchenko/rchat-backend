import uvicorn
from fastapi import FastAPI


app = FastAPI()


if __name__ == "__main__":
    uvicorn.run(
        app="rchat.app:app",
        reload=True,
        port=8000,
        host="0.0.0.0",
        access_log=False
    )
