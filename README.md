# tileget

## installation

```sh
pip install tileget
```

## usage

```sh
tileget <tile url> <output directory> [OPTIONS]
```

### exapmles

#### get tiles in extent [141.23 40.56 142.45 43.78] and in zoomlevels 0-12


```sh
tileget https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg ./output_dir --extent 141.23 40.56 142.45 43.78 --maxzoom 12
```

