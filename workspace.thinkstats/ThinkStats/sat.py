"""This file contains code used in "Think Stats",
by Allen B. Downey, available from greenteapress.com

Copyright 2010 Allen B. Downey
License: GNU GPLv3 http://www.gnu.org/licenses/gpl.html
"""

import csv
import datetime
import math
import random
import sys

import matplotlib.pyplot as pyplot

import bayes
import correlation
import Cdf
import myplot
import Pmf
import rankit
import thinkstats

def ParseRange(s):
    t = [int(x) for x in s.split('-')]
    return 1.0 * sum(t) / len(t)

def ReadScale(filename='sat_scale.csv', col=2):
    """Reads a CSV file of SAT scales (maps from raw score to standard score).

    Args:
      filename: string filename
      col: which column to start with (0=Reading, 2=Math, 4=Writing)

    Returns:
      list of (raw score, standardize score) pairs
    """
    fp = open(filename)
    reader = csv.reader(fp)
    raws = []
    scores = []

    for t in reader:
        try:
            raw = int(t[col])
            raws.append(raw)
            score = ParseRange(t[col+1])
            scores.append(score)
            print raw, score
        except:
            pass

    raws.sort()
    scores.sort()
    return thinkstats.Interpolator(raws, scores)


def ReadRanks(filename='sat_ranks.csv'):
    """Reads a CSV file of SAT scores.

    Args:
      filename: string filename

    Returns:
      list of (score, number) pairs
    """
    fp = open(filename)
    reader = csv.reader(fp)
    res = []

    for t in reader:
        try:
            score = int(t[0])
            number = int(t[1])
            res.append((score, number))
        except ValueError:
            pass

    return res

def ReadScores(filename='SATPercentileRanks2009.csv'):
    """Reads a CSV file of SAT scores.

    Args:
      filename: string filename

    Returns:
      list of (score, number) pairs
    """
    fp = open(filename)
    reader = csv.reader(fp)
    res = []

    for t in reader:
        try:
            score, number = [int(x) for x in t]
            res.append((score, number))
        except ValueError:
            pass

    return res

def Summarize(pmf):
    mu, var = pmf.Mean(), pmf.Var()
    sigma = math.sqrt(var)
    print 'mu, sigma', mu, sigma
    return mu, sigma

def ApplyLogistic(pmf, inter=-2.5, slope=10):
    mu, sigma = Summarize(pmf)
    new = Pmf.Pmf()
    for val, prob in sorted(pmf.Items()):
        z = inter + slope * StandardScore(val, mu, sigma)
        
        prob_admit = Logistic(z)
        new.Incr(val, prob * prob_admit)

        print val, z, prob_admit

    new.Normalize()
    mu, sigma = Summarize(new)
    return new

def StandardScore(val, mu, sigma):
    return (val-mu) / sigma

def Logistic(z):
    return 1 / (1 + math.exp(-z))

def SummarizeR(r, sigma):
    r2 = r**2
    var = sigma**2

    rmse_without = sigma
    rmse_with = math.sqrt(var * (1 - r2))

    reduction = 1.0 - (rmse_with / rmse_without)
    print 'r, R^2', r, r2
    print 'RMSE (reduction)', rmse_with, reduction

def Logit(p):
    return math.log10(p) - math.log10(1-p)

def ApplyLogit(pmf, denom):
    new = Pmf.Pmf()
    for val, prob in pmf.Items():
        if val > 0 and val < denom:
            x = Logit(val/denom)
            new.Incr(x, prob)
    return new

def ReverseScale(pmf, scale):
    new = Pmf.Pmf()
    for val, prob in pmf.Items():
        raw = scale.Reverse(val)
        new.Incr(raw, prob)
    return new

def SamplePmf(pmf, total, fraction=0.001):
    t = []
    for val, prob in pmf.Items():
        n = int(prob * total * fraction)
        t.extend([val] * n)
    return t

