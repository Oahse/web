import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import uuid4

from core.database import get_db
from core.security_config import get_security_validator, SecurityValidator
from core.dependencies import require_admin_or_supplier # Corrected import for require_admin_or_supplier
from models.user import User # For current_user type hint
from core.config import settings # For server_host and UPLOAD_DIR (if needed)

router = APIRouter(prefix="/api/v1/files", tags=["Files"])

# Define upload directory (make sure it exists)
# Using settings.UPLOAD_DIR if defined, otherwise default to "static/uploads"
# This path is relative to the backend's working directory
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "static/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin_or_supplier),
    db: AsyncSession = Depends(get_db), # Required by get_security_validator
    validator: SecurityValidator = Depends(get_security_validator)
):
    """
    Uploads a file to the server, performing security validation.
    Accessible by Admin or Supplier roles.
    """
    try:
        # Perform file validation
        # file.filename and file.size are available from UploadFile
        validation_result = await validator.validate_file_upload(file.filename, file.size)
        if not validation_result["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result["errors"][0] if validation_result["errors"] else "File validation failed."
            )

        # Generate a unique filename to prevent overwrites and security issues
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        # Save the file locally
        with file_path.open("wb") as buffer:
            # Read file in chunks to prevent large files from exhausting memory
            while contents := await file.read(1024 * 1024): # Read in 1MB chunks
                buffer.write(contents)

        # Construct a URL for the uploaded file
        # This assumes your FastAPI app serves static files from a "static" directory
        file_url = f"{settings.server_host}/static/uploads/{unique_filename}"

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "File uploaded successfully",
                "filename": unique_filename,
                "file_url": file_url,
                "file_size": file.size,
                "content_type": file.content_type,
            }
        )
    except HTTPException:
        raise # Re-raise FastAPI HTTPExceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {e}"
        )

# Note: Serving static files usually configured in main.py
# Example in main.py:
# from fastapi.staticfiles import StaticFiles
# app.mount("/static", StaticFiles(directory="static"), name="static")
