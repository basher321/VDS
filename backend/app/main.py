"""VDS — VAT Deduction at Source (Mushak-6.6) backend entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .api import auth, dashboard, organization, imports, certificates

settings = get_settings()
app = FastAPI(title="VDS — VAT Deduction at Source", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(organization.router)
app.include_router(imports.router)
app.include_router(certificates.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "vds"}
