#!/usr/local/bin/python
#
#
# Program: makeInterProAnnot.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	Create/load Marker annotation files for the following areas:
#
#	  Marker/InterPro	J:53168
#
# Usage:
#
#      makeInterProAnnot.py
#
# Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#	  MGI_UNIPROT_LOAD_FILE
#
#	  UNIPROT_IP_ASSOC_FILE
#         MARKER_IP_ASSOC_FILE
#         MARKER_IP_ANNOTREF
#	  MARKER_IPSP_ANNOTNOTE
#
#         MARKER_EVIDENCECODE
#         MARKER_ANNOTEDITOR
#         MARKER_ANNOTDATE
#
# Inputs:
#
#       - UniProt load file (${MGI_UNIPROT_LOAD_FILE})
#	  1: mgi id
#	  2: swiss-prot id
#	  3: trembl id
#
#       - UniProt/InterPro files (${UNIPROT_IP_ASSOC_FILE})
#
#	- Marker/InterPro Note ($MARKER_IPSP_ANNOTNOTE)
#
#       - Marker Evidence ($MARKER_EVIDENCECODE)
#
#       - Marker Editor ($MARKER_ANNOTEDITOR)
#
#       - Marker Date ($MARKER_ANNOTDATE)
#
# Outputs:
#
#	A tab-delimtied file, one for each of these areas:
#
#	Marker/InterPro/SP	J:53168	MARKER_IPSP_ASSOC_FILE
#	Marker/InterPro/TR	J:53168	MARKER_IPTR_ASSOC_FILE
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
# 03/31/2010	lec
#	- TR 9777; original program "swissecload"
#
#

import sys
import os
import re
import string
import db

# globals

# MGI UniProt load mapping/SP (MGI id -> UniProt/SwissProt id)
mgi_to_uniprotsp = {}

# MGI UniProt load mapping/TR (MGI id -> UniProt/TrEMBL id)
mgi_to_uniprottr = {}

# UniProt to InterPro mapping (UniProt id -> InterPro ids)
uniprot_to_ip = {}

#
# Purpose: Initialization
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def initialize():
    global mgi_to_uniprotFile
    global uniprot2ipFile
    global fpMGI2UNIPROT, fpUNIPROT2IP
    global fpIPSP, fpIPTR
    global markerIPSPRef, markerIPSPNote
    global markerIPTRRef, markerIPTRNote
    global markerEvidence, markerEditor, goDate

    #
    #  initialize caches
    #

    db.useOneConnection(1)
    db.set_sqlLogFunction(db.sqlLogAll)

    mgi_to_uniprotFile = os.getenv('MGI_UNIPROT_LOAD_FILE')

    uniprot2ipFile = os.getenv('UNIPROT_IP_ASSOC_FILE')

    markerIPSPFile = os.getenv('MARKER_IPSP_ASSOC_FILE')
    markerIPSPRef = os.environ['MARKER_IPSP_ANNOTREF']
    markerIPSPNote = os.environ['MARKER_IPSP_ANNOTNOTE']

    markerIPTRFile = os.getenv('MARKER_IPTR_ASSOC_FILE')
    markerIPTRRef = os.environ['MARKER_IPTR_ANNOTREF']
    markerIPTRNote = os.environ['MARKER_IPTR_ANNOTNOTE']

    markerEvidence = os.environ['MARKER_EVIDENCECODE']
    markerEditor = os.environ['MARKER_ANNOTEDITOR']
    markerDate = os.environ['MARKER_ANNOTDATE']

    rc = 0

    #
    # Make sure the required environment variables are set.
    #
    if not mgi_to_uniprotFile:
        print 'Environment variable not set: MGI_UNIPROT_LOAD_FILE'
        rc = 1

    if not uniprot2ipFile:
        print 'Environment variable not set: UNIPROT_IP_ASSOC'
        rc = 1

    if not markerIPSPFile:
        print 'Environment variable not set: MARKER_IPSP_ASSOC_FILE'
        rc = 1

    if not markerIPSPRef:
        print 'Environment variable not set: MARKER_IPSP_ANNOTREF'
        rc = 1

    if not markerIPSPNote:
        print 'Environment variable not set: MARKER_IPSP_ANNOTNOTE'
        rc = 1

    if not markerIPTRFile:
        print 'Environment variable not set: MARKER_IPTR_ASSOC_FILE'
        rc = 1

    if not markerIPTRRef:
        print 'Environment variable not set: MARKER_IPTR_ANNOTREF'
        rc = 1

    if not markerIPTRNote:
        print 'Environment variable not set: MARKER_IPTR_ANNOTNOTE'
        rc = 1

    if not markerEvidence:
        print 'Environment variable not set: MARKER_EVIDENCECODE'
        rc = 1

    if not markerEditor:
        print 'Environment variable not set: MARKER_ANNOTEDITOR'
        rc = 1

    if not markerDate:
        print 'Environment variable not set: MARKER_ANNOTDATE'
        rc = 1

    #
    # Initialize file pointers.
    #

    fpMGI2UNIPROT = None
    fpUNIPROT2IP = None
    fpIPSP = None
    fpIPTR = None

    return rc

