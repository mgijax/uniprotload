#!/usr/local/bin/python
#
#  makeBucketsDiff.py
###########################################################################
#
#  Purpose:
#
#      This script will compare the old/saved buckets
#      with the new/current buckets and generate output files
#      that display:
#
#          lose Markers
#	   gain Markers
#          in which bucket the lose/gain Markers now reside
#
#  Usage:
#
#      makeBucketsDiff.py
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#          BUCKETDIR
#          BUCKET_PREFIX
#
#  Inputs:
#
#      - Cardinality files (buckets) from the MGI/UniProt comparison.
#        Each file name is prefixed as follows:
#
#        ${BUCKET_PREFIX}.0_1.txt
#        ${BUCKET_PREFIX}.1_0.txt
#        ${BUCKET_PREFIX}.1_1.txt
#        ${BUCKET_PREFIX}.1_N.txt
#        ${BUCKET_PREFIX}.N_1.txt
#        ${BUCKET_PREFIX}.N_N.txt
#
#      - Save files from the previous buckets:
#
#        ${BUCKET_PREFIX}.0_1.txt.save
#        ${BUCKET_PREFIX}.1_0.txt.save
#        ${BUCKET_PREFIX}.1_1.txt.save
#        ${BUCKET_PREFIX}.1_N.txt.save
#        ${BUCKET_PREFIX}.N_1.txt.save
#        ${BUCKET_PREFIX}.N_N.txt.save
#
#  Outputs:
#
#      - Comparison between old bucket vs. new bucket
#        Each file name is prefixed as follows:
#
#        ${BUCKET_PREFIX}.1_1.txt.lose
#        ${BUCKET_PREFIX}.1_1.txt.gain
#
#        ${BUCKET_PREFIX}.1_N.txt.lose
#        ${BUCKET_PREFIX}.1_N.txt.gain
#
#        ${BUCKET_PREFIX}.0_1.txt.lose
#        ${BUCKET_PREFIX}.0_1.txt.gain
#
#        ${BUCKET_PREFIX}.1_0.txt.lose
#        ${BUCKET_PREFIX}.1_0.txt.gain
#
#        ${BUCKET_PREFIX}.N_1.txt.lose
#        ${BUCKET_PREFIX}.N_1.txt.gain
#
#        ${BUCKET_PREFIX}.N_N.txt.lose
#        ${BUCKET_PREFIX}.N_N.txt.gain
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#
#  Assumes:  Nothing
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Initialize variables.
#      2) Open files.
#      3) Create a set of old bucket and a set of new bucket.
#      4) Compare the lose/gain Marker/UniProt ids for each bucket.
#      5) Create output files for each bucket (one for lose, one for gain).
#      7) Close files.
#
#  Notes:  None
#
###########################################################################

import sys 
import os
import string
from sets import Set
import db

B0_1 = '0_1'
B1_0 = '1_0'
B1_1 = '1_1'
B1_N = '1_N'
BN_1 = 'N_1'
BN_N = 'N_N'

BUCKETLIST = [ B0_1, B1_0, B1_1, B1_N, BN_1, BN_N ]

# BUCKETDIR
bucketDir = None

# BUCKET_PREFIX
bucketPrefix = None

# file pointers...one for each bucket in BUCKETLIST
bucketOld = {}
bucketNew = {}
bucketLose = {}
bucketGain = {}

# reads a bucket that contains an MGI ID
# dictionary mapping MGI IDs to Marker Symbol
# looks like:  {MGI ID: [symbol]...}
mgiLookup = {}

#
# Purpose: Initialization
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global bucketDir, bucketPrefix
    global bucketOld, bucketNew
    global bucketLose, bucketGain

    bucketDir = os.getenv('BUCKETDIR')
    bucketPrefix = os.getenv('BUCKET_PREFIX')

    rc = 0

    #
    # Initialize file pointers.
    #
    for i in BUCKETLIST:
        bucketOld[i] = None
        bucketNew[i] = None
        bucketLose[i] = None
        bucketGain[i] = None

    return rc


