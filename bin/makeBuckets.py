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
#          BUCKETDIR
#          BUCKET_PREFIX
#          MGI_UNIPROT_LOAD_FILE
#
#  Inputs:
#
#      - MGI association file ($MGI_ACC_ASSOC_FILE)
#        to be used by the TableDataSet class. 
#        It has the following tab-delimited fields:
#
#        1) MGI ID (for a marker)
#        2) EntrezGene IDs and NBCI gene model IDs (comma-separated)
#        3) Ensembl gene model IDs (comma-separated)
#        4) EC IDs (comma-separated)
#        5) PDB IDs (comma-separated)
#        6) InterPro IDs (comma-separated)
#        7) SPKW Names (comma-separated)
#
#      - SwissProt association file ($UNIPROT_ACC1_ASSOC_FILE) 
#        to be used to generate a lookup file of SwissProt associations.
#        It has the following tab-delimited fields:
#
#        1) UniProt ID
#
#      - TrEMBL association file ($UNIPROT_ACC2_ASSOC_FILE)
#        to be used to generate a lookup file of TrEMBL associations.
#        It has the following tab-delimited fields:
#
#        1) UniProt ID
#
#  Outputs:
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
#      - A file of unique MGI/UniProt associations from the 1:1 and 1:N
#        buckets ($MGI_UNIPROT_LOAD_FILE). 
#        It has the following tab-delimited fields:
#
#        header:  MGI\tSWISS-PROT\tTrEMBL\tEC\tPDB
#        1) MGI ID (for a marker)
#        2) UniProt ID
#        3) EC ID
#        4) PDB ID
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
#      6) Write the MGI/UniProt associations from the 1:1 and 1:N buckets to a file.
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
    global fpSPAssoc, fpTRAssoc

    mgiAssocFile = os.getenv('MGI_ACC_ASSOC_FILE')
    uniprotAccAssocFile = os.getenv('UNIPROT_ACC_ASSOC_FILE')
    uniprotAcc1AssocFile = os.getenv('UNIPROT_ACC1_ASSOC_FILE')
    uniprotAcc2AssocFile = os.getenv('UNIPROT_ACC2_ASSOC_FILE')
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
    global swissprotLookup, tremblLookup
    global fpSPAssoc, fpTRAssoc

    #
    # Open the bucket files.
    # Before opening new buckets...
    #   Save a copy the existing buckets, so we can use them later
    #   to do "diffs" between the old and new bucketts
    #
    for i in BUCKETLIST:
        file = bucketDir + '/' + bucketPrefix + '.' + i + '.txt'
        savedfile = bucketDir + '/' + bucketPrefix + '.' + i + '.txt.save'

        try:
	    if os.path.isfile(savedfile):
                os.remove(savedfile)
	    if os.path.isfile(file):
                os.rename(file, savedfile)
            bucket[i] = open(file, 'w')
        except:
            print 'Cannot rename/open bucket: ' + file
            return 1

    #
    # Open the report files.
    #
    try:
        bucketRpt = open(bucketRptFile, 'w')
    except:
        print 'Cannot open report: ' + bucketRptFile
        return 1

    bucketRpt.write('MGI\tSWISS-PROT\tTrEMBL\tEC\tPDB\n')

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
    fields = [ 'UniProt ID', 'EntrezGene ID', 'Ensembl ID', 'EC', 'PDB', 'InterPro ID', 'SPKW name' ]
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
def writeBuckets_format1():

    reporter = tabledatasetlib.TableDataSetBucketizerReporter(bucketizer)

    bucket[B0_1].write('total number of unique records:  %s\n\n' % (len(bucketizer.get0_1())))
    bucket[B1_0].write('total number of unique records:  %s\n\n' % (len(bucketizer.get1_0())))
    bucket[B1_1].write('total number of unique records:  %s\n\n' % (len(bucketizer.get1_1())))
    bucket[B1_N].write('total number of unique records:  %s\n\n' % (len(bucketizer.get1_n())))
    bucket[BN_1].write('total number of unique records:  %s\n\n' % (len(bucketizer.getn_1())))
    bucket[BN_N].write('total number of unique records:  %s\n\n' % (len(bucketizer.getn_m())))

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
def writeBuckets_format2():

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
    ecLookup = {}
    pdbLookup = {}

    #
    # Find unique MGI/UniProt associations in the 1:1 bucket.
    #

    for (mgiKey, uniprotKey) in bucketizer.get1_1():

        mgiRcd = dsMGI.getRecords(mgiKey)
        mgiID = mgiRcd[0]['MGI ID']

        uniprotRcd = dsUniProt.getRecords(uniprotKey)
        uniprotID = uniprotRcd[0]['UniProt ID']
	ecID = uniprotRcd[0]['EC']
	pdbID = uniprotRcd[0]['PDB']

        if mgiDict.has_key(mgiID):
            list = mgiDict[mgiID]
        else:
            list = []
        if list.count(uniprotID) == 0:
            list.append(uniprotID)
            mgiDict[mgiID] = list

	# create a lookup of mgiID/ecIDs
	if ecID is not None:
	    if not ecLookup.has_key(mgiID):
	        ecLookup[mgiID] = []
	    if ecID not in ecLookup[mgiID]:
	        ecLookup[mgiID].append(ecID)

	# create a lookup of mgiID/pdbIDs
	if pdbID is not None:
	    if not pdbLookup.has_key(mgiID):
	        pdbLookup[mgiID] = []
	    if pdbID not in pdbLookup[mgiID]:
	        pdbLookup[mgiID].append(pdbID)

    #
    # Find unique MGI/UniProt associations in the 1:N bucket.
    #
    for (mgiKey, uniprotKeys) in bucketizer.get1_n():

        mgiRcd = dsMGI.getRecords(mgiKey)
        mgiID = mgiRcd[0]['MGI ID']

        for uniprotRcd in dsUniProt.getRecords(keys = uniprotKeys):
            uniprotID = uniprotRcd['UniProt ID']
	    ecID = uniprotRcd['EC']
	    pdbID = uniprotRcd['PDB']

            if mgiDict.has_key(mgiID):
                list = mgiDict[mgiID]
            else:
                list = []
            if list.count(uniprotID) == 0:
                list.append(uniprotID)
                mgiDict[mgiID] = list

	    # create a lookup of mgiID/ecIDs
	    if ecID is not None:
	        if not ecLookup.has_key(mgiID):
		    ecLookup[mgiID] = []
	        if ecID not in ecLookup[mgiID]:
	            ecLookup[mgiID].append(ecID)

	    # create a lookup of mgiID/pdbIDs
	    if pdbID is not None:
	        if not pdbLookup.has_key(mgiID):
		    pdbLookup[mgiID] = []
	        if pdbID not in pdbLookup[mgiID]:
	            pdbLookup[mgiID].append(pdbID)

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

	# EC ids
        if ecLookup.has_key(m):
            bucketRpt.write(string.join(ecLookup[m], ','))
        bucketRpt.write('\t')

	# PDB ids
        if pdbLookup.has_key(m):
            bucketRpt.write(string.join(pdbLookup[m], ','))
        bucketRpt.write('\n')

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

if writeBuckets_format1() != 0:
    closeFiles()
    sys.exit(1)

if writeBuckets_format2() != 0:
    closeFiles()
    sys.exit(1)

if writeReport() != 0:
    closeFiles()
    sys.exit(1)

closeFiles()
sys.exit(0)
