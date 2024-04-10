# What is torch.nn really?



# MNIST data setup
from pathlib import Path
import requests

DATA_PATH = Path("data")
PATH = DATA_PATH / "mnist"

PATH.mkdir(parents=True, exist_ok=True)

URL = "https://github.com/pytorch/tutorials/raw/main/_static/"
FILENAME = "mnist.pkl.gz"

if not (PATH / FILENAME).exists():
    content = requests.get(URL + FILENAME).content
    (PATH / FILENAME).open("wb").write(content)

# This dataset has been stored using pickle, a python-specific format for serializing data
import pickle
import gzip

with gzip.open((PATH / FILENAME).as_posix(), "rb") as f:
    ((x_train, y_train), (x_valid, y_valid), _) = pickle.load(f, encoding="latin-1")

import numpy as np

# shape of x_train

import torch

x_train, y_train, x_valid, y_valid = map(
    torch.tensor,
    (x_train, y_train, x_valid, y_valid)
)

n, c = x_train.shape
#print(x_train, y_train)
#print(x_train.shape)
#print(y_train.min(), y_train.max())



# Neural net from scratch without `torch,nn`
import math

# Xavier initialisation by multiplying with `1 / sqrt(n)`
weights = torch.randn(784, 10) / math.sqrt(784)
weights.requires_grad_()
bias = torch.randn(10, requires_grad=True)


def log_softmax(x):
    return x - x.exp().sum(-1).log().unsqueeze(-1)

def model(xb):
    return log_softmax(xb @ weights + bias)

bs = 64 # batch size

xb = x_train[0:bs] # a mini batch from x
preds = model(xb)
#print(preds[0], preds.shape)


# implement negative log-likelihood
def nll(input, target):
    return -input[range(target.shape[0]), target].mean()

loss_func = nll

yb = y_train[0:bs]
#print(loss_func(preds, yb))


# implement a function to calculate the accuracy of the model
def accuracy(out, yb):
    preds = torch.argmax(out, dim=1)
    return (preds == yb).float().mean()

#print(accuracy(preds, yb))

lr = torch.tensor(0.5) # learning rate
epochs = 2 # how many epochs to train for

for epoch in range(epochs):
    for i in range((n - 1) // bs + 1):
        start_i = i * bs
        end_i = start_i + bs
        xb = x_train[start_i:end_i]
        yb = y_train[start_i:end_i]
        pred = model(xb)
        loss = loss_func(pred, yb)

        loss.backward()
        with torch.no_grad():
            weights -= weights.grad * lr
            bias -= bias.grad * lr
            weights.grad.zero_()
            bias.grad.zero_()


# check the loss and accuracy
#print(loss_func(model(xb), yb), accuracy(model(xb), yb))


# Using torch.nn.Functional
import torch.nn.functional as F

loss_func = F.cross_entropy

def model(xb):
    return xb @ weights + bias

# check the loss and accuracy
#print(loss_func(model(xb), yb), accuracy(model(xb), yb))


# Refactor using nn.Module
from torch import nn

class Mnist_Logistic(nn.Module):
    def __init__(self):
        super().__init__()
        self.weights = nn.Parameter(torch.randn(784, 10) / math.sqrt(784))
        self.bias = nn.Parameter(torch.zeros(10))

    def forward(self, xb):
        return xb @ self.weights + self.bias

# instantiate model
model = Mnist_Logistic()

# Pytorch will call our `forward` method autematically
#print(loss_func(model(xb), yb))


def fit():
    for epoch in range(epochs):
        for i in range((n - 1) // bs + 1):
            start_i = i * bs
            end_i = start_i + bs
            xb = x_train[start_i:end_i]
            yb = y_train[start_i:end_i]
            loss = loss_func(model(xb), yb)
            loss.backward()
            with torch.no_grad():
                for p in model.parameters():
                    p -= p.grad * lr
                model.zero_grad()


fit()

#print(loss_func(model(x_train), y_train))


# Refactor using nn.Linear
class Mnist_Logistic(nn.Module):
    def __init__(self):
        super().__init__()
        self.lin = nn.Linear(784, 10)

    def forward(self, xb):
        return self.lin(xb)

model = Mnist_Logistic()
#print(loss_func(model(x_train), y_train))

fit()
#print(loss_func(model(x_train), y_train))


# Refactor using torch.optim
from torch import optim

def get_model():
    model = Mnist_Logistic()
    return model, optim.SGD(model.parameters(), lr=lr)

model, opt = get_model()
#print(loss_func(model(x_train), y_train))

for epoch in range(epochs):
    for i in range((n-1) // bs + 1):
        start_i = i * bs
        end_i = start_i + bs
        xb = x_train[start_i:end_i]
        yb = y_train[start_i:end_i]
        loss = loss_func(model(xb), yb)
        loss.backward()
        with torch.no_grad():
            opt.step()
            opt.zero_grad()

#print(loss_func(model(x_train), y_train))


# Refactor using Dataset
from torch.utils.data import TensorDataset

train_ds = TensorDataset(x_train, y_train)

model, opt = get_model()

for epoch in range(epochs):
    for i in range((n-1) // bs + 1):
        xb, yb = train_ds[i*bs:i*bs+bs]
        pred = model(xb)
        loss = loss_func(pred, yb)
        loss.backward()
        opt.step()
        opt.zero_grad()


#print(loss_func(model(x_train), y_train))



# Refactor using DataLoader
from torch.utils.data import DataLoader

# `DataLoader` is responsible for managing batches
# and makes it easier to iterate over batches
train_ds = TensorDataset(x_train, y_train)
train_dl = DataLoader(train_ds, batch_size=bs)


model, opt = get_model()

for epoch in range(epochs):
    for xb, yb in train_dl:
        pred = model(xb)
        loss = loss_func(pred, yb)
        loss.backward()
        opt.step()
        opt.zero_grad()

print(loss_func(model(x_train), y_train))


# Add validation
