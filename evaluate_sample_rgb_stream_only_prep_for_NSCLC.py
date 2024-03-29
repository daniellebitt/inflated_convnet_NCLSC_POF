# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Loads a sample video and classifies using a trained Kinetics checkpoint."""

#NB, the default if for this to load the imagenet pre-trained rgb model, although can choose not to use chkpt trained from 
#scratch from Kinetics instead of the chkpt from model pre-trained on imagenet (see multi_evaluate.sh)

#remove rgb600 throughout

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf

#the i3d file containts the model architecture
import i3d

#sets the image size
_IMAGE_SIZE = 224

#sets the number of video frames
_SAMPLE_VIDEO_FRAMES = 78

#just the path to the video RBG and flow np arrays that are being classified
_SAMPLE_PATHS = {
    'rgb': 'data/mock_array.npy'
}

#paths to the checkpoints (weights) for models trained from scratch, or pre-trained using imagenet first
#these pre-trained checkpoins will be loaded into the tf session
#I think I will want to use rbg_imagenet
_CHECKPOINT_PATHS = {
    'rgb': 'data/checkpoints/rgb_scratch/model.ckpt',
    #'rgb600': 'data/checkpoints/rgb_scratch_kin600/model.ckpt',
    'rgb_imagenet': 'data/checkpoints/rgb_imagenet/model.ckpt'
}

#path to the labels
_LABEL_MAP_PATH = 'data/label_map.txt'
#_LABEL_MAP_PATH_600 = 'data/label_map_600.txt'

FLAGS = tf.flags.FLAGS

#defining flags, can be used to adjust which model checkpoint to load and 
#which streams to use (rbg, flow, or both)
#remember, default: eval_type=rgb and imaget_pretrained=True
tf.flags.DEFINE_string('eval_type', 'rgb', 'rgb600')
tf.flags.DEFINE_boolean('imagenet_pretrained', True, '')


def main(unused_argv):
  tf.logging.set_verbosity(tf.logging.INFO)
  #defines eval_type
  eval_type = FLAGS.eval_type

  imagenet_pretrained = FLAGS.imagenet_pretrained

  NUM_CLASSES = 400
  #if eval_type == 'rgb600':
    #NUM_CLASSES = 600

  if eval_type not in ['rgb']:
    raise ValueError('Bad `eval_type`, must be rgb')

  #this prepares the labels from the appropriate path to the label file
  #if eval_type == 'rgb600':
    #kinetics_classes = [x.strip() for x in open(_LABEL_MAP_PATH_600)]
  #else:
  kinetics_classes = [x.strip() for x in open(_LABEL_MAP_PATH)]

  if eval_type in ['rgb']:
    #creates the placeholder input
    # RGB input has 3 channels.
    rgb_input = tf.placeholder(
        tf.float32,
        shape=(1, _SAMPLE_VIDEO_FRAMES, _IMAGE_SIZE, _IMAGE_SIZE, 3))

    #builds the model for the RBG stream
    with tf.variable_scope('RGB'):
      #defines the model
      rgb_model = i3d.InceptionI3d(
          NUM_CLASSES, spatial_squeeze=True, final_endpoint='Logits')

      # above ~ model = myModel()


      #runs the model with logits as endpoint
      rgb_logits, _ = rgb_model(
          rgb_input, is_training=False, dropout_keep_prob=1.0)

      # above ~ predictions = model(images)

    rgb_variable_map = {}
    for variable in tf.global_variables():

      if variable.name.split('/')[0] == 'RGB':
        #if eval_type == 'rgb600':
          #rgb_variable_map[variable.name.replace(':0', '')[len('RGB/inception_i3d/'):]] = variable
        #else:
        rgb_variable_map[variable.name.replace(':0', '')] = variable

    rgb_saver = tf.train.Saver(var_list=rgb_variable_map, reshape=True)

