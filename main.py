import sys
import os
import tensorflow as tf
import numpy as np
import rasterio
import cv2
import base64
import tensorflow as tf
from affine import Affine
from rasterio._base import _transform

os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

# MNIST methods
import sys
sys.path.append('mnist')
import model

x = tf.placeholder("float", [None, 784])
sess = tf.Session()

with tf.variable_scope("simple"):
    y1, variables = model.simple(x)
saver = tf.train.Saver(variables)
saver.restore(sess, "mnist/data/simple.ckpt")
def simple(input):
    return sess.run(y1, feed_dict={x: input}).flatten().tolist()

with tf.variable_scope("convolutional"):
    keep_prob = tf.placeholder("float")
    y2, variables = model.convolutional(x, keep_prob)
saver = tf.train.Saver(variables)
saver.restore(sess, "mnist/data/convolutional.ckpt")
def convolutional(input):
    return sess.run(y2, feed_dict={x: input, keep_prob: 1.0}).flatten().tolist()

# Remix API methods
tile_size = [512, 512]
model_dir = '/data/remix/'
raster_file = model_dir + 'ORCEUG17-merc-cloud.tif'

def inceptionV3(tile_size, model_dir, lon, lat):

    output_array = []

    with rasterio.open(raster_file) as src:
        dst_crs = src.crs
        transform = src.transform
        rev = ~Affine.from_gdal(*transform)

    src_crs = {'init': 'EPSG:4326'}
    x,y = _transform(src_crs, dst_crs, [lon], [lat], None)

    coordinates = [x[0], y[0]]
    #Transform the point coordinates
    coordinates = rev*coordinates

    #Extract the point Id to label the tile
    id = int(abs(lat*lon))
    min = [c - tile_size[1]/2 for c in coordinates]
    max = [c + tile_size[0]/2 for c in coordinates]

    with rasterio.open(raster_file) as src:
        r, g, b = src.read(window=((min[1], max[1]), (min[0], max[0])))
        tile = cv2.merge((b, g, r))

        label_lines = [line.rstrip() for line
                       in tf.gfile.GFile(model_dir + "retrained_labels-4_4N_5_7.txt")]
        with tf.gfile.FastGFile(model_dir + "retrained_graph-4_4N_5_7.pb", 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            _ = tf.import_graph_def(graph_def, name='')

        with tf.Session() as sess:

            softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')

            tile_str = cv2.imencode('.jpg', tile)[1].tostring()
            predictions = sess.run(softmax_tensor, \
                     {'DecodeJpeg/contents:0': tile_str})

            top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]

            output_array.append(["img_base64", "data:image/  jpg;base64," + base64.b64encode(tile_str)])
            for node_id in top_k:
                human_string = label_lines[node_id]
                score = predictions[0][node_id]
                output_array.append([str(human_string), str(score)])

    return output_array

def remix_guess(input):
    return "TBD"

# webapp
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

@app.route('/api/lanes', methods=['GET'])
def lanes():
    lon = request.args.get('lon')
    lat = request.args.get('lat')
    output1 = inceptionV3(tile_size, model_dir, float(lon), float(lat))
    output2 = remix_guess(input)
    return jsonify(results=[output1, output2])

@app.route('/api/mnist', methods=['POST'])
def mnist():
    input = ((255 - np.array(request.json, dtype=np.uint8)) / 255.0).reshape(1, 784)
    output1 = simple(input)
    output2 = convolutional(input)
    return jsonify(results=[output1, output2])

@app.route('/remix')
def remix():
    return render_template('lanes.html')

@app.route('/')
def main():
    return render_template('index.html')