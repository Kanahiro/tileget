import os
import argparse
import math
import itertools
import requests
import time

import tqdm
import tiletanic
import shapely


def get_args():
    parser = argparse.ArgumentParser(description='xyz-tile download tool')
    parser.add_argument('tileurl', help='xyz-tile url')
    parser.add_argument('output_dir', help='output dir')
    parser.add_argument('--extent',
                        help='min_lon min_lat max_lon max_lat, whitespace delimited', nargs=4)
    parser.add_argument('--geojson')
    parser.add_argument('--minzoom', default=0)
    parser.add_argument('--maxzoom', default=16)
    parser.add_argument('--header')
    parser.add_argument('--interval', default=500)
    parser.add_argument(
        '--overwrite', help='overwrite existing files', action='store_true')
    return parser.parse_args()


def lonlat_to_webmercator(lonlat: list):
    return (lonlat[0] * 20037508.34 / 180, math.log(math.tan((90 + lonlat[1]) * math.pi / 360)) / (math.pi / 180) * 20037508.34 / 180)


def main():
    args = get_args()
    extent = tuple(map(float, args.extent))
    geometry = get_geometry_as_3857(extent)
    all_tiles = tuple(itertools.chain.from_iterable((get_tiles_generator(
        geometry, zoom) for zoom in range(int(args.minzoom), int(args.maxzoom) + 1))))

    for tile in tqdm.tqdm(all_tiles):
        ext = args.tileurl.split(".")[-1]
        write_dir = os.path.join(args.output_dir, str(tile[2]), str(tile[0]))
        write_filepath = os.path.join(write_dir, str(tile[1]) + "." + ext)

        if os.path.exists(write_filepath) and args.overwrite == False:
            continue

        os.makedirs(write_dir, exist_ok=True)

        url = args.tileurl.replace(
            r"{x}", str(tile[0])).replace(
            r"{y}", str(tile[1])).replace(
            r"{z}", str(tile[2]))
        data = requests.get(url).content

        with open(write_filepath, mode='wb') as f:
            f.write(data)

        time.sleep(int(args.interval) / 1000)


def get_tiles_generator(geometry: dict, zoomlevel: int):
    """
    returns a generator to yield tile-indices covering the geometry at the zoomlevel

    Args:
        geometry (dict): GeoJSON Polygon geometry
        zoomlevel (int)

    Returns:
        Generator: yields tile-index [x, y, z]
    """
    tilesceme = tiletanic.tileschemes.WebMercator()
    feature_shape = shapely.geometry.shape(geometry)
    generator = tiletanic.tilecover.cover_geometry(
        tilesceme, feature_shape, zoomlevel)
    return generator


def get_geometry_as_3857(extent: list) -> dict:
    """
    returns GeoJSON Polygon geometry dict
    extent must be latitudes and longitudes and reprojected to WebMercator EPSG:3857

    Args:
        extent (list): [min_lon, min_lat, max_lon, max_lat]

    Returns:
        dict: Polygon geometry
    """
    return {
        "type": "Polygon",
        "coordinates": (tuple(map(lonlat_to_webmercator, (
            (extent[0], extent[1]),
            (extent[2], extent[1]),
            (extent[2], extent[3]),
            (extent[0], extent[3]),
            (extent[0], extent[1]),))),)
    }


if __name__ == "__main__":
    main()