#
# Purpose: Open files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global bucketOld, bucketNew
    global bucketLose, bucketGain
    global mgiLookup

    #
    # Open the bucket files.
    # Load the ids into a Set (bucketOld[], bucketNew[])
    # Create files for lose, gain (bucketLose[], bucketGain[])
    #
    for i in BUCKETLIST:

        fileOld = bucketDir + '/' + bucketPrefix + '.' + i + '.txt.save'
        fileNew = bucketDir + '/' + bucketPrefix + '.' + i + '.txt'
        fileLose = bucketDir + '/' + bucketPrefix + '.' + i + '.txt.lose'
        fileGain = bucketDir + '/' + bucketPrefix + '.' + i + '.txt.gain'

        try:
            fp = open(fileOld, 'r')
	    bucketList = []
	    for line in fp.readlines():
                tokens = string.split(line[:-1], '\t')
                id = tokens[0]
		if i == B0_1 or string.find(id, 'MGI:') >= 0:
	            bucketList.append(id)
		if string.find(id, 'MGI:') >= 0:
                    symbol = tokens[1]
		    if not mgiLookup.has_key(id):
		        mgiLookup[id] = []
		    mgiLookup[id].append(symbol)
	    fp.close()
	    bucketOld[i] = Set(bucketList)

            fp = open(fileNew, 'r')
	    bucketList = []
	    for line in fp.readlines():
                tokens = string.split(line[:-1], '\t')
                id = tokens[0]
		if i == B0_1 or string.find(id, 'MGI:') >= 0:
	            bucketList.append(id)
		if string.find(id, 'MGI:') >= 0:
                    symbol = tokens[1]
		    if not mgiLookup.has_key(id):
		        mgiLookup[id] = []
		    mgiLookup[id].append(symbol)
	    fp.close()
	    bucketNew[i] = Set(bucketList)

            #
            # Open the lose file.
            #
            bucketLose[i] = open(fileLose, 'w')
            bucketLose[i].write('#\n# LOSE file:  %s\n' % (fileLose))

	    if i != B0_1:
	        bucketLose[i].write('#\n# field 1:  MGI ID\n')
	        bucketLose[i].write('# field 2:  Symbol\n')
	        bucketLose[i].write('# field 3:  what bucket was I in before?\n')
                bucketLose[i].write('#\n# left-hand side of the bucket name is MGI; right-hand side is UniProt\n') 
            else:
	        bucketLose[i].write('#\n# field 1:  UniProt ID\n')

	    bucketLose[i].write('#\n')

            #
            # Open the gain file.
            #
            bucketGain[i] = open(fileGain, 'w')
            bucketGain[i].write('#\n# GAIN file: %s\n' % (fileGain))

	    if i != B0_1:
	        bucketGain[i].write('#\n# field 1:  MGI ID\n')
	        bucketGain[i].write('# field 2:  Symbol\n')
	        bucketGain[i].write('# field 3:  what bucket was I in before?\n')
                bucketGain[i].write('#\n# left-hand side of the bucket name is MGI; right-hand side is UniProt\n') 
            else:
	        bucketGain[i].write('#\n# field 1:  UniProt ID\n')

	    bucketGain[i].write('#\n')

        except:
            print 'Cannot read bucket: ' + fileOld
            print 'Cannot read bucket: ' + fileNew
            print 'Cannot create bucket lose: ' + fileLose
            print 'Cannot create bucket gain: ' + fileGain
            return 1

    return 0


#
# Purpose: Close files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def closeFiles():
    for i in BUCKETLIST:
        bucketLose[i].close();
        bucketGain[i].close();

    return 0


#
# Purpose: Bucket differences between old and new buckets
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def bucketDiff():

    #
    # for each record in bucketOld
    #   find/write set of ids lost
    #   find/write set of ids gained
    #

    for i in BUCKETLIST:

	loseSet = bucketOld[i].difference(bucketNew[i])
	gainSet = bucketNew[i].difference(bucketOld[i])

	bucketLose[i].write('# total number of records: %s\n#\n' % (len(loseSet)))
	bucketGain[i].write('# total number of records: %s\n#\n' % (len(gainSet)))

	for id in loseSet:

	    # determine if this id exists in another bucketNew set
	    otherBucket = ''
	    for j in BUCKETLIST:
		if j == i:
		    continue
                if id in bucketNew[j]:
		    otherBucket = j

	    bucketLose[i].write(id + '\t' + mgiLookup[id][0] + '\t' + otherBucket + '\n')

	for id in gainSet:

	    # determine if this id exists in another bucketOld set
	    otherBucket = ''
	    for j in BUCKETLIST:
		if j == i:
		    continue
                if id in bucketOld[j]:
		    otherBucket = j

	    bucketGain[i].write(id + '\t' + mgiLookup[id][0] + '\t' + otherBucket + '\n')

    return 0

#
#  MAIN
#

if initialize() != 0:
    sys.exit(1)

if openFiles() != 0:
    sys.exit(1)

if bucketDiff() != 0:
    closeFiles()
    sys.exit(1)

closeFiles()
sys.exit(0)
