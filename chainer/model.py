import numpy
 
import chainer
from chainer import cuda
import chainer.functions as F
import chainer.links as L
 
import ipdb
 
class Generator(chainer.Chain):
    def __init__(self, n_hidden, bottom_width=3, ch=512, wscale=0.02):
        super(Generator, self).__init__()
        self.n_hidden = n_hidden
        self.ch = ch
        self.bottom_width = bottom_width
 
        with self.init_scope():
            w = chainer.initializers.Normal(wscale)
            self.l0 = L.Linear(in_size=n_hidden, out_size=bottom_width*bottom_width*ch, initialW=w)
 
            self.dc1 = L.Deconvolution2D(in_channels=ch, out_channels=ch//2, ksize=2, stride=2, pad=1, initialW=w)
            self.dc2 = L.Deconvolution2D(in_channels=ch//2, out_channels=ch//4, ksize=2, stride=2, pad=1, initialW=w)
            self.dc3 = L.Deconvolution2D(in_channels=ch//4, out_channels=ch//8, ksize=2, stride=2, pad=1, initialW=w)
            self.dc4 = L.Deconvolution2D(in_channels=ch//8, out_channels=1, ksize=3, stride=3, pad=1, initialW=w)
 
            # self.bn0 = L.BatchNormalization(size=self.bottom_width*self.bottom_width*self.ch)
            self.bn1 = L.BatchNormalization(size=ch)
            self.bn2 = L.BatchNormalization(size=ch//2)
            self.bn3 = L.BatchNormalization(size=ch//4)
            self.bn4 = L.BatchNormalization(size=ch//8)
 
    def make_hidden(self, batchsize):
        return numpy.random.uniform(-1, 1, (batchsize, self.n_hidden, 1, 1)).astype(numpy.float32)
 
    def __call__(self, z):
        h0 = self.l0(z)
        # h0.shape = (-1, 73728)
        h1 = F.reshape(h0, (len(z), self.ch, self.bottom_width, self.bottom_width))
        # h1.shape = (-1, 512, 12, 12)
        h2 = F.relu(self.bn1(h1))
        # h1.shape = (-1, 512, 12, 12)
        h3 = F.relu(self.bn2(self.dc1(h2)))
        h4 = F.relu(self.bn3(self.dc2(h3)))
        h5 = F.relu(self.bn4(self.dc3(h4)))
        x = F.sigmoid(self.dc4(h5))
        # x = F.tanh(self.dc4(h))
 
        return x
 
 
class Discriminator(chainer.Chain):
    def __init__(self, bottom_width=3, ch=512, wscale=0.02):
        w = chainer.initializers.Normal(wscale)
        super(Discriminator, self).__init__()
        with self.init_scope():
 
            self.c0 = L.Convolution2D(in_channels=1, out_channels=64, ksize=3, stride=3, pad=1, initialW=w)
            self.c1 = L.Convolution2D(in_channels=ch//8, out_channels=128, ksize=2, stride=2, pad=1, initialW=w)
            self.c2 = L.Convolution2D(in_channels=ch//4, out_channels=256, ksize=2, stride=2, pad=1, initialW=w)
            self.c3 = L.Convolution2D(in_channels=ch//2, out_channels=512, ksize=2, stride=2, pad=1, initialW=w)
 
            # self.l4 = L.Linear(in_size=bottom_width*bottom_width*ch, out_size=1, initialW=w)
            self.l4 = L.Linear(in_size=None, out_size=1, initialW=w)
 
            # self.bn0 = L.BatchNormalization(size=ch//8, use_gamma=False)
            self.bn1 = L.BatchNormalization(size=ch//4, use_gamma=False)
            self.bn2 = L.BatchNormalization(size=ch//2, use_gamma=False)
            self.bn3 = L.BatchNormalization(size=ch//1, use_gamma=False)
 
 
    def __call__(self, x):
        #x.shape = (-1, 1, 256, 256)
        h0 = F.leaky_relu(self.c0(x))
        #h0.shape = (-1, 64, 86, 86)
        h1 = F.leaky_relu(self.bn1(self.c1(h0)))
        #h1.shape = (-1, 128, 44, 44)
        h2 = F.leaky_relu(self.bn2(self.c2(h1)))
        #h2.shape = (-1, 256, 23, 23)
        h3 = F.leaky_relu(self.bn3(self.c3(h2)))
        #h3.shape = (-1, 512, 12, 12)
        y = self.l4(h3)
 
        return y