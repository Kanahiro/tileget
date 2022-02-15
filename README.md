# tileget

Tile download utility - easily download xyz-tile data.

## installation

```sh
pip install tileget
```

## usage

```
usage: tileget [-h] [--extent EXTENT EXTENT EXTENT EXTENT]
                   [--geojson GEOJSON] [--minzoom MINZOOM] [--maxzoom MAXZOOM]
                   [--interval INTERVAL] [--overwrite] [--timeout TIMEOUT]
                   [--parallel PARALLEL]
                   tileurl output_dir

xyz-tile download tool

positional arguments:
  tileurl               xyz-tile url in {z}/{x}/{y} template
  output_dir            output dir

optional arguments:
  -h, --help            show this help message and exit
  --extent EXTENT EXTENT EXTENT EXTENT
                        min_lon min_lat max_lon max_lat, whitespace delimited
  --geojson GEOJSON     relative path to geojson which is Feature or
                        FeatureCollection with geometry in EPSG:3857
  --minzoom MINZOOM
  --maxzoom MAXZOOM
  --interval INTERVAL   time taken after each-request, set as miliseconds in
                        interger
  --overwrite           overwrite existing files
  --timeout TIMEOUT     wait response until this value, set as seconds in
                        integer
  --parallel PARALLEL   num of parallel requests
```

### exapmles

#### get tiles in extent [141.23 40.56 142.45 43.78] and in zoomlevels 0-12


```sh
tileget https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg ./output_dir --extent 141.23 40.56 142.45 43.78 --maxzoom 12
```

