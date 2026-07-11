import datetime
import json
import os
from peewee import SqliteDatabase, Model, CharField, FloatField, IntegerField, TextField, DateTimeField, ForeignKeyField
from error_manager import DatabaseError
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
    hospital = ForeignKeyField(Hospital, backref='routes')
    distance_m = FloatField()
    duration_s = FloatField()
    route_coords = TextField()
    class Meta:
        database = db

def initialize_db():
    try:
        db.connect()
        db.create_tables([Hospital, RouteResult], safe=True)
    except Exception as e:
        raise DatabaseError("Nu s-a putut inițializa baza de date", errors=str(e))

def save_route_result(address_from, hospital_name, distance_m, duration_s, route_coords):
    try:
        hospital_obj = Hospital.get(Hospital.name == hospital_name)
        if hospital_obj.current_occupancy < hospital_obj.capacity:
            hospital_obj.current_occupancy +=1
            hospital_obj.save()
        else:
            raise DatabaseError("Eroare la salvarea rutei - spital plin", errors=str(hospital_obj.current_occupancy))
        RouteResult.create(
            address_from=address_from,
            hospital=hospital_obj.id,
            distance_m=distance_m,
            duration_s=duration_s,
            route_coords=str(route_coords)
        )
        print(f"Rută salvată pentru {hospital_name}")
    except Exception as e:
        raise DatabaseError("Eroare la salvarea rutei", errors=str(e))

def get_active_routes():
    all_routes = RouteResult.select()
    active_routes = []
    now = datetime.datetime.now()
    for route in all_routes:
        arrival_time = route.created_at + datetime.timedelta(seconds=route.duration_s)
        if now < arrival_time:
            active_routes.append(route)
    return active_routes

def get_busy_coordinates():
    busy_coordinates = set()
    active_routes = get_active_routes()
    now = datetime.datetime.now()
    for route in active_routes:
        time_on_road = (now - route.created_at).total_seconds()
        duration = route.duration_s
        if time_on_road >= duration:
            continue
        coords_str = route.route_coords
        coords_list = json.loads(coords_str)
        aprox_progress = max(0, time_on_road / duration)
        start_index = int(aprox_progress * len(coords_list))
        remaining_coords = coords_list[start_index:]
        for coords_lon,  coords_lat in remaining_coords:
            busy_coordinates.add((round(coords_lon, 4), (round(coords_lat, 4))))
    return busy_coordinates

def add_or_get_hospital(name, lat, lon, capacity):
    Hospital.get_or_create(
        name=name,
        defaults={'lat': lat, 'lon': lon, 'capacity': capacity}
    )


def get_occupancy(name):
    try:
        hospital = Hospital.get(Hospital.name == name)
        if hospital.capacity == 0:
            return 0
        return hospital.current_occupancy / hospital.capacity
    except Hospital.DoesNotExist:
        return 0

def set_occupancy(name, occupancy):
    try:
        hospital_obj = Hospital.get(Hospital.name == name)
        if occupancy < hospital_obj.capacity:
            hospital_obj.current_occupancy = occupancy
            hospital_obj.save()
        else:
            raise DatabaseError("Eroare la salvarea rutei - spital plin", errors=str(hospital_obj.current_occupancy))
    except Exception as e:
        raise DatabaseError("Eroare la salvarea rutei", errors=str(e))


