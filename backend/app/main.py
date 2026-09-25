from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    activity_logs,
    auth,
    dashboard,
    departments,
    goals,
    imports,
    mkt_timeline,
    partners,
    projects,
    search,
    speakers,
    target_lists,
    tasks,
    users,
    invites,
)

app = FastAPI(title="SHIFT API", version="0.1.0")

# Adjust allow_origins to the real frontend URL(s) before deploying past local dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(invites.router)   
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(departments.router)
app.include_router(partners.router)
app.include_router(imports.router)
app.include_router(target_lists.router)
app.include_router(speakers.router)
app.include_router(tasks.router)
app.include_router(goals.router)
app.include_router(mkt_timeline.router)
app.include_router(dashboard.router)
app.include_router(activity_logs.router)
app.include_router(search.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
