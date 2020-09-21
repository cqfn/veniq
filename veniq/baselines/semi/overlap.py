
# The MIT License (MIT)
#
# Copyright (c) 2020 Veniq
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from itertools import combinations
from typing import List
import operator

MIN_OVERLAP = 0.1


def is_overlap(a: List[int], b: List[int]):
    """
    Checks whether 2 opportunities are overlapping

    :param a: array of 2 elements, the first is start statements number,
    the second is end statements number
    :param b: array of 2 elements, the first is start statements number,
    the second is end statements number

    :return: True if it is an overlap, False if it is not
    """

    a_LoC = abs(a[1] - a[0])
    b_LoC = abs(b[1] - b[0])
    overlap = len(set(range(a[0], a[1] + 1)) & set(range(b[0], b[1] + 1)))
    overlap_index = overlap / float(max(a_LoC, b_LoC))
    if overlap_index >= MIN_OVERLAP:
        return True
    else:
        return False
