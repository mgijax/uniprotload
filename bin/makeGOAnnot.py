#!/usr/local/bin/python

#
# Program: makeGOAnnot.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	Create/load GO annotation files for the following groups:
#
#	  GO/EC
#	  GO/InterPro
#
# Usage:
#
#      makeGOAnnot.py
#
# Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#         EC2GOFILE
#         GO_EC_ASSOC_FILE
#         GO_ECANNOTREF
#
#         GO_EVIDENCECODE
#         GO_ANNOTEDITOR
#         GO_ANNOTDATE
#
# Inputs:
#
#	- EC-2-GO file ($EC2GOFILE)
#
#	  EC:1 > GO:oxidoreductase activity ; GO:0016491
#
#       - GO/EC Reference ($GO_ECANNOTREF)
#
#       - GO/EC Evidence ($GO_EVIDENCECODE)
#
#       - GO/EC Editor ($GO_ANNOTEDITOR)
#
#       - GO/EC Date ($GO_ANNOTDATE)
#
# Outputs:
#
#	A tab-delimited annotation file in the format
#	(see dataload/annotload)
#
#               field 1: Accession ID of Vocabulary Term being Annotated to
#               field 2: ID of MGI Object being Annotated (ex. MGI ID)
#               field 3: J: (J:#####)
#               field 4: Evidence Code Abbreviation (max length 5)
#               field 5: Inferred From (max length 255)
#               field 6: Qualifier (max length 255)
#               field 7: Editor (max length 30)
#               field 8: Date (MM/DD/YYYY)
#               field 9: Notes (max length 255)
#
# History:
#
# 03/25/2010	lec
#	- TR 9777; original program "swissecload"
#
# 07/29/2008	lec
#	- TR 8877; only select markers of type "gene"
#
# 01/24/2007	lec
#	- TR 8122; added EC id to "inferred from" field for GO annotations
#
# 05/11/2005	lec
#	- TR 6790
#

import sys
import os
import re
import db

# globals

# EC to GO mapping (EC id -> GO id)
ec_to_go = {}		

# InterPro to GO mapping (InterPro id -> GO id)
ip_to_go = {}		

# MGI Marker key->MGI ID)
mgiMarker = {}		

# non-IEA MGI Marker/GO ID annotations
nonIEA_annotations = []	

def initialize():
    global ec2goFile, goECFile
    global interpro2goFile, goIPFile
    global goECRef, goEvidence, goEditor, goDate
    global fpEC2GO, fpGOEC, fpGOIP

    #
    #  initialize caches
    #

    db.useOneConnection(1)
    db.set_sqlLogFunction(db.sqlLogAll)

    ec2goFile = os.getenv('EC2GOFILE')
    goECFile = os.getenv('GO_EC_ASSOC_FILE')
    goECRef = os.environ['GO_ECANNOTREF']

    goEvidence = os.environ['GO_EVIDENCECODE']
    goEditor = os.environ['GO_ANNOTEDITOR']
    goDate = os.environ['GO_ANNOTDATE']

    rc = 0

    #
    # Make sure the required environment variables are set.
    #
    if not ec2goFile:
        print 'Environment variable not set: EC2GOFILE'
        rc = 1

    if not goECFile:
        print 'Environment variable not set: GO_EC_ASSOC_FILE'
        rc = 1

    if not goECRef:
        print 'Environment variable not set: GO_ECANNOTREF'
        rc = 1

    if not goEvidence:
        print 'Environment variable not set: GO_EVIDENCECODE'
        rc = 1

    if not goEditor:
        print 'Environment variable not set: GO_ANNOTEDITOR'
        rc = 1

    if not goDate:
        print 'Environment variable not set: GO_ANNOTDATE'
        rc = 1

    #
    # Initialize file pointers.
    #

    fpEC2GO = None
    fpGOEC = None

    return rc

