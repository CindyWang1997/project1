"""
Source Code for Homework 3 of ECBM E4040, Fall 2016, Columbia University

Instructor: Prof. Zoran Kostic

This code is based on
[1] http://deeplearning.net/tutorial/logreg.html
[2] http://deeplearning.net/tutorial/mlp.html
[3] http://deeplearning.net/tutorial/lenet.html
"""
import numpy

import theano
import theano.tensor as T
from theano.tensor.signal import downsample

from hw3_utils import shared_dataset, load_data
from hw3_nn import LogisticRegression, HiddenLayer, LeNetConvPoolLayer, train_nn

#Problem 1
#Implement the convolutional neural network architecture depicted in HW3 problem 1
#Reference code can be found in http://deeplearning.net/tutorial/code/convolutional_mlp.py
def test_lenet():

#Problem 2.1
#Write a function to add translations
def translate_image():
#Implement a convolutional neural network with the translation method for augmentation
def test_lenet_translation():


#Problem 2.2
#Write a function to add roatations
def rotate_image():
#Implement a convolutional neural network with the rotation method for augmentation
def test_lenet_rotation():

#Problem 2.3
#Write a function to flip images
def flip_image():
#Implement a convolutional neural network with the flip method for augmentation
def test_lenet_flip():
    
    
#Problem 2.4
#Write a function to add noise, it should at least provide Gaussian-distributed and uniform-distributed noise with zero mean
def noise_injection():
#Implement a convolutional neural network with the augmentation of injecting noise into input
def test_lenet_inject_noise_input():
    
#Problem 3 
#Implement a convolutional neural network to achieve at least 80% testing accuracy on CIFAR-dataset
def MY_lenet():

#Problem4
#Implement the convolutional neural network depicted in problem4 
def MY_CNN():


