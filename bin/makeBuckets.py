#!/usr/local/bin/python
#
#  makeBuckets.py
###########################################################################
#
#  Purpose:
#
#      This script will bucketize the MGI IDs in the MGI association file
#      against the UniProt IDs in the UniProt association file by comparing
#      what EntrezGene/Ensembl IDs they have in common.
#
#  Usage:
#
#      makeBuckets.py
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#          MGI_ACC_ASSOC_FILE
#          UNIPROT_ACC_ASSOC_FILE
#          UNIPROT_ACC1_ASSOC_FILE
#          UNIPROT_ACC2_ASSOC_FILE
#          UNIPROT_PDB_ASSOC_FILE
#          UNIPROT_EC_ASSOC_FILE
#          BUCKETDIR
#          BUCKET_PREFIX
#          MGI_UNIPROT_LOAD_FILE
#
#  Inputs:
#
#      - MGI association file ($MGI_ACC_ASSOC_FILE, $MGI_ACC2_ASSOC_FILE)
#        to be used by the TableDataSet class. It has the following tab-delimited fields:
#
#        1) MGI ID (for a marker)
#        2) EntrezGene IDs and NBCI gene model IDs (comma-separated)
#        3) Ensembl gene model IDs (comma-separated)
#
#      - SwissProt association file ($UNIPROT_ACC1_ASSOC_FILE) to be used by
#        the generate a lookup file.
#        It has the following tab-delimited fields:
#
#        1) UniProt ID
#
#      - TrEMBL association file ($UNIPROT_ACC2_ASSOC_FILE) to be used by
#        the generate a lookup file.
#        It has the following tab-delimited fields:
#
#        1) UniProt ID
#
#      - UniProt PDB association file ($UNIPROT_PDB_ASSOC_FILE) to be used
#        to generate a lookup file.
#        It has the following tab-delimited fields:
#
#        1) UniProt ID
#        2) PDB IDs (comma-separated)
#
#      - UniProt EC association file ($UNIPROT_EC_ASSOC_FILE) to be used
#        to generate a lookup file.
#        It has the following tab-delimited fields:
#
#        1) UniProt ID
#        2) EC IDs (comma-separated)
#
#  Outputs:
#
#      - Cardinality files (buckets) from the MGI/UniProt comparison.
#        Each file name is prefixed as follows:
#
#        ${BUCKET_PREFIX}.0_1.txt
#        ${BUCKET_PREFIX}.1_0.txt
#        ${BUCKET_PREFIX}.1_1.txt
#        ${BUCKET_PREFIX}.1_n.txt
#        ${BUCKET_PREFIX}.n_1.txt
#        ${BUCKET_PREFIX}.n_n.txt
#
#      - A file of unique MGI/UniProt associations from the 1:1 and 1:N
#        buckets ($MGI_UNIPROT_LOAD_FILE). It has the following tab-delimited
#        fields:
#
#        header:  MGI\tSWISS-PROT\tTrEMBL\tPDB\tEC
#        1) MGI ID (for a marker)
#        2) UniProt ID
#        3) PDB ID
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
#      3) Create a TableDataSet object for each of the input files.
#      4) Create a bucketizer for the TableDataSet objects and run it.
#      5) Write the contents of the buckets to the output files.
#      6) Write the MGI/UniProt associations from the 1:1 and 1:N buckets
#         the a file.
#      7) Close files.
#
#  Notes:  None
#
###########################################################################

import sys 
import os
import string
import db
import tabledatasetlib
#from tabledatasetlib import *


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

swissprotLookup = []
tremblLookup = []
pdbLookup = {}
ecLookup = {}

