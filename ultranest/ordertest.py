#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

This implements the same idea as https://arxiv.org/abs/2006.03371
except their KS test is problematic because the variable (insertion rank)
is not continuous. Instead, this implements a Mann-Whitney-Wilcoxon
U test, which also is in practice more sensitive than the KS test.
A highly efficient implementation is achieved by keeping only
a histogram of the insertion ranks and comparing those
to expectations from a uniform distribution.

To quantify the convergence of a run, one route is to apply this test
at the end of the run. Another approach is to reset the counters every
time the test exceeds a z-score of 3 sigma, and report the run lengths,
which quantify how many iterations nested sampling was able to proceed
without detection of a insertion order problem.

"""

from __future__ import print_function, division
import numpy as np

def infinite_U_zscore(sample, B):
	N = len(sample)
	return ((sample + 0.5).sum() - N * B * 0.5) / ((N / 12.0)**0.5 * B)

class UniformOrderAccumulator():
    """
    Store ranks (1 to N), with nsize allowed to vary, for comparison
    with a random rank.
    """
    def __init__(self, N):
        self.histogram = np.zeros(N, dtype=np.uint32)
        self.U = 0.0

    def reset(self):
        """Set all counts to zero. """
        self.histogram[:] = 0
        self.U = 0.0

    def expand(self, N):
        if N > self.histogram.size:
            old_hist = self.histogram
            self.histogram = np.zeros(N, dtype=np.uint32)
            self.histogram[:old_hist.size] = old_hist

    def add(self, rank, N):
        """ add rank out of N to histogram. """
        if not 0 <= rank <= N:
            raise ValueError("order %d out of %d invalid" % (rank, N))
        if N >= self.histogram.size:
            self.expand(N + 1)
        self.U += (rank + 0.5) / N
        self.histogram[rank] += 1
        return self
    
    @property
    def zscore(self):
        """ Mann-Whitney-Wilcoxon U test z-score, against a uniform distribution. """
        N = self.histogram.sum()
        if N == 0:
            return 0.0
        m_U = N * 0.5
        sigma_U_corr = (N / 12.0)**0.5
        return (self.U - m_U) / sigma_U_corr

    def __len__(self):
        return self.histogram.sum()
