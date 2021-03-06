import torch
import torchvision
import torchaudio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import random
import pickle
import tqdm
from tqdm import tqdm


import warnings
import glob

from metrics import *
from transforms import *

torchaudio.set_audio_backend("sox_io") 
os.environ["IMAGEIO_FFMPEG_EXE"] = "/home/sgurram/anaconda3/bin/ffmpeg"
warnings.filterwarnings("ignore")

def get_wave(path):
    wave, samp_freq = torchaudio.load(path)
    wave = wave.mean(dim=0) #avg both channels to get single audio strean
    return wave, samp_freq


def get_mfcc(wave, samp_freq=16000):
    return np.array((torchaudio.transforms.MFCC(sample_rate=samp_freq)(wave.unsqueeze(0))).mean(dim=0))


def get_mel_spec(wave, samp_freq=16000):
    wave = torch.unsqueeze(wave, 0)
    return (torchaudio.transforms.MelSpectrogram(sample_rate=samp_freq)(wave))[0,:,:]


def get_log_mel_spec(wave, samp_freq=16000):
    wave = torch.unsqueeze(wave, 0)
    spec = torchaudio.transforms.MelSpectrogram()(wave)
    return spec.log2()[0,:,:]


def pad_spec(spec, pad_len=2040):
    to_pad = pad_len - spec.shape[-1] 
    if to_pad > 0:
        return torch.nn.functional.pad(spec, (0,to_pad,0,0))
    return spec[:,:pad_len]


def augment(sample, wave_transform, spec_transform, threshold, crop=True, fixed=True):
    wave = wave_transform(threshold)(sample)
    wave = wave.type(torch.FloatTensor)
    spec = get_log_mel_spec(wave)

    #suppressing "assert mask_end - mask_start < mask_param" for time/freq masks
    # try:
    #     return spec_transform(threshold)(SpecFixedCrop(threshold)(spec[15:]))
    # except:
    #     # return SpecFixedCrop(threshold)(spec)
    #     return spec_transform(threshold)(SpecFixedCrop(threshold)(spec[15:]))

    spec = pad_spec(spec)

    if crop and fixed:
        spec = spec_transform(threshold)(SpecFixedCrop(threshold)(spec))
    elif crop:
        spec = spec_transform(threshold)(SpecRandomCrop(threshold)(spec))
    else:
        spec = spec_transform(threshold)(spec)

    spec[torch.isinf(spec)] = 0
    return spec

def get_augmented_views(path, identity=False):
    sample, _ = get_wave(path)
    threshold1 = random.uniform(0.0, 0.5)
    threshold2 = random.uniform(0.0, 0.5)

    if not identity:

        wave1 = WaveIdentity
        spec1 = SpecIdentity

        # wave1 =  random.choice(list(wave_transforms.values()))
        # spec1 =  random.choice(list(spec_transforms.values()))

        wave2 =  random.choice(list(wave_transforms.values()))
        spec2 =  random.choice(list(spec_transforms.values()))
        
    else:
        wave1 = WaveIdentity
        wave2 = WaveIdentity

        spec1 = SpecIdentity
        spec2 = SpecIdentity

    # print(wave1, spec1)
    # print(wave2, spec2)

    return augment(sample, wave1, spec1, threshold1, crop=False), augment(sample, wave2, spec2, threshold2, crop=False)

def get_temporal_permutes(path):
    sample, _ = get_wave(path)
    wave = WaveIdentity
    spec1 = SpecIdentity
    spec2 = SpecPermutes
    threshold = random.uniform(0.0, 0.5)

    # Return (anchor, permutes), anchor is single sample, permutes is a list of samples
    return augment(sample, wave, spec2, threshold, crop=False)
    
def get_temporal_shuffle(path):
    #assume num_segments = 3
    # shuffle_idx = random.randint(0, 23)
    shuffle_idx = random.randint(1, 5)
    permutes = get_temporal_permutes(path)

    #permutes[0] is in-order sample, so anchor, shuffle_idx-1 to range [1, 5] -> [0, 4]
    return permutes[0], permutes[shuffle_idx], shuffle_idx-1

def get_supervised_data(path):
    spec = pad_spec(get_augmented_views(path, identity=True)[0])
    label = int((path.split('/')[4]).split('_')[0]) - 1
    return spec, label


if __name__ == '__main__':
    for _ in tqdm(range(1)):
        filepath = "/{dir}/kinetics_audio/train/25_riding a bike/0->--JMdI8PKvsc.wav".format(dir = data)
        # view1, view2, _, _ = get_augmented_views(filepath)
        anchor, shuffle, label = get_temporal_shuffle(filepath)
 
    #     view1, view2 = permutes[5], permutes[10]
    
    # print(permutes.shape)
    # f = plt.figure()
    # f.add_subplot(1, 2, 1)
    # plt.imshow(view1)

    # f.add_subplot(1, 2, 2)
    # plt.imshow(view2)
    # plt.savefig("Desktop/log_mel_two_views.png")


