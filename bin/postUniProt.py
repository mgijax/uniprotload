#
#  postUniProt.py
###########################################################################
#
#  Purpose:
#
#      This script will use the records in the UNIPROT_ACC_ASSOC_FILE file
#
#	   If the UNIPROT_ACC_ASSOC_FILE/field 8 contains "Reference proteome", 
#        then add row for ACC_Accession._logicaldb_key = 234
#
#  Usage:
#
#      postUniProt.py
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#          UNIPROT_ACC_ASSOC_FILE
#
#  Inputs:
#      - UniProt association file ($UNIPROT_ACC_ASSOC_FILE) 
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#
#  Assumes:  Nothing
#
###########################################################################

import sys 
import os
import db

db.setTrace()

# UNIPROT_ACC_ASSOC_FILE
uniprotAccAssocFile = None

# file pointers
fpAccAssoc = None

#
# Purpose: Initialization
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global uniprotAccAssocFile
    global fpAccAssoc

    uniprotAccAssocFile = os.getenv('UNIPROT_ACC_ASSOC_FILE')

    rc = 0

    #
    # Make sure the environment variables are set.
    #
    if not uniprotAccAssocFile:
        print('Environment variable not set: UNIPROT_ACC_ASSOC_FILE')
        rc = 1

    #
    # Initialize file pointers.
    #
    fpAccAssoc = None

    return rc

#
# Purpose: Open files.
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global fpAccAssoc

    #
    # Open the acc association file.
    #
    try:
        fpAccAssoc = open(uniprotAccAssocFile, 'r')
    except:
        print('Cannot open association file: ' + uniprotAccAssocFile)
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

    if fpAccAssoc:
        fpAccAssoc.close()

    return 0


#
# Purpose:  Process Updates of ACC_Accession.preferred
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def processUpdates():

    db.sql('delete from ACC_Accession where _logicaldb_key = 234', None)
    db.commit()

    results = db.sql('select max(_Accession_key) + 1 as maxKey from ACC_Accession', 'auto')
    accKey = results[0]['maxKey']

    # list of accids that contain 'Reference proteome'
    accLookup = {}
    for line in fpAccAssoc.readlines():

        tokens = line[:-1].split('\t')
        accid = tokens[0]
        info = tokens[7]

        if 'Reference proteome' in info:
            accLookup[accid] = []
            accLookup[accid].append(info)

    #print(accLookup)

    # search for accids that exist for markers/SWISS-PROT/TrEMBL, er uniprotload_assocload
    results = db.sql('''
            select a._accession_key, a.accid, m._marker_key, m.symbol
            from acc_accession a, mrk_marker m
            where a._mgitype_key = 2 
            and a._logicaldb_key in (13,41) 
            and a._createdby_key in (1442,1555)
            and a._object_key = m._marker_key
            ''', 'auto')

    addSQL = ''
    for r in results:
        accid = r['accid']
        markerKey = r['_marker_key']

        # if accid in database exists in accLookup, then set preferred = 0
        if accid in accLookup:
            addSQL += '''insert into ACC_Accession values(%s,'%s',null,null,234,%d,2,0,1,1442,1442,now(),now());\n''' % (accKey, accid, markerKey)
            addSQL += '''insert into ACC_AccessionReference values(%s,53672,1442,1442,now(),now());\n''' % (accKey)
            accKey += 1
            #print(r)
           
    #print(addSQL)
    if len(addSQL) > 0:
        db.sql(addSQL, None)
        db.commit()

    return 0

#
#  MAIN
#

#print('initialize()')
if initialize() != 0:
    sys.exit(1)

#print('openFiles()')
if openFiles() != 0:
    sys.exit(1)

#print('processUpdates()')
if processUpdates() != 0:
    closeFiles()
    sys.exit(1)

closeFiles()
sys.exit(0)
