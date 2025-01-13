from pyrosm import OSM
import networkx as nx
import geopandas as gpd

# Path to your OSM file
pbf_path = "D:/Github_extras/india-latest.osm.pbf"

# Initialize OSM
osm = OSM(pbf_path)

# Extract substations as points
substations = osm.get_pois(custom_filter={"power": ["substation"]})
print(f"Extracted {len(substations)} substations")

# Extract transmission lines as ways
lines = osm.get_network("driving", custom_filter={"power": ["line"]})
print(f"Extracted {len(lines)} transmission lines")

# Convert substations and lines into a graph
G = nx.Graph()

# Add substations as nodes
for _, row in substations.iterrows():
    G.add_node(row["id"], geometry=row["geometry"], **row)

# Add transmission lines as edges
for _, row in lines.iterrows():
    coords = list(row["geometry"].coords)
    for i in range(len(coords) - 1):
        G.add_edge(coords[i], coords[i + 1], **row)

print(f"Graph has {len(G.nodes)} nodes and {len(G.edges)} edges.")

# Save results (Optional)
substations.to_file("substations.geojson", driver="GeoJSON")
lines.to_file("lines.geojson", driver="GeoJSON")

from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="power_network_extractor")

def reverse_geocode(lat, lon):
    location = geolocator.reverse((lat, lon), exactly_one=True)
    return location.raw.get("address", {}).get("country"), location.raw.get("address", {}).get("state")

substations["country"], substations["region"] = zip(*substations.apply(
    lambda row: reverse_geocode(row.geometry.y, row.geometry.x), axis=1
))

import geopandas as gpd
import matplotlib.pyplot as plt

# Convert graph nodes and edges to GeoDataFrames
nodes = gpd.GeoDataFrame(
    [(node, data["geometry"]) for node, data in G.nodes(data=True)],
    columns=["id", "geometry"],
    crs="EPSG:4326"  # WGS 84
)

edges = gpd.GeoDataFrame(
    [(u, v, data["geometry"]) for u, v, data in G.edges(data=True)],
    columns=["source", "target", "geometry"],
    crs="EPSG:4326"
)

# Plot the data
fig, ax = plt.subplots(figsize=(12, 10))
nodes.plot(ax=ax, color="blue", markersize=50, label="Substations")
edges.plot(ax=ax, color="red", linewidth=1, label="Transmission Lines")

# Add map features
ax.set_title("Power Network in India", fontsize=16)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.legend()

# Show plot
plt.show()
