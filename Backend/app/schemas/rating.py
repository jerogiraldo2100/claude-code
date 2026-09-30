from pydantic import BaseModel, Field


class RatingCreate(BaseModel):
    """
    Request body for POST /courses/{course_id}/ratings.
    """
    user_id: int = Field(..., gt=0, strict=True)
    rating: int = Field(..., ge=1, le=5, strict=True)
