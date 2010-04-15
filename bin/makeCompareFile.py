#!/usr/local/bin/python

#
# This script will compare the MGI/UniProt associations that were generated
# by the new bucketization process versus the MGI/UniProt associations that
# were loaded in the database.
#

import sys 
import os
import db
import tabledatasetlib


FIELDS = [ 'MGI ID', 'SWISS-PROT', 'TrEMBL' ]

DEFAULT_BUCKETDIR = os.getcwd()
DEFAULT_BUCKET_PREFIX = 'bucket'

B0_1 = '0_1'
B1_0 = '1_0'
B1_1 = '1_1'
B1_N = '1_N'
BN_1 = 'N_1'
BN_N = 'N_N'

BUCKETLIST = [ B0_1, B1_0, B1_1, B1_N, BN_1, BN_N ]

bucket = {}
bucketizer = None


#
# Purpose: Initialization
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global newAssocFile, oldAssocFile
    global bucketDir, bucketPrefix
    global bucket

    newAssocFile = os.getenv('MGI_UNIPROT_LOAD_FILE')
    oldAssocFile = os.getenv('MGI_UNIPROT_OLDLOAD')
    bucketDir = os.getenv('BUCKETDIR')
    bucketPrefix = sys.argv[1]

    rc = 0

    #
    # Make sure the required environment variables are set.
    #
    if not newAssocFile:
        print 'Environment variable not set: MGI_UNIPROT_LOAD_FILE'
        rc = 1
    if not oldAssocFile:
        print 'Environment variable not set: MGI_UNIPROT_OLDLOAD'
        rc = 1

    #
    # Use defaults for optional environment variables that are not set.
    #
    if not bucketDir:
        bucketDir = DEFAULT_BUCKETDIR
    if not bucketPrefix:
        bucketPrefix = DEFAULT_BUCKET_PREFIX

    #
    # Initialize file pointers.
    #
    for i in BUCKETLIST:
        bucket[i] = None

    return rc


#
# Purpose: Open files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global bucket

    #
    # Open the bucket files.
    #
    for i in BUCKETLIST:
        file = bucketDir + '/' + bucketPrefix + '.' + i + '.txt'
        try:
            bucket[i] = open(file, 'w')
        except:
            print 'Cannot open bucket: ' + file
            return 1

    return 0


#
# Purpose: Close files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def closeFiles():
    for i in BUCKETLIST:
        if bucket[i]:
            bucket[i].close()

    return 0


#
# Purpose: Bucketize the files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def bucketize():
    global dsNew, dsOld, bucketizer

    #
    # Create a TableDataSet for the new association file.
    #
    multiFields = { 'SWISS-PROT' : ',' , 'TrEMBL' : ',' }

    dsNew = tabledatasetlib.TextFileTableDataSet(
                'new',
                newAssocFile,
                fieldnames=FIELDS,
		multiValued=multiFields,
                readNow=1)

    dsNew.addIndexes( [ 'SWISS-PROT',  'TrEMBL' ] )

    #
    # Create a TableDataSet for the old association file.
    #
    dsOld = tabledatasetlib.TextFileTableDataSet(
                'old',
                oldAssocFile,
                fieldnames=FIELDS,
		multiValued=multiFields,
                readNow=1)

    dsOld.addIndexes( [ 'SWISS-PROT',  'TrEMBL' ] )

    #
    # Create a bucketizer for the two datasets and run it.
    #
    bucketizer = tabledatasetlib.TableDataSetBucketizer(
                     dsNew,
                     [ 'SWISS-PROT', 'TrEMBL' ],
                     dsOld,
                     [ 'SWISS-PROT', 'TrEMBL' ])
    bucketizer.run()

    print 'MGI/UniProt Associations (New Bucketization vs SwissProt Load)'

    print '0:1 Bucket: ' + str(len(bucketizer.get0_1()))
    print '1:0 Bucket: ' + str(len(bucketizer.get1_0()))
    print '1:1 Bucket: ' + str(len(bucketizer.get1_1()))

    count = 0
    for (newKey, oldKeys) in bucketizer.get1_n():
        count += len(oldKeys)
    print '1:N Bucket: ' + str(count)

    count = 0
    for (newKeys, oldKey) in bucketizer.getn_1():
        count += len(newKeys)
    print 'N:1 Bucket: ' + str(count)

    return 0


#
# Purpose: Write the bucketizing results to the bucket files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def writeBuckets():

    reporter = tabledatasetlib.TableDataSetBucketizerReporter(bucketizer)

    reporter.write_0_1(bucket[B0_1], FIELDS)
    reporter.write_1_0(bucket[B1_0], FIELDS)
    reporter.write_1_1(bucket[B1_1], FIELDS, FIELDS)
    reporter.write_1_n(bucket[B1_N], FIELDS, FIELDS)
    reporter.write_n_1(bucket[BN_1], FIELDS, FIELDS)
    reporter.write_n_m(bucket[BN_N], FIELDS, FIELDS)

    return 0


#
#  MAIN
#

if initialize() != 0:
    sys.exit(1)

if openFiles() != 0:
    sys.exit(1)

if bucketize() != 0:
    closeFiles()
    sys.exit(1)

if writeBuckets() != 0:
    closeFiles()
    sys.exit(1)

closeFiles()
sys.exit(0)