#
# Purpose: Initialization
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global mgiAssocFile
    global uniprotAccAssocFile, uniprotAcc1AssocFile, uniprotAcc2AssocFile
    global uniprotPDBAssocFile, uniprotECAssocFile
    global bucketRptFile
    global bucketDir, bucketPrefix
    global bucket, bucketRpt
    global fpSPAssoc, fpTRAssoc, fpPDBAssoc, fpECAssoc

    mgiAssocFile = os.getenv('MGI_ACC_ASSOC_FILE')
    uniprotAccAssocFile = os.getenv('UNIPROT_ACC_ASSOC_FILE')
    uniprotAcc1AssocFile = os.getenv('UNIPROT_ACC1_ASSOC_FILE')
    uniprotAcc2AssocFile = os.getenv('UNIPROT_ACC2_ASSOC_FILE')
    uniprotPDBAssocFile = os.getenv('UNIPROT_PDB_ASSOC_FILE')
    uniprotECAssocFile = os.getenv('UNIPROT_EC_ASSOC_FILE')
    bucketDir = os.getenv('BUCKETDIR')
    bucketPrefix = os.getenv('BUCKET_PREFIX')
    bucketRptFile = os.getenv('MGI_UNIPROT_LOAD_FILE')

    rc = 0

    #
    # Make sure the required environment variables are set.
    #
    if not mgiAssocFile:
        print 'Environment variable not set: MGI_ACC_ASSOC_FILE'
        rc = 1

    if not uniprotAccAssocFile:
        print 'Environment variable not set: UNIPROT_ACC_ASSOC_FILE'
        rc = 1

    if not uniprotAcc1AssocFile:
        print 'Environment variable not set: UNIPROT_ACC1_ASSOC_FILE'
        rc = 1

    if not uniprotAcc2AssocFile:
        print 'Environment variable not set: UNIPROT_ACC2_ASSOC_FILE'
        rc = 1

    if not uniprotPDBAssocFile:
        print 'Environment variable not set: UNIPROT_PDB_ASSOC_FILE'
        rc = 1

    if not uniprotECAssocFile:
        print 'Environment variable not set: UNIPROT_EC_ASSOC_FILE'
        rc = 1

    if not bucketRptFile:
        print 'Environment variable not set: MGI_UNIPROT_LOAD_FILE'
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
    bucketRpt = None
    fpSPAssoc = None
    fpTRAssoc = None
    fpPDBAssoc = None
    fpECAssoc = None

    return rc


#
# Purpose: Open files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global bucket, bucketRpt
    global swissprotLookup, tremblLookup, pdbLookup
    global fpSPAssoc, fpTRAssoc, fpPDBAssoc, fpECAssoc

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

    #
    # Open the report files.
    #
    try:
        bucketRpt = open(bucketRptFile, 'w')
    except:
        print 'Cannot open report: ' + bucketRptFile
        return 1

    bucketRpt.write('MGI\tSWISS-PROT\tTrEMBL\tPDB\tEC\n')

    #
    # Open the swissprot association file.
    #
    try:
        fpSPAssoc = open(uniprotAcc1AssocFile, 'r')
	for line in fpSPAssoc.readlines():
            swissprotLookup.append(line[:-1])
    except:
        print 'Cannot open swissprot association file: ' + uniprotPDBAssocFile
        return 1

    #
    # Open the trembl association file.
    #
    try:
        fpTRAssoc = open(uniprotAcc2AssocFile, 'r')
	for line in fpTRAssoc.readlines():
            tremblLookup.append(line[:-1])
    except:
        print 'Cannot open trembl association file: ' + uniprotPDBAssocFile
        return 1

    #
    # Open the pdb association file.
    #
    try:
        fpPDBAssoc = open(uniprotPDBAssocFile, 'r')
	for line in fpPDBAssoc.readlines():
	    tokens = string.split(line[:-1], '\t')
	    key = tokens[0]
	    value = tokens[1]
	    if not pdbLookup.has_key(key):
		pdbLookup[key] = []
            pdbLookup[key].append(value)
    except:
        print 'Cannot open pdb association file: ' + uniprotPDBAssocFile
        return 1

    #
    # Open the ec association file.
    #
    try:
        fpECAssoc = open(uniprotECAssocFile, 'r')
	for line in fpECAssoc.readlines():
	    tokens = string.split(line[:-1], '\t')
	    key = tokens[0]
	    value = tokens[1]
	    if not ecLookup.has_key(key):
		ecLookup[key] = []
            ecLookup[key].append(value)
    except:
        print 'Cannot open ec association file: ' + uniprotPDBAssocFile
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

    if bucketRpt:
        bucketRpt.close()

    if fpSPAssoc:
        fpSPAssoc.close()

    if fpTRAssoc:
        fpTRAssoc.close()

    if fpPDBAssoc:
        fpPDBAssoc.close()

    if fpECAssoc:
        fpECAssoc.close()

    return 0


