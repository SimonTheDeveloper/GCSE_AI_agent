from pydantic import BaseModel

class Flight(BaseModel):
    flight_id: str
    source: str
    sink: str
    airline: str
    departure_dt: str
    arrival_dt: str
    number_of_stops: int
    emissions: int
    price: float
