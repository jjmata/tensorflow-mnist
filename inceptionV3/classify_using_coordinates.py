import os
import fiona
import rasterio
import cv2
from affine import Affine

from def_classify import classify

def extract_tile_to_infer(tile_size, raster_file, tiles_dir, points_shp):

    offset = 5480378.654 - 5450650

    with rasterio.open(raster_file) as src:
        transform = src.transform
        rev = ~Affine.from_gdal(*transform)

    points = fiona.open(points_shp)

    for key in points.keys():
        print 'Creating tiles from points'

        coordinates = points[key]['geometry']['coordinates']
        coordinates = [coordinates[0], coordinates[1] + offset]
        #Transform the point coordinates
        coordinates = rev*coordinates

        #Extract the point Id to label the tile
        id = int(points[key]['id'])
        min = [c - tile_size[1]/2 for c in coordinates]
        max = [c + tile_size[0]/2 for c in coordinates]

        with rasterio.open(raster_file) as src:
            r, g, b = src.read(window=((min[1], max[1]), (min[0], max[0])))
            tile = cv2.merge((b, g, r))

            cv2.imwrite(os.path.join(tiles_dir, 'tile_{}.jpg'.format(id+1)), tile)

    return None

tile_size = [512, 512]
raster_file = '/data/remix/ORCEUG17-merc-cloud.tif'
points_shp = '/data/remix/points_click2.shp'
tiles_dir = '/data/remix/tiles'
save_dir = '/data/remix'

if not os.path.exists(tiles_dir):
    os.mkdir(tiles_dir)

extract_tile_to_infer(tile_size,raster_file, tiles_dir, points_shp)
classify(tiles_dir, save_dir)
