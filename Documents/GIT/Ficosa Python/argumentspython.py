#!/usr/bin/python

import sys
import os

print 'Number of arguments:', len(sys.argv), 'arguments.'
print 'Argument List:', str(sys.argv)
print 'Solo el argumento 1:', sys.argv[1]
newpath = sys.argv[1]+ 'desdepython'
newpathtwo = r'C:\Users\Administrator\Documents\FolderTest\desdepython' 
if not os.path.exists(newpath):
    os.makedirs(newpath)
