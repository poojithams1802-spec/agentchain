from pydantic import BaseModel, Field


class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    mode: str = Field(..., min_length=1)
    max_tests: int = Field(..., gt=0)
