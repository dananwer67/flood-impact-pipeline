import geopandas as gpd

# These 3 districts are Indian-administered territory (part of Ladakh/Jammu &
# Kashmir) but appear nested inside Pakistan's claimed Gilgit-Baltistan structure
# in this GADM file. Excluded because this project models Pakistan's administrative
# flood response system, which does not govern these areas. See docs/methodology.md
# for the full investigation and reasoning.
EXCLUDED_DISTRICT_IDS = [
    "Z06.6.1.4_1",  # Kargil
    "Z06.6.1.5_1",  # Kupwara(GilgitWazarat)
    "Z06.6.1.6_1",  # Ladakh(Leh)
]


def load_pakistan_districts():
    gdf = gpd.read_file("data/raw/gadm_pakistan/gadm41_PAK_3.json")

    gdf = gdf[~gdf["GID_3"].isin(EXCLUDED_DISTRICT_IDS)]

    gdf = gdf[["GID_3", "NAME_3", "geometry"]].rename(
        columns={"GID_3": "district_id", "NAME_3": "district_name"}
    )

    return gdf
