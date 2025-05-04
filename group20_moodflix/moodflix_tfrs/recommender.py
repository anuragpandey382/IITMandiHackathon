import os
import pprint
import tempfile

from typing import Dict, Text

import numpy as np
import tensorflow as tf
from dataloader import create_dataset

dataset = create_dataset()
dataset.batch(32)

movies = dataset.map(lambda x: x["Title"])
genres = dataset.map(lambda x: x["Genre"])
unique_movie_titles = np.unique(np.concatenate(list(movies)))
unique_genres = np.unique(np.concatenate(list(genres)))
print(unique_genres)


# class UserModel(tf.keras.Model):

#   def __init__(self):
#     super().__init__()

#     self.user_embedding = tf.keras.Sequential([
#         user_id_lookup,
#         tf.keras.layers.Embedding(user_id_lookup.vocab_size(), 32),
#     ])
#     self.timestamp_embedding = tf.keras.Sequential([
#       tf.keras.layers.Discretization(timestamp_buckets.tolist()),
#       tf.keras.layers.Embedding(len(timestamp_buckets) + 2, 32)
#     ])
#     self.normalized_timestamp = tf.keras.layers.Normalization(
#         axis=None
#     )

#   def call(self, inputs):

#     # Take the input dictionary, pass it through each input layer,
#     # and concatenate the result.
#     return tf.concat([
#         self.user_embedding(inputs["user_id"]),
#         self.timestamp_embedding(inputs["timestamp"]),
#         tf.reshape(self.normalized_timestamp(inputs["timestamp"]), (-1, 1))
#     ], axis=1)