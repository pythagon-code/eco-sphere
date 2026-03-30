import math
from typing import Callable
from ursina import *
from globals import *
import os
import re
import zipfile
import urllib.request
import json
import csv

running = {}

def rebounded(func: Callable):
    running[func] = False
    def wrapper(*args, **kwargs):
        if running[func]:
            return
        running[func] = True
        func(*args, **kwargs)
        running[func] = False
    return wrapper

def spherical_to_cartesian(rho: float, phi: float, theta: float) -> tuple[float, float, float]:
    x = rho * math.sin(theta) * math.cos(phi)
    z = rho * math.sin(theta) * math.sin(phi)
    y = rho * math.cos(theta)
    return x, y, z

def draw_globe_line(
    globe: Entity, 
    rho: float, 
    color: Color,
    size: float,
    num_markers: int,
    phi: float | None = None,
    theta: float | None = None,
) -> None:
    assert (phi is None) ^ (theta is None)
    change_phi = phi is None
    for i in range(num_markers):
        angle = math.radians(i * (360 / num_markers))
        if change_phi:
            phi = angle
        else:
            theta = angle
        x, y, z = spherical_to_cartesian(rho, phi, theta)
        Entity(model="sphere", color=color, scale=size, position=(x, y, z), parent=globe)

def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))

def download(url: str, base_dir: str = "data") -> str:
    filename = url.split("/")[-1]
    file_path = os.path.join(base_dir, filename)
    if os.path.exists(file_path):
        return file_path

    os.makedirs(base_dir, exist_ok=True)

    urllib.request.urlretrieve(url, file_path)

    return file_path

def download_and_extract(url: str, base_dir: str = "data") -> str:
    filename = url.split("/")[-1]
    folder_name = re.sub(r"\.zip$", "", filename)
    folder_path = os.path.join(base_dir, folder_name)
    zip_path = os.path.join(base_dir, filename)

    os.makedirs(base_dir, exist_ok=True)
    urllib.request.urlretrieve(url, zip_path)

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(folder_path)

    os.remove(zip_path)
    return folder_path

def load_geojson(file_path: str) -> None:
    with open(file_path, "r") as f:
        geojson = json.load(f)
    import json
import math
from ursina import *

def draw_boundaries(globe: Entity, radius: float, col: Color, step: int = 1) -> None:
    boundaries_url = "http://raw.githubusercontent.com/nvkelso/natural-earth-vector/refs/heads/master/geojson/ne_110m_admin_0_countries.geojson"
    boundaries_path = download(boundaries_url, "data")
    with open(boundaries_path, "rb") as f:
        geojson = json.load(f)
    
    for feature in geojson["features"]:
        geometry = feature["geometry"]
        geom_type = geometry["type"]
        coords = geometry["coordinates"]
        
        polygons = coords if geom_type == "MultiPolygon" else [coords]
        
        for poly in polygons:
            outline = poly[0] if isinstance(poly[0][0], list) else poly
            
            if len(outline) < 20:
                continue
                
            vertices = []
            for lon, lat in outline[::step]:
                phi = math.radians(lon) 
                theta = math.radians(90 - lat)

                x, y, z = spherical_to_cartesian(radius, phi, theta)
                vertices.append(Vec3(x, y, z))

            if len(vertices) > 2:
                vertices.append(vertices[0])
                Entity(
                    model=Mesh(vertices=vertices, mode='line', static=True),
                    color=col,
                    parent=globe,
                    thickness=1
                )

def draw_centroids(globe: Entity, radius: float, col: Color, size: float) -> None:
    centroids_url = "https://raw.githubusercontent.com/google/dspl/master/samples/google/canonical/countries.csv"
    centroids_path = download(centroids_url, "data")
    with open(centroids_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                country = row["name"]

                countries[country] = 1

                phi = math.radians(lon)
                theta = math.radians(90 - lat)

                x, y, z = spherical_to_cartesian(radius, phi, theta)

                Entity(
                    model="sphere",
                    color=col,
                    scale=size,
                    position=(x, y, z),
                    parent=globe,
                    name=country
                )
            except:
                print(f"Error parsing row: {row}")