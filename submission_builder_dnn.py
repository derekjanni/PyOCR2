# neural net 



# sklearn models
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn import linear_model
from sklearn.naive_bayes import BernoulliNB
from sklearn.naive_bayes import MultinomialNB

# wow even more sklearn stuff
from sklearn.preprocessing import scale
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.grid_search import GridSearchCV

# sklearn metrics
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import roc_curve 
from sklearn.metrics import auc
from sklearn.metrics import classification_report
from sklearn.learning_curve import learning_curve
from sklearn.cross_validation import cross_val_score
from sklearn.cross_validation import train_test_split

# graphs
import matplotlib.pyplot as plt
import seaborn as sns

# images
from scipy.ndimage import convolve, rotate
from skimage.feature import hog
from skimage import draw, data, io, segmentation, color, exposure
from skimage.measure import regionprops
from skimage.filters import threshold_otsu
from skimage.transform import resize 
from skimage.transform import warp 
from PIL import Image

# basics
import pickle
import pandas as pd
import numpy as np
import math
#import cv2
import glob 

def load_data(size):
    files = glob.glob("/users/derekjanni/pyocr/train/*")
    X = []
    for i in files:
        img = Image.open(i)
        img = img.convert("L")
        img = img.resize((size,size))
        image = np.asarray(img).astype('int32')
        image.setflags(write=True)
        thresh = threshold_otsu(image)
        binary = image > thresh
        X.append(binary)

    df = pd.read_csv('trainLabels.csv', header=0)
    Y = np.asarray(df['Class'])
    X = np.asarray(X)
    LE = LabelEncoder()
    Y  = np.asarray(LE.fit_transform(Y)).astype(np.int32)
    return X, Y, LE

def get_hog(img):
    """
    Returns HOG representation of image from my file directory with corresponding index i
    """
    img = Image.open('/users/derekjanni/pyocr/test/'+ str(i) + '.Bmp')
    img = img.convert("L")
    img = img.resize((50,50))
    image = np.asarray(img)
    image.setflags(write=True)
    thresh = threshold_otsu(image)
    binary = image > thresh
    fd, hog_image = hog(binary, orientations=10, pixels_per_cell=(5, 5), cells_per_block=(2, 2), visualise=True)
    return exposure.rescale_intensity(hog_image, in_range=(0, 0.9))

def get_test_img(i, size):
    """
    Returns image from my file directory with corresponding index i
    """
    img = Image.open('/users/derekjanni/pyocr/test/'+ str(i) + '.Bmp')
    img = img.convert("L")
    img = img.resize((50,50))
    image = np.asarray(img)
    image.setflags(write=True)
    thresh = threshold_otsu(image)
    binary = image > thresh
    return binary

def nudge_dataset(X, Y, size):
    """
    This produces a dataset 5 times bigger than the original one,
    by moving the (size x size) images around by 1px to left, right, down, up
    """

    direction_vectors = [
        [[0, 1, 0],
         [0, 0, 0],
         [0, 0, 0]],

        [[0, 0, 0],
         [1, 0, 0],
         [0, 0, 0]],

        [[0, 0, 0],
         [0, 0, 1],
         [0, 0, 0]],

        [[0, 0, 0],
         [0, 0, 0],
         [0, 1, 0]]]

    shift = lambda x, w: convolve(x.reshape(50,50), mode='constant',
                                  weights=w).ravel()
    #add nudged data
    X = np.concatenate([X] +
                       [np.apply_along_axis(shift, 1, X, vector)
                        for vector in direction_vectors])
    Y = np.concatenate([Y for _ in range(5)], axis=0)
    return X, Y
  
size = 50
X, Y, LE = load_data(size)
X = X.reshape(-1, 1, size, size)
#nudge dataset improves performance: test and see!
X_train, Y_train = X[:4000], Y[:4000]
X_test, Y_test = X[4000:], Y[4000:]

with open('char_data_cnn.pkl', 'r') as infile:
    data = pickle.load(infile)
    X_train, Y_train, X_test, Y_test = data[0], data[1], data[2], data[3]

Y_train
print X.shape
X_train, X_test = X_train.astype(np.float32), X_test.astype(np.float32)
Y_train = LE.fit_transform(Y_train).astype(np.int32)
Y_test = LE.fit_transform(Y_test).astype(np.int32)
#X_train, Y_train = nudge_dataset(X_train, Y_train, size)

#neural net & params
from lasagne.layers import DenseLayer
from lasagne.layers import InputLayer
from lasagne.layers import DropoutLayer
from lasagne.nonlinearities import softmax, sigmoid, tanh
from lasagne.updates import nesterov_momentum
from nolearn.lasagne import NeuralNet
from lasagne import layers

model = NeuralNet(
    layers=[
        ('input', layers.InputLayer),
        ('conv1', layers.Conv2DLayer),
        ('pool1', layers.MaxPool2DLayer),
        ('conv2', layers.Conv2DLayer),
        ('pool2', layers.MaxPool2DLayer),
        ('conv3', layers.Conv2DLayer),
        ('pool3', layers.MaxPool2DLayer),
        ('hidden4', layers.DenseLayer),
        ('hidden5', layers.DenseLayer),
        ('output', layers.DenseLayer),
        ],

    input_shape=(None, 1, size, size),
    conv1_num_filters=128, conv1_filter_size=(8, 8), pool1_pool_size=(8, 8),
    conv2_num_filters=64, conv2_filter_size=(4, 4), pool2_pool_size=(4, 4),
    conv3_num_filters=32, conv3_filter_size=(2, 2), pool3_pool_size=(2, 2),
    hidden4_num_units=1000,
    hidden5_num_units=1000,
    output_num_units=62, 
    output_nonlinearity=softmax,

    update_learning_rate=0.01,
    update_momentum=0.9,

    regression=False,
    max_epochs=250,
    verbose=1,
    )

print 'Fitting...'
model.fit(X_train, Y_train)

print "Predicting..."
Y_pred = model.predict(X_test)
Y_pred = LE.inverse_transform(Y_pred)
Y_test = LE.inverse_transform(Y_test)

y1 = LE.inverse_transform(model.predict(X_train))
y2 = LE.inverse_transform(Y_train)
print classification_report(y2, y1)

print classification_report(Y_test, Y_pred)

with open('char2string_DNN.pkl', 'w') as outfile:
    pickle.dump([model, LE], outfile)

'''
X_sub = np.asarray([get_test_img(i, size) for i in range(6284, 12504)])
Y_sub = model.predict(X_sub)

print LE.inverse_transform(Y_sub[:20])
# create submission output
with open('submission.csv', 'w') as outfile:
    outfile.write('ID,Class\n')
    for i in range(len(Y_sub)):
        outfile.write(str(i+6284) + ','+ Y_sub[i] +'\n')'''
print "-------DONE-------"
