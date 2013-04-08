import math

def mean(li):
    """
    Calculate mean of a list.

    >>> mean([0.5,2.0,3.5])
    2.0
    >>> mean([])
    """
    if li:
        return sum(li) / len(li)
    return None

def percentile(li, pc):
    """
    Calculate percentiles of a list.

    >>> li = [0,1,2,3,4,5,6,7,8,9,10]
    >>> percentile(li, 0.5)
    5
    >>> percentile(li, 0.9)
    9
    >>> percentile(li, 1.0)
    10
    >>> percentile(li, 0.0)
    0
    >>> percentile([], 0.5)

    :param list li: data points
    :param float pc: percentile from 0.0 to 1.0
    """
    if not li:
        return None
    k = (len(li)-1) * pc
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return li[int(k)]
    d0 = li[int(f)] * (c-k)
    d1 = li[int(c)] * (k-f)
    return d0 + d1

def stddev(li, mean):
    """
    Calculate the standard deviation of a set of data.

    >>> stddev([3, 3.5, 4], 3.5)
    5.0
    """
    if not li:
        return None
    return math.sqrt(sum(x*x for x in li) - mean*mean)
