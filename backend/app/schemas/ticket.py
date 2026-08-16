from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TeamSchema(BaseModel):
    team_id: int
    name: str


class MatchSchema(BaseModel):
    match_id: int
    competition_name: str
    sport_type_name: str
    home_team: TeamSchema
    away_team: TeamSchema
    venue_name: str
    city_name: str
    match_datetime: datetime
    status: str


class TicketSummarySchema(BaseModel):
    ticket_id: int
    ticket_code: str
    category_name: str
    price: float
    remaining_capacity: int
    status: str
    match: MatchSchema

class CreateTicketRequest(BaseModel):
    match_id: int
    category_id: int
    total_capacity: int
    price: int

class FootballDetailsSchema(BaseModel):
    gate_number: Optional[str] = None
    has_parking: Optional[bool] = None
    vip_services: Optional[str] = None


class VolleyballDetailsSchema(BaseModel):
    entrance_gate: Optional[str] = None
    special_services: Optional[str] = None


class BasketballDetailsSchema(BaseModel):
    entrance_gate: Optional[str] = None
    vip_services: Optional[str] = None
    has_food_court: Optional[bool] = None


class TicketDetailSchema(TicketSummarySchema):
    facilities: List[str] = Field(default_factory=list)
    football_details: Optional[FootballDetailsSchema] = None
    volleyball_details: Optional[VolleyballDetailsSchema] = None
    basketball_details: Optional[BasketballDetailsSchema] = None