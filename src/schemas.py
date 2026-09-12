from pydantic import BaseModel, Field


class HousingInput(BaseModel):
    typology: str
    municipality: str
    land_area_sqm: float = Field(ge=0)
    living_area_sqm: float = Field(gt=0)
    number_rooms: int = Field(gt=0)
    latitude: float = Field(ge=55, le=69.1)
    longitude: float = Field(ge=10.5, le=24.2)