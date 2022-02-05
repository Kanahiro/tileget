import os
import argparse
import math
import itertools
import time
import urllib.request
import socket
from concurrent.futures import ThreadPoolExecutor

import tiletanic
import shapely


def get_args():
    parser = argparse.ArgumentParser(description='xyz-tile download tool')
    parser.add_argument('tileurl', help='xyz-tile url')
    parser.add_argument('output_dir', help='output dir')
    parser.add_argument('--extent',
                        help='min_lon min_lat max_lon max_lat, whitespace delimited', nargs=4)
    parser.add_argument('--geojson')
    parser.add_argument('--minzoom', default="0")
    parser.add_argument('--maxzoom', default="16")
    parser.add_argument('--interval', default="500")
    parser.add_argument('--overwrite',
                        help='overwrite existing files',
                        action='store_true')
    parser.add_argument('--timeout', default="5")
    parser.add_argument('--parallel', default="1")
    args = parser.parse_args()

    verified_args = {
        "tileurl": args.tileurl,
        "output_dir": args.output_dir,
        "extent": None,
        "geojson": None,
        "minzoom": int(args.minzoom),
        "maxzoom": int(args.maxzoom),
        "interval": int(args.interval),
        "overwrite": args.overwrite,
        "timeout": int(args.timeout),
        "parallel": int(args.parallel)
    }
    if args.extent is not None:
        verified_args["extent"] = tuple(map(float, args.extent))

    if args.geojson is not None:
        # TODO: load geojson-geometry
        verified_args["geojson"] = None

    return verified_args


def lonlat_to_webmercator(lonlat: list):
    return (lonlat[0] * 20037508.34 / 180, math.log(math.tan((90 + lonlat[1]) * math.pi / 360)) / (math.pi / 180) * 20037508.34 / 180)


def main():
    args = get_args()
    geometry = get_geometry_as_3857(args["extent"])
    all_tiles = tuple(itertools.chain.from_iterable((get_tiles_generator(
        geometry, zoom) for zoom in range(args["minzoom"], args["maxzoom"] + 1))))

    def download(tile, idx):
        ext = args["tileurl"].split(".")[-1]
        write_dir = os.path.join(
            args["output_dir"], str(tile[2]), str(tile[0]))
        write_filepath = os.path.join(write_dir, str(tile[1]) + "." + ext)

        if os.path.exists(write_filepath) and args["overwrite"] == False:
            return

        os.makedirs(write_dir, exist_ok=True)

        url = args["tileurl"].replace(
            r"{x}", str(tile[0])).replace(
            r"{y}", str(tile[1])).replace(
            r"{z}", str(tile[2]))

        data = None
        while(True):
            try:
                data = urllib.request.urlopen(url, timeout=args["timeout"])
                break
            except socket.timeout:
                print("timeout, retrying... :" + url)
            except urllib.error.HTTPError as e:
                print(e.code + " error, skipping... :" + url)
                break
            except Exception as e:
                print(e.args + " skipping... :" + url)
                break

        if data is not None:
            with open(write_filepath, mode='wb') as f:
                f.write(data.read())
            time.sleep(args["interval"] / 1000)

        if idx % 10 == 0:
            print(str(idx + 1) + "/" + str(len(all_tiles)))

    with ThreadPoolExecutor(max_workers=args["parallel"]) as executor:
        for idx, tile in enumerate(all_tiles):
            executor.submit(download, tile, idx)


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