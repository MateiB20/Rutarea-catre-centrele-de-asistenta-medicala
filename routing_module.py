import os
import json
import requests

from database_manager import save_route_result, get_busy_coordinates, get_occupancy
from map_visualizer import MapVisualizer
from Astar import AstarAlgorithm, Problem as AstarProblem
from Greedy import GreedyAlgorithm, Problem as GreedyProblem
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()

mapVisualizer = MapVisualizer("iasi_routes.html")


class RoutingModule:
    def __init__(self, method):
        self.method = method

    def route(self, hospitals, address, start_lon, start_lat):
        if self.method == "Astar":
            solver = AstarAlgorithm()
            problem_class = AstarProblem
        elif self.method == "BestFirst":
            solver = GreedyAlgorithm()
            problem_class = GreedyProblem
        else:
            return HTMLResponse("Nu s-a putut găsi o metodă validă.", status_code=422)

        mapbox_token = os.getenv("MAPBOX_TOKEN")

        if not mapbox_token:
            return HTMLResponse("Token-ul Mapbox nu este configurat.", status_code=500)

        all_routes_data = []
        profiles = ["mapbox/driving-traffic", "mapbox/driving"]
        occupancy = {}

        for hosp in hospitals:
            occupancy[hosp["name"]] = get_occupancy(hosp["name"])

            for profile in profiles:
                mapbox_url = (
                    f"https://api.mapbox.com/directions/v5/"
                    f"{profile}/{start_lon},{start_lat};{hosp['lon']},{hosp['lat']}"
                )

                params = {
                    "geometries": "geojson",
                    "overview": "full",
                    "alternatives": "true",
                    "access_token": mapbox_token
                }

                try:
                    response = requests.get(mapbox_url, params=params, timeout=10)
                    data = response.json()
                except Exception:
                    continue

                if "routes" not in data:
                    continue

                for route_option in data["routes"]:
                    geometry = route_option.get("geometry", {})
                    coordinates = geometry.get("coordinates", [])

                    if len(coordinates) < 2:
                        continue

                    coords = [[coord[1], coord[0]] for coord in coordinates]

                    all_routes_data.append({
                        "coords": coords,
                        "start": coords[0],
                        "goal": tuple([round(coords[-1][0], 4), round(coords[-1][1], 4)]),
                        "name": hosp["name"],
                        "duration": route_option.get("duration", 0),
                        "profile": profile
                    })

        if not all_routes_data:
            return HTMLResponse("Nu s-au putut obține rute candidate.", status_code=404)

        local_graph = {}

        for route_info in all_routes_data:
            path = route_info["coords"]

            for index in range(len(path) - 1):
                current_node = tuple([round(path[index][0], 4), round(path[index][1], 4)])
                next_node = tuple([round(path[index + 1][0], 4), round(path[index + 1][1], 4)])

                if current_node not in local_graph:
                    local_graph[current_node] = []

                if next_node not in local_graph[current_node]:
                    local_graph[current_node].append(next_node)

        busy_now = get_busy_coordinates()

        best_final_path = None
        best_time = None
        min_cost = float("inf")
        final_hospital_name = ""

        for route_info in all_routes_data:
            start_node = route_info["start"]
            start_node_tuple = tuple([round(start_node[0], 4), round(start_node[1], 4)])

            problem = problem_class(
                start_node=start_node_tuple,
                goal_node=route_info["goal"],
                graph=local_graph,
                busy_points=busy_now
            )

            result = solver.solve(problem)

            if result and isinstance(result, tuple):
                path, cost = result
                occupancy_penalty = occupancy[route_info["name"]] * 7000
                final_cost = cost + occupancy_penalty

                if path and final_cost < min_cost:
                    min_cost = final_cost
                    best_final_path = path
                    best_time = route_info["duration"]
                    final_hospital_name = route_info["name"]

        if best_final_path:
            route_coords_json = json.dumps(best_final_path)
            dist_m = min_cost

            save_route_result(
                address,
                final_hospital_name,
                dist_m,
                best_time,
                route_coords_json
            )

            visual_routes = []

            for route_info in all_routes_data:
                visual_routes.append({
                    "name": f"Alternativă spre {route_info['name']}",
                    "coords": route_info["coords"],
                    "distance": 0,
                    "duration": route_info["duration"],
                    "status": "alternativ"
                })

            visual_routes.append({
                "name": f"Ruta {self.method} spre {final_hospital_name}",
                "coords": best_final_path,
                "distance": dist_m,
                "duration": best_time,
                "status": "optim"
            })

            for point in busy_now:
                visual_routes.append({
                    "name": "Zonă trafic intens",
                    "coords": [point],
                    "distance": 0,
                    "duration": 0,
                    "status": "busy"
                })

            mapVisualizer.generate_map(
                [start_lat, start_lon],
                14,
                visual_routes,
                "m",
                "s",
                final_hospital_name
            )

            return HTMLResponse(
                content=open("iasi_routes.html", "r", encoding="utf-8").read()
            )

        return HTMLResponse("Nu s-a putut găsi o rută validă.", status_code=404)