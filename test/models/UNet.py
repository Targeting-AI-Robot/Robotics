import os,time,cv2
import tensorflow as tf
#import tensorflow.contrib.slim as slim
import numpy as np

def ConvBlock(inputs, n_filters, kernel_size=[3, 3]):
    """
    Builds the conv block for UNets
    Apply successivly a 2D convolution, BatchNormalization, ReLU
    """
    conv_layer = tf.keras.layers.Conv2D(n_filters, kernel_size=kernel_size, padding='same')
    batch_norm = tf.keras.layers.BatchNormalization(axis = -1, fused=True)
    
    net = conv_layer(inputs)
    net = tf.keras.activations.relu(net)
    net = batch_norm(net)
    return net

def conv_transpose_block(inputs, n_filters, kernel_size=[3, 3], strides=[2, 2], output_shape=None):
    """
    Basic conv transpose block for Encoder-Decoder upsampling
    Apply successivly Transposed Convolution, BatchNormalization, ReLU
    """
    if output_shape is None:
        output_padding = [strides[0]-1,strides[1]-1]
    else:
        output_padding = [(output_shape[1]+strides[0]-1)%strides[0], (output_shape[2]+strides[1]-1)%strides[1]]
    conv2d_transpose_layer = tf.keras.layers.Conv2DTranspose(n_filters, kernel_size=kernel_size, strides=strides, output_padding=output_padding, padding="same")
    batch_norm = tf.keras.layers.BatchNormalization(axis = -1, fused=True)

    net = conv2d_transpose_layer(inputs)
    net = tf.keras.activations.relu(net)
    net = batch_norm(net)
    return net

def build_unet(inputs, preset_model, num_classes):

    #####################
    # Downsampling path #
    #####################

    strides = (2, 2)
    
    max_pooling = tf.keras.layers.MaxPool2D(pool_size=(2,2), strides=strides, padding="same")
    
    net = ConvBlock(inputs, 64)
    net = ConvBlock(net, 64)
    skip_1 = net

    net = max_pooling(net)
    net = ConvBlock(net, 128)
    net = ConvBlock(net, 128)
    skip_2 = net
    
    net = max_pooling(net)
    net = ConvBlock(net, 256)
    net = ConvBlock(net, 256)
    skip_3 = net

    net = max_pooling(net)
    net = ConvBlock(net, 512)
    net = ConvBlock(net, 512)
    skip_4 = net

    net = max_pooling(net)
    net = ConvBlock(net, 1024)
    net = ConvBlock(net, 1024)

    ####################
    # Upsampling path  #
    ####################

    net = conv_transpose_block(net, 512, strides=strides, output_shape=skip_4.shape)
    net = tf.add(net, skip_4)
    net = ConvBlock(net, 512)
    net = ConvBlock(net, 512)

    net = conv_transpose_block(net, 256, strides=strides, output_shape=skip_3.shape)
    net = tf.add(net, skip_3)
    net = ConvBlock(net, 256)
    net = ConvBlock(net, 256)

    net = conv_transpose_block(net, 128, strides=strides, output_shape=skip_2.shape)
    net = tf.add(net, skip_2)
    net = ConvBlock(net, 128)
    net = ConvBlock(net, 128)

    net = conv_transpose_block(net, 64, strides=strides, output_shape=skip_1.shape)
    net = tf.add(net, skip_1)
    net = ConvBlock(net, 64)
    net = ConvBlock(net, 64)

    #####################
    #      Softmax      #
    #####################
    
    fc_layer = tf.keras.layers.Conv2D(num_classes, kernel_size=[1, 1], padding='same')
    net = fc_layer(net)
    return net
