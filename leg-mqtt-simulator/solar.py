"""Solar PV production model for Basel, Switzerland in July."""

import math
import random
from datetime import datetime

# Basel coordinates
LATITUDE = 47.56
LONGITUDE = 7.59

# July average daily insolation for Basel: ~5.5 kWh/m²/day
# Peak sun hours: ~06:00 to 20:00 (14 hours daylight)
# Solar noon: ~13:30 (due to timezone + DST)

def get_pv_production_kw(pv_kwp: float, dt: datetime = None) -> float:
    """
    Calculate PV production for given system size and time.
    
    Args:
        pv_kwp: PV system peak power in kWp
        dt: datetime (defaults to now)
    
    Returns:
        Current production in kW
    """
    if pv_kwp <= 0:
        return 0.0
    
    if dt is None:
        dt = datetime.now()
    
    hour = dt.hour + dt.minute / 60.0
    
    # No production at night (before 5:30 or after 21:00)
    if hour < 5.5 or hour > 21.0:
        return 0.0
    
    # Solar production curve (simplified sine model)
    # Peak at 13:00 (solar noon for Basel in summer with DST)
    solar_noon = 13.0
    day_length = 15.5  # hours of daylight in July
    
    # Normalized position in day (-1 to 1, 0 at solar noon)
    position = (hour - solar_noon) / (day_length / 2)
    
    if abs(position) > 1:
        return 0.0
    
    # Cosine curve for solar elevation effect
    # cos(position * pi/2) gives smooth curve peaking at noon
    elevation_factor = math.cos(position * math.pi / 2)
    
    # Typical July clear-sky efficiency: ~85% of peak
    # Account for panel temperature, inverter losses, etc.
    system_efficiency = 0.85
    
    # Cloud variation: random ±20%
    cloud_factor = 1.0 + random.uniform(-0.2, 0.2)
    
    # Calculate production
    production = pv_kwp * elevation_factor * system_efficiency * cloud_factor
    
    # Ensure non-negative
    return max(0.0, production)


def get_daily_production_kwh(pv_kwp: float) -> float:
    """
    Estimate daily production for July in Basel.
    
    Typical: 4-6 kWh per kWp per day in July
    """
    return pv_kwp * random.uniform(4.5, 5.5)


if __name__ == "__main__":
    # Test the model
    from datetime import datetime
    
    print("PV Production Test (10 kWp system, July day):")
    print("-" * 40)
    
    for hour in range(5, 22):
        dt = datetime(2026, 7, 15, hour, 0)
        prod = get_pv_production_kw(10.0, dt)
        bar = "█" * int(prod)
        print(f"{hour:02d}:00  {prod:5.2f} kW  {bar}")