def MakeNormalPlot(ys, root=None, lineoptions={}, **options):
    """Makes a normal probability plot.
    
    Args:
        ys: sequence of values
        lineoptions: dictionary of options for pyplot.plot        
        options: dictionary of options for myplot.Plot
    """
    n = len(ys)
    ys.sort()
    xs = [random.normalvariate(0.0, 1.0) for i in range(n)]
    xs.sort()

    inter, slope = correlation.LeastSquares(xs, ys)
    print 'inter, slope', inter, slope
    x_fit = [-4, 4]
    y_fit = [inter + slope*x for x in x_fit]

    pyplot.clf()
    pyplot.plot(x_fit, y_fit, 'r-')
    pyplot.plot(sorted(xs), sorted(ys), 'b.', markersize=2, **lineoptions)
 
    myplot.Plot(root,
                xlabel = 'Standard normal values',
                legend=False,
                **options)


def ShiftValues(pmf, shift):
    new = Pmf.Pmf()
    for val, prob in pmf.Items():
        if val >= shift:
            x = val - shift
            new.Incr(x, prob)
    return new

def DivideValues(pmf, denom):
    new = Pmf.Pmf()
    for val, prob in pmf.Items():
        if val >= 0:
            x = 1.0 * val / denom
            new.Incr(x, prob)
    return new


def Update(prior, score, shift, max_score, scale):
    raw = scale.Reverse(score) - shift
    evidence = raw, max_score-raw

    updater = bayes.BinomialBayes()
    posterior = updater.Update(prior, evidence)

    return posterior

def ProbBigger(pmf1, pmf2):
    total = 0.0
    for v1, p1 in pmf1.Items():
        for v2, p2 in pmf2.Items():
            if v1 > v2:
                total += p1 * p2
    return total

def main(script):

    SummarizeR(r=0.53, sigma=0.71)

    scale = ReadScale()
    print scale.xs
    print scale.ys
    print scale.Lookup(53)
    print scale.Reverse(800)

    scores = ReadRanks()
    hist = Pmf.MakeHistFromDict(dict(scores))
    total = hist.Total()

    pmf = Pmf.MakePmfFromHist(hist)

    raw = ReverseScale(pmf, scale)
    raw_sample = SamplePmf(raw, total, fraction=0.01)
    MakeNormalPlot(raw_sample, 
                   root='sat_normal',
                   ylabel='Raw scores (math)',)

    print 'raw mean, var', raw.Mean(), raw.Var()

    shift = 0
    raw = ShiftValues(raw, shift=shift)

    max_score = max(raw.Values())

    log = ApplyLogit(raw, denom=max_score)

    prior = DivideValues(raw, denom=max_score)

    low = 720
    high = low+50
    posterior_low = Update(prior, low, shift, max_score, scale)
    posterior_high = Update(prior, high, shift, max_score, scale)

    prob_bigger = ProbBigger(posterior_high, posterior_low)
    print "prob_bigger:", prob_bigger

    cdf1 = Cdf.MakeCdfFromPmf(pmf, 'scaled')
    myplot.Cdfs([cdf1],
               xlabel='score', 
               ylabel='CDF', 
               show=False)

    cdf2 = Cdf.MakeCdfFromPmf(raw, 'raw')
    myplot.Cdfs([cdf2],
               xlabel='score', 
               ylabel='CDF', 
               show=False)

    cdf3 = Cdf.MakeCdfFromPmf(prior, 'prior')

    cdf4 = Cdf.MakeCdfFromPmf(posterior_low, 'posterior %d' % low)
    cdf5 = Cdf.MakeCdfFromPmf(posterior_high, 'posterior %d' % high)

    myplot.Cdfs([cdf4, cdf5],
                xlabel='P', 
                ylabel='CDF', 
                axis=[0.5, 1.0, 0.0, 1.0],
                show=True)



def InferLogit(pmf):
    admitted = ApplyLogistic(pmf)

    cdf1 = Cdf.MakeCdfFromPmf(pmf)
    cdf2 = Cdf.MakeCdfFromPmf(admitted)

    quartiles = cdf2.Percentile(25), cdf2.Percentile(50), cdf2.Percentile(75)
    print 'quartiles', quartiles

    myplot.Cdfs([cdf1, cdf2],
               xlabel='score', 
               ylabel='CDF', 
               show=True)
    
if __name__ == '__main__':
    main(*sys.argv)
