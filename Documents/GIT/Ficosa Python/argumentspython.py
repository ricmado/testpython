#!/usr/bin/python

import sys
import os

print 'Number of arguments:', len(sys.argv), 'arguments.'
print 'Argument List:', str(sys.argv)
print 'Solo el argumento 1:', sys.argv[1]
if not os.path.exists(sys.argv[1]):
    os.makedirs(sys.argv[1]/desdepython)
