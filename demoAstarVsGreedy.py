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

def test_get_route_status_multiple_astar():
    reset_routes_table()
    with open("benchmark_multiple.csv", "w") as file:
        location = "Palatul Culturii, Iasi"
        writer = csv.writer(file)
        writer.writerow(["method","latency_seconds","memory_used_kb","duration_seconds"])
        for _ in range(0,5):
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
        for _ in range(0,5):
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