#
# Purpose: Close files
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def closeFiles():

    if fpMGI2UNIPROT:
	fpMGI2UNIPROT.close()

    if fpUNIPROT2IP:
	fpUNIPROT2IP.close()

    if fpIPSP:
	fpIPSP.close()

    if fpIPTR:
	fpIPTR.close()

    return 0

#
# Purpose: Open Files
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def openFiles():

    readMGI2UNIPROT()

    return 0

#
# Purpose: Read MGI-to-UniProt file & create lookup
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def readMGI2UNIPROT():

    #
    # parse mgi-to-uniprot file
    #

    global mgi_to_uniprotsp, mgi_to_uniprottr
    global mgi_to_uniprotFile, fpMGI2UNIPROT

    fpMGI2UNIPROT = open(mgi_to_uniprotFile,'r')

    lineNum = 0
    for line in fpMGI2UNIPROT.readlines():

	if lineNum == 0:
	    lineNum = lineNum + 1
	    continue

	tokens = string.split(line[:-1], '\t')
	key = tokens[0]
	value1 = string.split(tokens[1], ',')
	value2 = string.split(tokens[2], ',')

	mgi_to_uniprotsp[key] = []
	for v in value1:
	    mgi_to_uniprotsp[key].append(v)

	for v in value2:
	    if not mgi_to_uniprottr.has_key(key):
	        mgi_to_uniprottr[key] = []
	    mgi_to_uniprottr[key].append(v)

    return 0

#
# Purpose: Process Marker/InterPro data & create annotation file
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def processIP(markerIPSPFile, fpIPSP, mgi_to_uniprot, markerIPRef, markerIPNote):

    #
    # Select all Marker/UniProt associations from the Marker/UniProt association file.
    # Generate an annotation file from the Marker/InterPro associations.
    #
    # each marker has one-or-more uniprot ids (mgi_to_uniprot[sp|tr]):
    #    each uniprot id has one-or-more interpro ids (uniprot_to_ip)
    #

    fpIPSP = open(goIPSPFile, 'w')

    markerIDs = mgi_to_uniprot.keys()
    markerIDs.sort()

    for m in markerIDs:

        for uniprotVal in mgi_to_uniprot[m]:

            # if there is no uniprot_to_ip mapping, then skip it

            if not uniprot_to_ip.has_key(uniprotVal):
                continue

	    print uniprotVal
	    # for each UNIPROT-2-IP mapping....

	    #for ipName in uniprot_to_ip[uniprotVal]:

            #    fpIPSP.write(goid + '\t' + \
	#	             m + '\t' + \
	#      	             goIPRef + '\t' + \
	#      	             goEvidence + '\t' + \
	#      	             '\t' + \
	#      	             '\t' + \
	#      	             goEditor + '\t' + \
	#      	             goDate + '\t' + \
	#	             goIPNote + '\n')

    return 0

#
# Main
#

if initialize() != 0:
    sys.exit(1)

if openFiles() != 0:
    sys.exit(1)

if processIP(markerIPSPFile, fpIPSP, mgi_to_uniprotsp, markerIPSPRef, markerIPSPNote) != 0:
    sys.exit(1)

if processIP(markerIPTRFile, fpIPTR, mgi_to_uniprottr, markerIPTRRef, markerIPTRNote) != 0:
    sys.exit(1)

closeFiles()
sys.exit(0)

