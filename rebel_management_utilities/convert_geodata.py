import json
from geopy.geocoders import Nominatim, options
from geopy.distance import geodesic
from geopy.extra.rate_limiter import RateLimiter


def get_coordinates(data):
    """
        Converts some geodata (can be any format) to its coordinates.
    """
    options.default_timeout = None
    geolocator = Nominatim(user_agent="NL postcode mapping.")
    geocode = RateLimiter(geolocator.geocode, error_wait_seconds=300)
    location = geocode(f"{data}, Nederland")
    try:
        coordinates = (location.latitude, location.longitude)
        return coordinates
    except AttributeError:
        # invalid postcode if no coordinates are found
        print(f'Coordinates not found: {data}')
        raise ValueError(data)


def converter(from_data_type, to_data_type, data):
    """
        Converter geodata between the following types

            "postcode",
            "municipality",
            "town",
            "province",
            "region",

        Example:
        - To get the municipality corresponding to the postcode 1098AB, you
          would call: "convert("postcode", "municipality", "1098AB")".
    """
    with open('geodata.json') as f:
        geodata = json.load(f)

        data_types_index = {
            'postcode': 0,
            'municipality': 1,
            'town': 2,
            'province': 3,
            'region': 4,
        }

        try:
            for row in geodata:
                if row[data_types_index[from_data_type]] in data:
                    return row[data_types_index[to_data_type]]
        except KeyError:
            raise ValueError(f'from_data_type and to_data_type must have '
                             f'one of the following values: {", ".join(data_types_index.keys())}')
