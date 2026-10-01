from pydantic import BaseModel, Field


class RatingCreate(BaseModel):
    """
    Request body for POST /courses/{course_id}/ratings.
    """
    # Upper bound matches the INTEGER (int4) column; larger values would fail in Postgres with a 500
    user_id: int = Field(..., gt=0, le=2_147_483_647, strict=True)
    rating: int = Field(..., ge=1, le=5, strict=True)
