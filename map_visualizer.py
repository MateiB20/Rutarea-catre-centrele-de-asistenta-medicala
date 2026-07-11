import folium


class MapVisualizer:
    def __init__(self, file):
        self.file = file

    def normalize_coord(self, coord):
        first = coord[0]
        second = coord[1]

        if 46 <= first <= 48 and 26 <= second <= 29:
            return [first, second]

        if 26 <= first <= 29 and 46 <= second <= 48:
            return [second, first]

        return [first, second]

    def get_tooltip(self, route):
        name = route.get("name", "")
        distance = route.get("distance", 0)
        duration = route.get("duration", 0)

        tooltip = f"<b>{name}</b>"

        if distance:
            tooltip += f"<br>Cost decizional: {round(distance, 2)}"

        if duration:
            tooltip += f"<br>Durată estimată: {round(duration, 2)} s"

        return tooltip

    def generate_map(self, location, zoom_start, routes, distance_unit, time_unit, final_hospital_name):
        m = folium.Map(
            location=location,
            zoom_start=zoom_start,
            tiles="CartoDB Positron"
        )

        alternatives_layer = folium.FeatureGroup(
            name="Rute candidate / alternative",
            show=True
        )

        optimal_layer = folium.FeatureGroup(
            name="Ruta aleasă",
            show=True
        )

        busy_layer = folium.FeatureGroup(
            name="Zone aglomerate / ocupate",
            show=True
        )

        final_destination = None

        for route in routes:
            status = route.get("status", "")
            raw_coords = route.get("coords", [])

            if not raw_coords:
                continue

            coords = [self.normalize_coord(coord) for coord in raw_coords]

            if status == "busy":
                for coord in coords:
                    folium.CircleMarker(
                        location=coord,
                        radius=5,
                        color="red",
                        fill=True,
                        fill_color="red",
                        fill_opacity=0.7,
                        popup="Zonă aglomerată",
                        tooltip="Zonă aglomerată"
                    ).add_to(busy_layer)

            elif status == "alternativ":
                if len(coords) >= 2:
                    folium.PolyLine(
                        locations=coords,
                        color="orange",
                        weight=3,
                        opacity=0.45,
                        tooltip=self.get_tooltip(route)
                    ).add_to(alternatives_layer)

            elif status == "optim":
                if len(coords) >= 2:
                    folium.PolyLine(
                        locations=coords,
                        color="green",
                        weight=7,
                        opacity=0.9,
                        tooltip=self.get_tooltip(route)
                    ).add_to(optimal_layer)

                    final_destination = coords[-1]

        alternatives_layer.add_to(m)
        optimal_layer.add_to(m)
        busy_layer.add_to(m)

        legend_html = """
        <div style="
            position: fixed;
            bottom: 30px;
            left: 30px;
            background: white;
            padding: 12px;
            border: 2px solid #555;
            border-radius: 8px;
            z-index: 9999;
            font-family: Arial;
            font-size: 14px;">
            <b>Legendă rutare</b><br>
            <span style="color: orange;">━━</span> Rute candidate / alternative<br>
            <span style="color: green;">━━</span> Ruta aleasă de algoritm<br>
            <span style="color: red;">●</span> Zonă aglomerată / ocupată
        </div>
        """

        m.get_root().html.add_child(folium.Element(legend_html))

        m.save(self.file)

        return m._repr_html_()