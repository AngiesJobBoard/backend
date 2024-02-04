import requests
from ajb.config.settings import SETTINGS


def get_lat_long_from_address(address: str) -> tuple[float, float]:
    response = requests.get(
        url=f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={SETTINGS.GOOGLE_API_KEY}",
        timeout=30,
    )
    resp_json_payload = response.json()["results"][0]["geometry"]["location"]
    return round(resp_json_payload["lat"], 6), round(resp_json_payload["lng"], 6)
