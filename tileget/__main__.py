import os
import argparse
import time
import urllib.request
import json
from concurrent.futures import ThreadPoolExecutor

import tiletanic
import shapely
from pyproj import Transformer


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
        help="path to geojson file of Feature or FeatureCollection",
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
    parser.add_argument("--tms", help="if set, parse z/x/y as TMS", action="store_true")
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
        "tms": args.tms,
    }

    if args.extent is None and args.geojson is None:
        raise Exception("extent or geojson must be input")

    if args.extent is not None:
        verified_args["extent"] = tuple(map(float, args.extent))

    if args.geojson is not None:
        verified_args["geojson"] = args.geojson

    return verified_args


def main():
    args = get_args()

    if args["extent"] is not None:
        geometry = shapely.geometry.shape(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        (args["extent"][0], args["extent"][1]),
                        (args["extent"][2], args["extent"][1]),
                        (args["extent"][2], args["extent"][3]),
                        (args["extent"][0], args["extent"][3]),
                        (args["extent"][0], args["extent"][1]),
                    ],
                ],
            }
        )
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

    # tiletanic accept only EPSG:3857 shape, convert
    transformer = Transformer.from_crs(4326, 3857, always_xy=True)
    geom_3857 = shapely.ops.transform(transformer.transform, geometry)

    def download(tile):
        basepath = args["tileurl"].split("/")[-1]  # ?foo=bar&z={z}.ext
        segments = basepath.split(".")
        ext = "." + segments[-1] if len(segments) > 1 else ""

        write_dir = os.path.join(args["output_dir"], str(tile[2]), str(tile[0]))
        write_filepath = os.path.join(write_dir, str(tile[1]) + ext)

        if os.path.exists(write_filepath) and not args["overwrite"]:
            # skip if already exists when not-overwrite mode
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

    tilescheme = (
        tiletanic.tileschemes.WebMercatorBL()
        if args["tms"]
        else tiletanic.tileschemes.WebMercator()
    )

    with ThreadPoolExecutor(max_workers=args["parallel"]) as executor:
        for zoom in range(args["minzoom"], args["maxzoom"] + 1):
            generator = tiletanic.tilecover.cover_geometry(tilescheme, geom_3857, zoom)
            for tile in generator:
                future = executor.submit(download, tile)
                if future.exception() is not None:
                    print(future.exception())

    print("finished")


if __name__ == "__main__":
    main()
