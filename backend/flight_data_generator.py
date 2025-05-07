from typing import TypedDict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from random import randint, random
from pprint import pprint

AIRLINES = ["BRITISH AIRWAYS", "EASYJET", "WIZZ AIR"]

class Flight(TypedDict):
    source: str
    sink: str
    airline: str
    departure_dt: datetime
    arrival_dt: datetime
    number_of_stops: int
    emissions: int
    price: Decimal

def flight_data(source: str, sink: str, departure_date: date, return_date: date):
    flights: list[Flight] = []
    for airline in AIRLINES:
        for _ in range(randint(0, 4)):
            departure_dt = datetime.combine(departure_date, time(randint(0, 23), randint(0, 50)))
            arrival_dt = departure_dt + timedelta(minutes=randint(60, 240))
            price = random() * 500
            departure_flight: Flight = {
                "source": source,
                "sink": sink,
                "airline": airline,
                "departure_dt": departure_dt,
                "arrival_dt": arrival_dt,
                "number_of_stops": randint(0, 3),
                "emissions": int((arrival_dt - departure_dt).total_seconds() * 0.01),
                "price": Decimal(f"{price:.2f}"),
            }

            return_departure_dt = datetime.combine(return_date, time(randint(0, 23), randint(0, 59)))
            return_arrival_dt = return_departure_dt + timedelta(minutes=randint(60, 240))
            return_price = random() * 200
            return_flight: Flight = {
                "source": sink,
                "sink": source,
                "airline": airline,
                "departure_dt": return_departure_dt,
                "arrival_dt": return_arrival_dt,
                "number_of_stops": randint(0, 3),
                "emissions": int((return_arrival_dt - return_departure_dt).total_seconds() * 0.01),
                "price": Decimal(f"{return_price:.2f}"),
            }
            flights.append(departure_flight)
            flights.append(return_flight)
    return flights

if __name__ == "__main__":
    flights = flight_data(
        source="London",
        sink="Amsterdam",
        departure_date=date(2024, 10, 3),
        return_date=date(2024, 10, 10),
    )
    pprint(flights)