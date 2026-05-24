from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, debts, events, friends, summary, users

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"pong": True}

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(friends.router)
app.include_router(events.router)
app.include_router(debts.router)
app.include_router(summary.router)
