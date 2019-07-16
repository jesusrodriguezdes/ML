#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 18:34:25 2019

@author: jesusrodriguez
"""

import numpy as np

def randomization(n):
    
    x = np.random.random([n,1])
    return x



def operations(h,w):
    
    A = np.random.random([h,w])
    B = np.random.random([h,w])
    s = A + B
    
    return (A,B,s)

breakpoint()
def norm(A,B):
   
    return (np.linalg.norm(A+B))



