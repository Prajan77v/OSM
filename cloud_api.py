"""
OMS Sentinel — Production Cloud API Gateway
Entry point for Render / Cloud deployments. Imports from modular cloud package.
"""

from cloud.api.app import app

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("cloud_api:app", host="0.0.0.0", port=port, reload=False)
