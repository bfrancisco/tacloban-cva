import json
import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Fullscreen
import xml.etree.ElementTree as ET

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config("Tacloban City CVA", layout="wide")

# -----------------------------
# LOAD DATA
# -----------------------------
with open("landmarks.json") as f:
    landmarks = json.load(f)["landmarks"]

# -----------------------------
# CVI LOGIC
# -----------------------------
def compute_cvi(l):
    return round(
        (
            l["geomorphology"]["score"] +
            l["natural_buffers"]["score"] +
            l["engineering_structures"]["score"]
        ) / 3,
        2
    )

def get_color(cvi):
    if cvi <= 1.0:
        return "red"
    elif cvi <= 2.0:
        return "orange"
    elif cvi <= 3.0:
        return "yellow"
    elif cvi <= 4.0:
        return "green"
    else:
        return "blue"

# -----------------------------
# LOAD KML
# -----------------------------
def load_kml(kml_file):
    tree = ET.parse(kml_file)
    root = tree.getroot()
    ns = {"kml": "http://www.opengis.net/kml/2.2"}

    polygons = {}
    for placemark in root.findall(".//kml:Placemark", ns):
        name = placemark.find("kml:name", ns).text
        coords_text = placemark.find(".//kml:coordinates", ns).text.strip()

        coords = []
        for c in coords_text.split():
            lon, lat, _ = map(float, c.split(","))
            coords.append([lat, lon])

        polygons[name] = coords

    return polygons

kml_polygons = load_kml("tacloban_coastal_landmarks.kml")

# -----------------------------
# SIDEBAR – LANDMARK LIST
# -----------------------------
st.sidebar.title("📍 Coastal Landmarks")

landmark_names = [l["name"] for l in landmarks]

selected_name = st.sidebar.radio(
    "Select a landmark",
    landmark_names,
    index=None
)

# -----------------------------
# MAP CENTER LOGIC
# -----------------------------
if selected_name is None:
    map_center = [11.230, 125.003]  # Tacloban City overview
    zoom_level = 13.5
    selected_landmark = None
    selected_cvi = None
    selected_color = None
else:
    selected_landmark = next(
        l for l in landmarks if l["name"] == selected_name
    )

    selected_cvi = compute_cvi(selected_landmark)
    selected_color = get_color(selected_cvi)
    selected_coords = kml_polygons[selected_name]

    map_center = [
        sum(p[0] for p in selected_coords) / len(selected_coords),
        sum(p[1] for p in selected_coords) / len(selected_coords)
    ]
    zoom_level = 15

# -----------------------------
# MAP
# -----------------------------
m = folium.Map(
    location=map_center,
    zoom_start=zoom_level
)
Fullscreen().add_to(m)

for l in landmarks:
    cvi = compute_cvi(l)
    color = get_color(cvi)
    coords = kml_polygons[l["name"]]

    border_weight = 4 if l["name"] == selected_name else 1

    folium.Polygon(
        locations=coords,
        fill=True,
        fill_color=color,
        fill_opacity=0.6,
        color="black",
        weight=border_weight
    ).add_to(m)

# -----------------------------
# MAIN UI
# -----------------------------
st.title("🌊 Coastal Vulnerability Assessment – Tacloban City")

col1, col2 = st.columns([2, 1])

with col1:
    st_folium(m, width="100%", height=600)

with col2:
    if selected_name is None:
        st.subheader("📌 No landmark selected")
        st.info(
            "Select a coastal landmark from the list to view its "
            "Coastal Vulnerability Index (CVI) and assessment details."
        )
    else:
        st.subheader(f"📌 {selected_name}")

        st.markdown(f"""
        **Coastal Vulnerability Index (CVI):** `{selected_cvi}`  
        **Vulnerability Level:** `{selected_color.capitalize()}`
        """)

        st.markdown("### 📐 Scoring Breakdown")

        st.markdown(f"""
        **Geomorphology ({selected_landmark['geomorphology']['score']})**  
        {selected_landmark['geomorphology']['description']}

        **Natural Buffers ({selected_landmark['natural_buffers']['score']})**  
        {selected_landmark['natural_buffers']['description']}

        **Engineering Structures ({selected_landmark['engineering_structures']['score']})**  
        {selected_landmark['engineering_structures']['description']}
        """)

# -----------------------------
# CVI EXPLANATION
# -----------------------------
st.markdown("""
### ℹ️ Coastal Vulnerability Index (CVI) Interpretation

The **Coastal Vulnerability Index (CVI)** indicates how susceptible a coastal area is to
flooding, erosion, and storm surge based on physical setting and protection mechanisms.

**Color and Score Classification:**
- 🔵 **Blue (1)** – Lowest vulnerability; elevated or well-protected areas  
- 🟢 **Green (2)** – Low vulnerability; minor exposure to hazards  
- 🟡 **Yellow (3)** – Moderate vulnerability; noticeable risk  
- 🟠 **Orange (4)** – High vulnerability; significant exposure  
- 🔴 **Red (5)** – Highest vulnerability; very exposed and at risk  
""")

# -----------------------------
# IMAGE SHOWCASE
# -----------------------------
st.markdown("### 🖼️ Google Streetview Photos")

if selected_name is None:
    st.info("Select a landmark to view related field images.")
else:
    images = selected_landmark.get("images", [])

    if not images:
        st.warning("No images available for this landmark.")
    else:
        cols = st.columns(3)
        for idx, img_path in enumerate(images):
            with cols[idx % 3]:
                st.image(
                    img_path,
                    use_container_width=True,
                    caption=selected_name
                )

st.markdown("---")
st.markdown("© 2026 James Bryan Francisco")