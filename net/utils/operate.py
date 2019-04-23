import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import numpy as np
from torch.autograd import Variable


def my_softmax(input, axis=1):
	trans_input = input.transpose(axis, 0).contiguous()
	soft_max_1d = F.softmax(trans_input)
	return soft_max_1d.transpose(axis, 0)


def get_offdiag_indices(num_nodes):
	ones = torch.ones(num_nodes, num_nodes)
	eye = torch.eye(num_nodes, num_nodes)
	offdiag_indices = (ones - eye).nonzero().t()
	offdiag_indices_ = offdiag_indices[0] * num_nodes + offdiag_indices[1]
	return offdiag_indices, offdiag_indices_


def gumbel_softmax(logits, tau=1, hard=False, eps=1e-10):
	y_soft = gumbel_softmax_sample(logits, tau=tau, eps=eps)
	if hard:
		shape = logits.size()
		_, k = y_soft.data.max(-1)
		y_hard = torch.zeros(*shape)
		if y_soft.is_cuda:
			y_hard = y_hard.cuda()
		y_hard = y_hard.zero_().scatter_(-1, k.view(shape[:-1] + (1,)), 1.0)
		y = Variable(y_hard - y_soft.data) + y_soft
	else:
		y = y_soft
	return y


def gumbel_softmax_sample(logits, tau=1, eps=1e-10):
	gpu_id = logits.get_device()
	gumbel_noise = sample_gumbel(logits.size(), eps=eps)
	gumbel_noise = gumbel_noise.cuda(gpu_id)
	y = logits + gumbel_noise
	return my_softmax(y/tau, axis=-1)


def sample_gumbel(shape, eps=1e-10):
	uniform = torch.rand(shape).float()
	return -torch.log(eps-torch.log(uniform+eps))


def encode_onehot(labels):
    classes = set(labels)
    classes_dict = {c: np.identity(len(classes))[i, :] for i, c in enumerate(classes)}
    labels_onehot = np.array(list(map(classes_dict.get, labels)), dtype=np.int32)
    return labels_onehot