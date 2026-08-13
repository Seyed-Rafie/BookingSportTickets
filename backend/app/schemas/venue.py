from pydantic import BaseModel
from typing import Optional

class ProvinceSchema(BaseModel):
    province_id: int
    name: str

class CitySchema(BaseModel):
    city_id: int
    name: str
    province: ProvinceSchema

class VenueResponseSchema(BaseModel):
    venue_id: int
    name: str
    address: str
    capacity: int
    city: CitySchema