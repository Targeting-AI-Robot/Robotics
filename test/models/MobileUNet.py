import tensorflow as tf
from tensorflow.keras.layers import Conv2D, BatchNormalization, ReLU, SeparableConv2D, Conv2DTranspose, MaxPool2D

class ConvBlock(tf.keras.layers.Layer):
	"""
	Builds the conv block for MobileNets
	Apply successivly a 2D convolution, BatchNormalization ReLU
	"""
	# Skip pointwise by setting num_outputs=Non
	def __init__(self, n_filters, kernel_size=[1, 1]):
		super(ConvBlock, self).__init__()
		self.conv2d = Conv2D(n_filters, kernel_size=kernel_size, padding='same', activation=None)
		self.batchnorm = BatchNormalization(fused=True)
		self.relu = ReLU()

	def call(self, x):
		x = self.conv2d(x)
		x = self.batchnorm(x)
		x = self.relu(x)
		return x


class DepthwiseSeparableConvBlock(tf.keras.layers.Layer):
	"""
	Builds the Depthwise Separable conv block for MobileNets
	Apply successivly a 2D separable convolution, BatchNormalization ReLU, conv, BatchNormalization, ReLU
	"""
	# Skip pointwise by setting num_outputs=None
	def __init__(self, n_filters, kernel_size=[3, 3]):
		super(DepthwiseSeparableConvBlock, self).__init__()
		self.separableconv2d = SeparableConv2D(n_filters, depth_multiplier=1, kernel_size=kernel_size, padding='same', activation=None)
		self.batchnorm1 = BatchNormalization(fused=True)
		self.relu = ReLU()
		self.conv2d = Conv2D(n_filters, kernel_size=[1, 1], padding='same', activation=None)
		self.batchnorm2 = BatchNormalization(fused=True)

	def call(self, x):
		x = self.separableconv2d(x)
		x = self.batchnorm1(x)
		x = self.relu(x)
		x = self.conv2d(x)
		x = self.batchnorm2(x)
		x = self.relu(x)
		return x


class ConvTransposeBlock(tf.keras.layers.Layer):
	"""
	Basic conv transpose block for Encoder-Decoder upsampling
	Apply successivly Transposed Convolution, BatchNormalization, ReLU nonlinearity
	"""
	def __init__(self, n_filters, kernel_size=[3, 3]):
		super(ConvTransposeBlock, self).__init__()
		self.conv2dtranspose = Conv2DTranspose(n_filters, kernel_size=kernel_size, strides=[2, 2], padding='same', activation=None)
		self.batchnorm = BatchNormalization()
		self.relu = ReLU()

	def call(self, x):
		x = self.conv2dtranspose(x)
		x = self.batchnorm(x)
		x = self.relu(x)
		return x


class DownSamplingBlock(tf.keras.layers.Layer):
	def __init__(self, n_filters, n):
		super(DownSamplingBlock, self).__init__()
		self.features = []
		for _ in range(n):
			self.features.append(DepthwiseSeparableConvBlock(n_filters))
		self.features.append(MaxPool2D((2, 2), strides=2))

	def call(self, x):
		for layer in self.features:
			x = layer(x)
		return x


class UpSamplingBlock(tf.keras.layers.Layer):
	def __init__(self, n_filters, n, is_skip, out_depthwise_ch):
		super(UpSamplingBlock, self).__init__()
		self.is_skip = is_skip
		self.features = []
		self.features.append(ConvTransposeBlock(n_filters))
		for _ in range(n):
			self.features.append(DepthwiseSeparableConvBlock(n_filters))
		self.features.append(DepthwiseSeparableConvBlock(out_depthwise_ch))

	def call(self, x1, x2):
		for layer in self.features:
			x1 = layer(x1)
		if self.is_skip:
			diffY = x2.shape[1] - x1.shape[1]
			diffX = x2.shape[2] - x1.shape[2]
			x1 = tf.pad(x1, tf.constant([[0, 0], [diffY, 0], [diffX, 0], [0, 0]]))
			x1 = tf.add(x1, x2)
		return x1


class MobileUNet(tf.keras.Model):
    def __init__(self, num_classes, preset_model="MobileUNet-Skip"):
        super(MobileUNet, self).__init__()
        if preset_model == "MobileUNet":
            self.has_skip = False
        elif preset_model == "MobileUNet-Skip":
            self.has_skip = True
        else:
            raise ValueError("Unsupported MobileUNet model '%s'. This function only supports MobileUNet and MobileUNet-Skip" % (preset_model))

        self.conv_block = ConvBlock(64)
        self.downsampling_block1 = DownSamplingBlock(64, 1)
        self.downsampling_block2 = DownSamplingBlock(128, 2)
        self.downsampling_block3 = DownSamplingBlock(256, 3)
        self.downsampling_block4 = DownSamplingBlock(512, 3)
        self.downsampling_block5 = DownSamplingBlock(512, 3)
        self.upsampling_block1 = UpSamplingBlock(512, 2, self.has_skip, out_depthwise_ch=512)
        self.upsampling_block2 = UpSamplingBlock(512, 2, self.has_skip, out_depthwise_ch=256)
        self.upsampling_block3 = UpSamplingBlock(256, 2, self.has_skip, out_depthwise_ch=128)
        self.upsampling_block4 = UpSamplingBlock(128, 1, self.has_skip, out_depthwise_ch=64)
        self.upsampling_block5 = UpSamplingBlock(64, 1, False, out_depthwise_ch=64)
        self.fc = Conv2D(num_classes, kernel_size=[1, 1], padding='same', activation=None)

    def call(self, inputs):
        #####################
        # Downsampling path #
        #####################
        net = self.conv_block(inputs)

        net = self.downsampling_block1(net)
        skip_1 = net

        net = self.downsampling_block2(net)
        skip_2 = net

        net = self.downsampling_block3(net)
        skip_3 = net

        net = self.downsampling_block4(net)
        skip_4 = net

        net = self.downsampling_block5(net)

        #####################
        #  Upsampling path  #
        #####################
        net = self.upsampling_block1(net, skip_4)

        net = self.upsampling_block2(net, skip_3)

        net = self.upsampling_block3(net, skip_2)

        net = self.upsampling_block4(net, skip_1)

        net = self.upsampling_block5(net, None)

        diffY = inputs.shape[1] - net.shape[1]
        diffX = inputs.shape[2] - net.shape[2]
        paddings = tf.constant([[0, 0], [diffY.value, 0], [diffX.value, 0], [0, 0]])
        net = tf.pad(net, paddings)

        #####################
        #      Softmax      #
        #####################
        net = self.fc(net)
        
        return net
