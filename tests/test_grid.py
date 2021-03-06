# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2018, TU Wien
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
Tests for grid generation
'''

from ecmwf_models.grid import ERA_RegularImgGrid, get_grid_resolution, ERA_IrregularImgGrid
import numpy as np

def test_ERA_regular_grid():
    reg_grid = ERA_RegularImgGrid(0.3, 0.3)
    assert np.unique(reg_grid.activearrlat).size == 601
    assert np.unique(reg_grid.activearrlon).size == 1200
    assert get_grid_resolution(reg_grid.activearrlat,
                               reg_grid.activearrlon) == (0.3, 0.3)


def test_ERA_irregular_grid():
    # we test this with a regular grid, because it's easier
    lon = np.arange(0, 360 - 1. / 2, 1.)
    lat = np.arange(90, -1 * 90 - 1. / 2, -1 * 1.)
    lons, lats = np.meshgrid(lon, lat)

    grid = ERA_IrregularImgGrid(lons, lats)

    assert grid == ERA_RegularImgGrid(1.,1.)
