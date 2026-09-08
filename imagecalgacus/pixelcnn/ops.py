# Adapted for inference only from pclucas14/pixel-cnn-pp, commit
# 7cb4436f062fda9b63ecc9e3b75d2c2dcb379931. Modified imports/device handling;
# training, continuous samplers and debug code removed. See LICENSE and THIRD_PARTY.md.
import torch
import torch.nn as nn
import torch.nn.functional as F


def concat_elu(x):
    return F.elu(torch.cat((x, -x), dim=len(x.size()) - 3))


def down_shift(x, pad=None):
    return (nn.ZeroPad2d((0, 0, 1, 0)) if pad is None else pad)(x[:, :, :-1, :])


def right_shift(x, pad=None):
    return (nn.ZeroPad2d((1, 0, 0, 0)) if pad is None else pad)(x[:, :, :, :-1])