#
# Purpose: Bucketize the MGI/UniProt IDs from the association files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def bucketize():
    global dsMGI, dsUniProt, bucketizer

    #
    # Create a TableDataSet for the MGI association file.
    #
    fields = [ 'MGI ID', 'EntrezGene ID', 'Ensembl ID' ]
    multiFields = { 'EntrezGene ID' : ',' , 'Ensembl ID' : ',' }

    dsMGI = tabledatasetlib.TextFileTableDataSet(
                'mgi',
                mgiAssocFile,
                fieldnames=fields,
                multiValued=multiFields,
                readNow=1)

    dsMGI.addIndexes( [ 'EntrezGene ID', 'Ensembl ID' ] )

    #
    # Create a TableDataSet for the UniProt association file.
    #
    fields = [ 'UniProt ID', 'EntrezGene ID', 'Ensembl ID' ]
    multiFields = { 'EntrezGene ID' : ',' , 'Ensembl ID' : ',' }

    dsUniProt = tabledatasetlib.TextFileTableDataSet(
                    'uniprot',
                    uniprotAccAssocFile,
                    fieldnames=fields,
                    multiValued=multiFields,
                    readNow=1)

    dsUniProt.addIndexes( [ 'EntrezGene ID', 'Ensembl ID' ] )

    #
    # Create a bucketizer for the two datasets and run it.
    #
    bucketizer = tabledatasetlib.TableDataSetBucketizer(
                     dsMGI,
                     [ 'EntrezGene ID', 'Ensembl ID' ],
                     dsUniProt,
                     [ 'EntrezGene ID', 'Ensembl ID' ])
    bucketizer.run()

    print 'MGI vs UniProt'

    print '0:1 Bucket: ' + str(len(bucketizer.get0_1()))
    print '1:0 Bucket: ' + str(len(bucketizer.get1_0()))
    print '1:1 Bucket: ' + str(len(bucketizer.get1_1()))

    count = 0
    for (mgiKey, uniprotKeys) in bucketizer.get1_n():
        count += len(uniprotKeys)
    print '1:N Bucket: ' + str(count)

    count = 0
    for (mgiKeys, uniprotKey) in bucketizer.getn_1():
        count += len(mgiKeys)
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

    reporter.write_0_1(bucket[B0_1],
                       [ 'UniProt ID', 'EntrezGene ID', 'Ensembl ID' ])

    reporter.write_1_0(bucket[B1_0],
                       [ 'MGI ID', 'EntrezGene ID', 'Ensembl ID' ])

    reporter.write_1_1(bucket[B1_1],
                       [ 'MGI ID', 'EntrezGene ID', 'Ensembl ID' ],
                       [ 'UniProt ID', 'EntrezGene ID', 'Ensembl ID' ])

    reporter.write_1_n(bucket[B1_N],
                       [ 'MGI ID', 'EntrezGene ID', 'Ensembl ID' ],
                       [ 'UniProt ID', 'EntrezGene ID', 'Ensembl ID' ])

    reporter.write_n_1(bucket[BN_1],
                       [ 'MGI ID', 'EntrezGene ID', 'Ensembl ID' ],
                       [ 'UniProt ID', 'EntrezGene ID', 'Ensembl ID' ])

    reporter.write_n_m(bucket[BN_N],
                       [ 'MGI ID', 'EntrezGene ID', 'Ensembl ID' ],
                       [ 'UniProt ID', 'EntrezGene ID', 'Ensembl ID' ])

    return 0


#
# Purpose: Write the bucketizing results to the bucket files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def writeBuckets_save():
    #
    # Load the 0:1 bucket.
    #
    for uniprotKey in bucketizer.get0_1():
        uniprotRcd = dsUniProt.getRecords(uniprotKey)
        uniprotID = uniprotRcd[0]['UniProt ID']
        entrezgeneIDs = ','.join(uniprotRcd[0]['EntrezGene ID'])
        ensemblIDs = ','.join(uniprotRcd[0]['Ensembl ID'])
        bucket[B0_1].write(uniprotID + '\t' + entrezgeneIDs + '\t' + ensemblIDs + '\n')

    #
    # Load the 1:0 bucket.
    #
    for mgiKey in bucketizer.get1_0():
        mgiRcd = dsMGI.getRecords(mgiKey)
        mgiID = mgiRcd[0]['MGI ID']
        entrezgeneIDs = ','.join(mgiRcd[0]['EntrezGene ID'])
        ensemblIDs = ','.join(mgiRcd[0]['Ensembl ID'])
        bucket[B1_0].write(mgiID + '\t' + entrezgeneIDs + '\t' + ensemblIDs + '\n')

    #
    # Load the 1:1 bucket.
    #
    for (mgiKey, uniprotKey) in bucketizer.get1_1():
        mgiRcd = dsMGI.getRecords(mgiKey)
        mgiID = mgiRcd[0]['MGI ID']
        entrezgeneIDs = ','.join(mgiRcd[0]['EntrezGene ID'])
        ensemblIDs = ','.join(mgiRcd[0]['Ensembl ID'])
        bucket[B1_1].write(mgiID + '\t' + entrezgeneIDs + '\t' + ensemblIDs + '\t')
        uniprotRcd = dsUniProt.getRecords(uniprotKey)
        uniprotID = uniprotRcd[0]['UniProt ID']
        entrezgeneIDs = ','.join(uniprotRcd[0]['EntrezGene ID'])
        ensemblIDs = ','.join(uniprotRcd[0]['Ensembl ID'])
        bucket[B1_1].write(uniprotID + '\t' + entrezgeneIDs + '\t' + ensemblIDs + '\n')

    #
    # Load the 1:N bucket.
    #
    for (mgiKey, uniprotKeys) in bucketizer.get1_n():
        mgiRcd = dsMGI.getRecords(mgiKey)
        mgiID = mgiRcd[0]['MGI ID']
        entrezgeneIDs = ','.join(mgiRcd[0]['EntrezGene ID'])
        ensemblIDs = ','.join(mgiRcd[0]['Ensembl ID'])
        bucket[B1_N].write(mgiID + '\t' + entrezgeneIDs + '\t' + ensemblIDs + '\t')
        str = ' '*len(mgiID) + '\t' + ' '*len(entrezgeneIDs) + '\t' + ' '*len(ensemblIDs) + '\t'
        count = 0
        for uniprotRcd in dsUniProt.getRecords(keys = uniprotKeys):
            if count > 0:
                bucket[B1_N].write(str)
            uniprotID = uniprotRcd['UniProt ID']
            entrezgeneIDs = ','.join(uniprotRcd['EntrezGene ID'])
            ensemblIDs = ','.join(uniprotRcd['Ensembl ID'])
            bucket[B1_N].write(uniprotID + '\t' + entrezgeneIDs + '\t' + ensemblIDs + '\n')
            count+=1

    #
    # Load the N:1 bucket.
    #
    for (mgiKeys, uniprotKey) in bucketizer.getn_1():
        count = 0
        for mgiRcd in dsMGI.getRecords(keys = mgiKeys):
            mgiID = mgiRcd['MGI ID']
            entrezgeneIDs = ','.join(mgiRcd['EntrezGene ID'])
            ensemblIDs = ','.join(mgiRcd['Ensembl ID'])
            bucket[BN_1].write(mgiID + '\t' + entrezgeneIDs + '\t' + ensemblIDs + '\t')
            if count == 0:
                uniprotRcd = dsUniProt.getRecords(uniprotKey)
                uniprotID = uniprotRcd[0]['UniProt ID']
                entrezgeneIDs = ','.join(uniprotRcd[0]['EntrezGene ID'])
                ensemblIDs = ','.join(uniprotRcd[0]['Ensembl ID'])
                bucket[BN_1].write(uniprotID + '\t' + entrezgeneIDs + '\t' + ensemblIDs + '\n')
            else:
                bucket[BN_1].write('\t\t\n')
            count+=1

    return 0