def openFiles():

    global mgiMarker
    global nonIEA_annotations

    readEC2GO()

    #
    # Markers & MGI IDs

    results = db.sql('select _Object_key, accID from ACC_Accession ' + \
        'where _MGIType_key = 2 and _LogicalDB_key = 1 ' + \
        'and prefixPart = "MGI:" and preferred = 1', 'auto')
    for r in results:
        mgiMarker[r['_Object_key']] = r['accID']

    #
    # Non-IEA GO Annotations.
    #

    # get all GO annotations in MGD

    db.sql('''select a._Annot_key, a._Object_key, ac.accID 
	into #annots 
	from VOC_Annot a, ACC_Accession ac 
	where a._AnnotType_key = 1000 
	and a._Term_key = ac._Object_key 
	and ac._MGIType_key = 13 ''', None)
    db.sql('create index idx1 on #annots(_Annot_key)', None)

    # get  all non-IEA
    db.sql('''select distinct a._Object_key, a.accID 
	into #evidence 
	from #annots a, VOC_Evidence e 
	where a._Annot_key = e._Annot_key 
	and e._EvidenceTerm_key != 115''', None)
    db.sql('create index idx1 on #evidence(_Object_key)', None)

    # get Marker MGI ID/GO ID pairs for markers of type "gene" only

    results = db.sql('''select mgiID = a.accID, e.accID 
	from #evidence e, ACC_Accession a, MRK_Marker m 
	where e._Object_key = a._Object_key 
	and a._MGIType_key = 2 
	and a._LogicalDB_key = 1 
	and a.prefixPart = "MGI:" 
	and a.preferred = 1 
	and a._Object_key = m._Marker_key 
	and m._Marker_Type_key = 1''', 'auto')
    for r in results:
        key = r['mgiID'] + r['accID']
        nonIEA_annotations.append(key)

    return 0

def readEC2GO():

    #
    # parse ec2go file...one EC ID can have many GO mappings
    #

    global ec_to_go, ec2goFile, fpEC2GO

    ec2gore = re.compile("(^EC:.+) +> +GO:.* +; +(GO:[0-9]+)")

    fpEC2GO = open(ec2goFile,'r')

    for line in fpEC2GO.readlines():
        r = ec2gore.match(line)
        if (r is not None):
            ecid = r.group(1)
            goid = r.group(2)
            if not ec_to_go.has_key(ecid):
                ec_to_go[ecid] = []
            ec_to_go[ecid].append(goid)

    return 0

def closeFiles():

    if fpEC2GO:
	fpEC2GO.close()

    if fpGOEC:
	fpGOEC.close()

    return 0

def processEC2GO():

    global goECFile, fpGOEC

    #
    # Prepare an GO annotation load file that will contain all Marker/GO annotations
    # that are based on Marker/EC annotations currently in MGI.
    #
    # Only select those Markers that are of marker type "gene".
    #
    # Some of the Marker/EC annotations in MGI are manually curated.
    # Others are the result of the SwissProt load.
    #
    # Only consider loading a Marker/GO IEA EC annotation if a non-IEA GO annotation
    # to the same GO term does not already exist.
    #

    fpGOEC = open(goECFile, 'w')

    results = db.sql('''select a._Object_key, accID = "EC:" + a.accID 
        from ACC_Accession a, MRK_Marker m 
        where a._MGIType_key = 2 
        and a._LogicalDB_key = 8 
        and a._Object_key = m._Marker_key 
        and m._Marker_Type_key = 1''', 'auto')

    for r in results:

        marker = r['_Object_key']
        markerID = mgiMarker[marker]
        ec = r['accID']

        # if there is no EC-2-GO mapping for the EC ID, then skip it

        if not ec_to_go.has_key(ec):
            continue

	# for each EC-2-GO mapping....

	for goid in ec_to_go[ec]:

	    # if a non-IEA annotation does not exist for this Marker/GO association....

	    nonIEAkey = markerID + goid
	    if nonIEAkey not in nonIEA_annotations:

		# ....then we want to load this annotation.

	        fpGOEC.write(goid + '\t' + \
		         markerID + '\t' + \
	      	         goECRef + '\t' + \
	      	         goEvidence + '\t' + \
	      	         ec + '\t' + \
	      	         '\t' + \
	      	         goEditor + '\t' + \
	      	         goDate + '\t' + \
	      	         '\n')

    return 0

#
# Main
#

if initialize() != 0:
    sys.exit(1)

if openFiles() != 0:
    sys.exit(1)

if processEC2GO() != 0:
    sys.exit(1)

closeFiles()
sys.exit(0)