#commenting out the flow stream...
#builds the model for the Flow stream and saves checkpoint
  #if eval_type in ['flow', 'joint']:
    # Flow input has only 2 channels.
    #flow_input = tf.placeholder(
        #tf.float32,
        #shape=(1, _SAMPLE_VIDEO_FRAMES, _IMAGE_SIZE, _IMAGE_SIZE, 2))
    #with tf.variable_scope('Flow'):
      #flow_model = i3d.InceptionI3d(
          #NUM_CLASSES, spatial_squeeze=True, final_endpoint='Logits')
      #flow_logits, _ = flow_model(
          #flow_input, is_training=False, dropout_keep_prob=1.0)
    #saves the appropriate checkpoint weights for use later
    #flow_variable_map = {}
    #for variable in tf.global_variables():
      #if variable.name.split('/')[0] == 'Flow':
        #flow_variable_map[variable.name.replace(':0', '')] = variable
    #flow_saver = tf.train.Saver(var_list=flow_variable_map, reshape=True)

#option to use 2-stream of flow-only stream in prediction is commented out 
  #defining rgb_logts
  #if eval_type == 'rgb' or eval_type == 'rgb600':
  model_logits = rgb_logits
  #elif eval_type == 'flow':
    #model_logits = flow_logits
  #with default flags, the 2-stream model is built and used for prediction!
  #else:
    #RBG and flow stream concatenated for eval_type = 'joint'
    #model_logits = rgb_logits + flow_logits

  #this makes the prediction
  #can probably remove this if not using joint
  model_predictions = tf.nn.softmax(model_logits)


  #opens tf session, loads pre-trained checkpoints into tf session and pass sample into the 
  #model for prediction
  with tf.Session() as sess:
    feed_dict = {}

    #restores appropriate checkpoint for eval_types that include rbg
    #creates dictionary to feed as input into the model for prediction
    if eval_type in ['rgb']:
      #restore appropriate checkpoint
      if imagenet_pretrained:
        rgb_saver.restore(sess, _CHECKPOINT_PATHS['rgb_imagenet'])
      else:
        rgb_saver.restore(sess, _CHECKPOINT_PATHS[eval_type])
      tf.logging.info('RGB checkpoint restored')
      #loads the sample RBG np file
      rgb_sample = np.load(_SAMPLE_PATHS['rgb'])
      #logs the shape of the RBG np array
      tf.logging.info('RGB data loaded, shape=%s', str(rgb_sample.shape))
      #creates dictionary feed_dict with key=rgb_input, value=rgb_sample
      feed_dict[rgb_input] = rgb_sample

#flow stream commented out
    #restores appropriate chkpt for eval types that includ flow
    #creates dictionary to feed as input into the model for prediction
    #if eval_type in ['flow', 'joint']:
      #if imagenet_pretrained:
        #flow_saver.restore(sess, _CHECKPOINT_PATHS['flow_imagenet'])
      #else:
        #flow_saver.restore(sess, _CHECKPOINT_PATHS['flow'])
      #tf.logging.info('Flow checkpoint restored')
      #flow_sample = np.load(_SAMPLE_PATHS['flow'])
      #tf.logging.info('Flow data loaded, shape=%s', str(flow_sample.shape))
      #feed_dict[flow_input] = flow_sample

#runs the opperations and evaluates tensors in [model_logits, model_predictions], 
#substituting the values in feed_dict for the corresponding input values
    out_logits, out_predictions = sess.run(
        [model_logits, model_predictions],
        feed_dict=feed_dict)

    out_logits = out_logits[0] #logits
    out_predictions = out_predictions[0] #prediction (softmax)
    #sorts predictions in order
    sorted_indices = np.argsort(out_predictions)[::-1]

    print('Norm of logits: %f' % np.linalg.norm(out_logits))
    print('\nTop classes and probabilities')
    #prints top 20 classes in descending order of predictions
    for index in sorted_indices[:20]:
      print(out_predictions[index], out_logits[index], kinetics_classes[index])

#execute the code
if __name__ == '__main__':
  tf.app.run(main)