#
# Purpose: Write the unique MGI/UniProt associations to a file using the
#          1:1 and 1:N buckets only.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def writeReport():

    mgiDict = {}

    #
    # Find unique MGI/UniProt associations in the 1:1 bucket.
    #
    for (mgiKey, uniprotKey) in bucketizer.get1_1():
        mgiRcd = dsMGI.getRecords(mgiKey)
        mgiID = mgiRcd[0]['MGI ID']
        uniprotRcd = dsUniProt.getRecords(uniprotKey)
        uniprotID = uniprotRcd[0]['UniProt ID']

        if mgiDict.has_key(mgiID):
            list = mgiDict[mgiID]
        else:
            list = []
        if list.count(uniprotID) == 0:
            list.append(uniprotID)
            mgiDict[mgiID] = list

    #
    # Find unique MGI/UniProt associations in the 1:N bucket.
    #
    for (mgiKey, uniprotKeys) in bucketizer.get1_n():
        mgiRcd = dsMGI.getRecords(mgiKey)
        mgiID = mgiRcd[0]['MGI ID']
        for uniprotRcd in dsUniProt.getRecords(keys = uniprotKeys):
            uniprotID = uniprotRcd['UniProt ID']

            if mgiDict.has_key(mgiID):
                list = mgiDict[mgiID]
            else:
                list = []
            if list.count(uniprotID) == 0:
                list.append(uniprotID)
                mgiDict[mgiID] = list

    #
    # Write the MGI/UniProt associations to the file.
    #
    mgiIDs = mgiDict.keys()
    mgiIDs.sort()

    for m in mgiIDs:
        uniprotIDs = mgiDict[m]
        uniprotIDs.sort()

	# MGI id
        bucketRpt.write(m + '\t')
	
	# SwissProt ids
	# TrEMBL ids
	spIDs = []
	trIDs = []
	for id in uniprotIDs:

	    if id in swissprotLookup:
		spIDs.append(id)

	    if id in tremblLookup:
		trIDs.append(id)

	bucketRpt.write(string.join(spIDs, ',') + '\t')
	bucketRpt.write(string.join(trIDs, ',') + '\t')

	# PDB ids
	for id in uniprotIDs:
	    if pdbLookup.has_key(id):
		bucketRpt.write(pdbLookup[id][0])
        bucketRpt.write('\t')

	# EC ids
	ecIDs = []
	for id in uniprotIDs:
	    if ecLookup.has_key(id):
		# ignore duplicates
		e = ecLookup[id][0]
		if e not in ecIDs:
		    ecIDs.append(e)
        bucketRpt.write(string.join(ecIDs, ',') + '\n')

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

if writeReport() != 0:
    closeFiles()
    sys.exit(1)

closeFiles()
sys.exit(0)
