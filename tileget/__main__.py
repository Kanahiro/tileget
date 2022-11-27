import os
import argparse
import math
import time
import urllib.request
import json
from concurrent.futures import ThreadPoolExecutor

import tiletanic
import shapely


def get_args():
    parser = argparse.ArgumentParser(description="xyz-tile download tool")
    parser.add_argument("tileurl", help=r"xyz-tile url in {z}/{x}/{y} template")
    parser.add_argument("output_dir", help="output dir")
    parser.add_argument(
        "--extent",
        help="min_lon min_lat max_lon max_lat, whitespace delimited",
        nargs=4,
    )
    parser.add_argument(
        "--geojson",
        help="path to geojson which is Feature or FeatureCollection with geometry in EPSG:3857",
    )
    parser.add_argument("--minzoom", default="0", help="default to 0")
    parser.add_argument("--maxzoom", default="16", help="default to 16")
    parser.add_argument(
        "--interval",
        default="500",
        help="time taken after each-request, set as miliseconds in interger, default to 500",
    )
    parser.add_argument(
        "--overwrite", help="overwrite existing files", action="store_true"
    )
    parser.add_argument(
        "--timeout",
        default="5",
        help="wait response until this value, set as seconds in integer, default to 5",
    )
    parser.add_argument("--parallel", default="1", help="num of parallel requests")
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
        "parallel": int(args.parallel),
    }

    if args.extent is None and args.geojson is None:
        raise Exception("extent or geojson must be input")

    if args.extent is not None:
        verified_args["extent"] = tuple(map(float, args.extent))

    if args.geojson is not None:
        verified_args["geojson"] = args.geojson

    return verified_args


def lonlat_to_webmercator(lonlat: list):
    return (
        lonlat[0] * 20037508.34 / 180,
        math.log(math.tan((90 + lonlat[1]) * math.pi / 360))
        / (math.pi / 180)
        * 20037508.34
        / 180,
    )


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
        "coordinates": (
            tuple(
                map(
                    lonlat_to_webmercator,
                    (
                        (extent[0], extent[1]),
                        (extent[2], extent[1]),
                        (extent[2], extent[3]),
                        (extent[0], extent[3]),
                        (extent[0], extent[1]),
                    ),
                )
            ),
        ),
    }


def main():
    args = get_args()

    if args["extent"] is not None:
        geometry = shapely.geometry.shape(get_geometry_as_3857(args["extent"]))
    elif args["geojson"] is not None:
        with open(args["geojson"], mode="r") as f:
            geojson = json.load(f)
        if geojson.get("features") is None:
            geometry = shapely.geometry.shape(geojson["geometry"])
        else:
            geometries = [
                shapely.geometry.shape(g)
                for g in list(map(lambda f: f["geometry"], geojson["features"]))
            ]
            geometry = shapely.ops.unary_union(geometries)

    def download(tile):
        ext = args["tileurl"].split(".")[-1]
        write_dir = os.path.join(args["output_dir"], str(tile[2]), str(tile[0]))
        write_filepath = os.path.join(write_dir, str(tile[1]) + "." + ext)

        if os.path.exists(write_filepath) and args["overwrite"] == False:
            return

        url = (
            args["tileurl"]
            .replace(r"{x}", str(tile[0]))
            .replace(r"{y}", str(tile[1]))
            .replace(r"{z}", str(tile[2]))
        )

        data = None
        while True:
            try:
                data = urllib.request.urlopen(url, timeout=args["timeout"])
                break
            except urllib.error.HTTPError as e:
                raise Exception(str(e) + ":" + url)
            except Exception as e:
                if (
                    str(e.args)
                    == "(timeout('_ssl.c:1091: The handshake operation timed out'),)"
                ):
                    print("timeout, retrying... :" + url)
                else:
                    raise Exception(str(e) + ":" + url)

        if data is not None:
            os.makedirs(write_dir, exist_ok=True)
            with open(write_filepath, mode="wb") as f:
                f.write(data.read())
            time.sleep(args["interval"] / 1000)

    with ThreadPoolExecutor(max_workers=args["parallel"]) as executor:
        for zoom in range(args["minzoom"], args["maxzoom"] + 1):
            generator = tiletanic.tilecover.cover_geometry(
                tiletanic.tileschemes.WebMercator(), geometry, zoom
            )
            for tile in generator:
                future = executor.submit(download, tile)
                if future.exception() is not None:
                    print(future.exception())

    print("finished")


if __name__ == "__main__":
    main()
