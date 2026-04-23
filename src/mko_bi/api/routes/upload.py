from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends
from typing import Optional
import tempfile
import os
from pathlib import Path

from mko_bi.data.loaders.loader import load_csv
from mko_bi.data.processing.base import DataPipeline
from mko_bi.services.dashboard_service import list_dashboards

router = APIRouter(prefix="/upload", tags=["upload"])


class UploadResponse(BaseModel):
    message: str
    records_processed: int


@router.post("", status_code=status.HTTP_200_OK)
async def upload_csv(
    file: UploadFile = File(...),
    user_id: int = 1,
) -> UploadResponse:
    """Upload and process a CSV file.

    Args:
        file: CSV file to upload (must be .csv.gz)
        user_id: Current user ID

    Returns:
        Upload response with processing results

    Raises:
        HTTPException: 400 if file is invalid or processing fails
    """
    # Validate file type
    if not file.filename.endswith(".csv.gz"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv.gz files are allowed",
        )

    # Save to temporary file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv.gz") as tmp:
            tmp_path = tmp.name
            content = await file.read()
            tmp.write(content)

        # Process the file
        pipeline = DataPipeline()
        df = load_csv(tmp_path)

        # Get available dashboards for filtering
        dashboards = list_dashboards(user_id)

        # Process for each dashboard
        total_records = 0
        for dashboard in dashboards:
            # Apply transformations
            transformed_df = pipeline.transform(df, dashboard.config)

            # Aggregate
            aggregated_df = pipeline.aggregate(transformed_df, dashboard.config)

            # Save to database
            from mko_bi.data.storage.manager import save_aggregates

            save_aggregates(dashboard.id, aggregated_df)

            total_records += len(aggregated_df)

        # Clean up temp file
        os.unlink(tmp_path)

        return UploadResponse(
            message="File processed successfully",
            records_processed=total_records,
        )

    except Exception as e:
        # Clean up temp file on error
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File processing failed: {str(e)}",
        )
