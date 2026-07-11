import json
import datetime
import folium
import os
from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    FloatField,
    IntegerField,
    TextField,
    DateTimeField,
    ForeignKeyField
)

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "routes.db")
db = SqliteDatabase(db_path)


class Hospital(Model):
    name = CharField()
    lat = FloatField()
    lon = FloatField()
    capacity = IntegerField(default=0)
    current_occupancy = IntegerField(default=0)

    class Meta:
        database = db


class RouteResult(Model):
    created_at = DateTimeField(default=datetime.datetime.now)
    address_from = CharField()
    hospital = ForeignKeyField(Hospital, backref="routes")
    distance_m = FloatField()
    duration_s = FloatField()
    route_coords = TextField()

    class Meta:
        database = db


def normalize_coord(coord):
    a, b = coord

    if 46 <= a <= 48 and 26 <= b <= 29:
        return a, b

    if 26 <= a <= 29 and 46 <= b <= 48:
        return b, a

    return a, b


def get_active_routes():
    active_routes = []
    now = datetime.datetime.utcnow()

    for route in RouteResult.select().order_by(RouteResult.id.asc()):
        created_at = route.created_at
        duration = float(route.duration_s)
        elapsed = (now - created_at).total_seconds()

        print(
            f"id={route.id} | "
            f"address={route.address_from} | "
            f"created_at={created_at} | "
            f"now_utc={now} | "
            f"duration={duration} | "
            f"elapsed={elapsed} | "
            f"active={0 <= elapsed < duration}"
        )

        if 0 <= elapsed < duration:
            active_routes.append(route)

    return active_routes


def get_busy_coordinates():
    busy_coordinates = set()
    now = datetime.datetime.utcnow()

    for route in get_active_routes():
        duration = float(route.duration_s)
        elapsed = (now - route.created_at).total_seconds()

        if duration <= 0:
            continue

        if elapsed < 0:
            elapsed = 0

        if elapsed >= duration:
            continue

        coords = json.loads(route.route_coords)

        progress = elapsed / duration
        start_index = int(progress * len(coords))
        remaining_coords = coords[start_index:]

        for coord in remaining_coords:
            lat, lon = normalize_coord(coord)
            busy_coordinates.add((round(lat, 4), round(lon, 4)))

    return busy_coordinates


def generate_busy_points_html():
    busy_coordinates = get_busy_coordinates()

    print(f"Număr puncte active afișate: {len(busy_coordinates)}")

    m = folium.Map(
        location=[47.1585, 27.6014],
        zoom_start=13,
        tiles="CartoDB Positron"
    )

    for lat, lon in busy_coordinates:
        folium.CircleMarker(
            location=[lat, lon],
            radius=3,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.55,
            popup="Zonă aglomerată"
        ).add_to(m)

    m.save("busy_points_map.html")
    print("Harta a fost generată: busy_points_map.html")


if __name__ == "__main__":
    if db.is_closed():
        db.connect()

    generate_busy_points_html()

    if not db.is_closed():
        db.close()