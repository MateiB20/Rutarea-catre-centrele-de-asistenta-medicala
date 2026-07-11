import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from database_manager import initialize_db, add_or_get_hospital
from map_visualizer import MapVisualizer
from error_manager import InvalidInputError,  process_location
from routing_module import RoutingModule
from logging_manager import log_error

mapVisualizer = MapVisualizer("iasi_routes.html")

initialize_db()

app = FastAPI()

hospitals = [
    {"name": "Spitalul Clinic Județean de Urgență Sf. Spiridon", "lat": 47.1594, "lon": 27.6068, "capacity": 1100},
    {"name": "Spitalul Clinic de Urgență Sf. Maria", "lat": 47.1589, "lon": 27.6072, "capacity": 650},
    {"name": "Spitalul Arcadia", "lat": 47.1575, "lon": 27.6010, "capacity": 100},
    {"name": "Spitalul Elytis", "lat": 47.1530, "lon": 27.5760, "capacity": 50}
]

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <style>
        h1 {
            color: rgb(34, 2, 0);
            font-size: 48px;
            font-weight: 700;
            line-height: 1.1;
            margin-bottom: 24px;
        }
        button:hover {
            background: rgb(21, 101, 192);
        }
        label {
            font-weight: 600;
            display: block;
        }
        input:focus,
        select:focus {
            outline: none;
            border-color: rgb(25, 118, 210);
            box-shadow: 0 0 0 3px rgba(25,118,210,0.15);
        }
        </style>
    </head>
    <body>
        <form action="/route" method="get">
            <h1>Sistem inteligent de rutare către unități medicale</h1>
            <label for="address">Locatie:</label><br>
            <input type="text" name="address" id="address" placeholder="Strada Palat, Iasi" size="40">
            <br><br>
            <label for="method">Metodă Routing:</label><br>
            <select name="method" id="method">
                <option value="Astar">Algoritm A*</option>
                <option value="BestFirst">Algoritm Best-First Search</option>
            </select>
            <br><br>
            <button type="submit">Gaseste ruta optimă</button>
        </form>
    </body>
    </html>
    """


@app.get("/route", response_class=HTMLResponse)
def route(address: str, method:str):
    for h in hospitals:
        add_or_get_hospital(h["name"], h["lat"], h["lon"], h["capacity"])
    url2 = "https://nominatim.openstreetmap.org/search"
    params2 = {
        "q": address.strip() + ", Romania",
        "format": "jsonv2",
        "limit": 1
    }
    try:
        response2 = requests.get(url2, params=params2, headers={"User-Agent": "LicentaApp/1.0"})
        data2 = response2.json()
        if not data2:
            raise InvalidInputError(f"Locația {address} nu a fost gasită.")
        start_lon = float(data2[0]["lon"])
        start_lat = float(data2[0]["lat"])
        process_location(start_lon, start_lat, address)
        router=RoutingModule(method)
        return router.route(hospitals, address, start_lon, start_lat)
    except InvalidInputError as e:
            return HTMLResponse(f"Eroare legată de datele introduse.", status_code=400)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        log_error(str(e))
        return HTMLResponse(f"A apărut o eroare neașteptată.", status_code=500)