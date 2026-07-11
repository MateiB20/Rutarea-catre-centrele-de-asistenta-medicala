import sqlite3
import tracemalloc
from fastapi.testclient import TestClient

from database_manager import set_occupancy, get_occupancy
from main import app
import time
import csv
from main import hospitals

client = TestClient(app)

def reset_routes_table():
    conn = sqlite3.connect("routes.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM routeresult")
    cursor.execute("UPDATE hospital SET current_occupancy = 0")
    conn.commit()
    conn.close()

def test_get_route_status():
    reset_routes_table()
    with open("benchmark.csv", "w") as file:
        locations = ["Palatul Culturii, Iasi", "Piata Unirii, Iasi", "Targu Cucu, Iasi","Strada Palat, Iasi","Strada Tudor, Iasi"]
        writer = csv.writer(file)
        writer.writerow(["method","latency_seconds","memory_used_kb","duration_seconds"])
        for address in locations:
            tracemalloc.start()
            start_mem, peak_mem = tracemalloc.get_traced_memory()
            start = time.perf_counter()
            response = client.get(f"/route?address={address}&method=Astar")
            end = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            memory_used_kb = peak / 1024
            latency = end - start
            conn = sqlite3.connect('routes.db')
            cursor = conn.cursor()
            query = "SELECT * FROM routeresult ORDER BY id DESC LIMIT 1"
            cursor.execute(query)
            route = cursor.fetchone()
            writer.writerow(["Astar",latency, memory_used_kb, route[5]])
            assert response.status_code == 200
            reset_routes_table()
        for address in locations:
            tracemalloc.start()
            start_mem, peak_mem = tracemalloc.get_traced_memory()
            start = time.perf_counter()
            response = client.get(f"/route?address={address}&method=BestFirst")
            end = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            memory_used_kb = peak / 1024
            latency = end - start
            conn = sqlite3.connect('routes.db')
            cursor = conn.cursor()
            query = "SELECT * FROM routeresult ORDER BY id DESC LIMIT 1"
            cursor.execute(query)
            route = cursor.fetchone()
            writer.writerow(["BestFirst",latency,memory_used_kb, route[5]])
            assert response.status_code == 200
            reset_routes_table()

def test_route_valid_address_astar():
    response = client.get("/route?address=Palatul Culturii, Iasi&method=Astar")
    assert response.status_code == 200

def test_route_valid_address_best_first_search():
    response = client.get("/route?address=Palatul Culturii, Iasi&method=BestFirst")
    assert response.status_code == 200

def test_route_invalid_method():
    response = client.get("/route?address=Palatul Culturii, Iasi&method=Invalid")
    assert response.status_code == 422

def test_route_invalid_address_astar():
    response = client.get("/route?address=falseAdress&method=Astar")
    assert response.status_code == 400

def test_route_invalid_address_best_first_search():
    response = client.get("/route?address=falseAdress&method=BestFirst")
    assert response.status_code == 400

def test_get_route_status_multiple_astar():
    reset_routes_table()
    with open("benchmark_multiple.csv", "w") as file:
        location = "Palatul Culturii, Iasi"
        writer = csv.writer(file)
        writer.writerow(["method","latency_seconds","memory_used_kb","duration_seconds"])
        for _ in range(0,10):
            tracemalloc.start()
            start_mem, peak_mem = tracemalloc.get_traced_memory()
            start = time.perf_counter()
            response = client.get(f"/route?address={location}&method=Astar")
            end = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            memory_used_kb = peak / 1024
            latency = end - start
            conn = sqlite3.connect('routes.db')
            cursor = conn.cursor()
            query = "SELECT * FROM routeresult ORDER BY id DESC LIMIT 1"
            cursor.execute(query)
            route = cursor.fetchone()
            writer.writerow(["Astar",latency, memory_used_kb, route[5]])
            assert response.status_code == 200
    reset_routes_table()

def test_get_route_status_multiple_best_first_search():
    reset_routes_table()
    with open("benchmark_multiple_1.csv", "w") as file:
        location = "Palatul Culturii, Iasi"
        writer = csv.writer(file)
        writer.writerow(["method","latency_seconds","memory_used_kb","duration_seconds"])
        for _ in range(0,10):
            tracemalloc.start()
            start_mem, peak_mem = tracemalloc.get_traced_memory()
            start = time.perf_counter()
            response = client.get(f"/route?address={location}&method=BestFirst")
            end = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            memory_used_kb = peak / 1024
            latency = end - start
            conn = sqlite3.connect('routes.db')
            cursor = conn.cursor()
            query = "SELECT * FROM routeresult ORDER BY id DESC LIMIT 1"
            cursor.execute(query)
            route = cursor.fetchone()
            writer.writerow(["BestFirst",latency, memory_used_kb, route[5]])
            assert response.status_code == 200
    reset_routes_table()

def test_high_occupancy():
    location = "Strada Eternitate 1, Iasi"
    with open("benchmark_high_occupancy.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(["highly_occupied_hospital", "chosen_hospital", "duration_seconds"])
        for hosp in hospitals:
            old_occupancy=get_occupancy(hosp['name'])
            set_occupancy(hosp['name'], hosp['capacity']*0.95)
            response = client.get(f"/route?address={location}&method=Astar")
            set_occupancy(hosp['name'], old_occupancy)
            conn = sqlite3.connect('routes.db')
            conn = sqlite3.connect("routes.db", timeout=10)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    hospital.name,
                    routeresult.duration_s
                FROM routeresult
                JOIN hospital ON routeresult.hospital_id = hospital.id
                ORDER BY routeresult.id DESC
                LIMIT 1
            """)
            route = cursor.fetchone()
            writer.writerow([hosp['name'], route[0], route[1]])
            assert response.status_code == 200
            reset_routes_table()
