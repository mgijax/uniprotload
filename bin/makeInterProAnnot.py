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
#         MARKER_IP_ANNOT_REF
#
#         ANNOT_EVIDENCECODE
#         ANNOT_EDITOR
#         ANNOT_DATE
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
#	- Marker/InterPro Reference (${MARKER_IP_ANNOT_REF})
#
#	- Marker/InterPro Note (${MARKER_IPSP_ANNOT_NOTE}, ${MARKER_IPTR_ANNOT_NOTE})
#
#       - Marker Evidence (${ANNOT_EVIDENCECODE})
#
#       - Marker Editor (${ANNOT_EDITOR})
#
#       - Marker Date (${ANNOT_DATE})
#
# Outputs:
#
#	A tab-delimtied file, one for each of these areas:
#
#	Marker/InterPro	J:53168	MARKER_IP_ASSOC_FILE
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

# MGI UniProt load mapping/SP/TR (MGI id -> UniProt id)
mgi_to_uniprot = {}

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
    global markerIPFile
    global markerIPRef
    global annotEvidence, annotEditor, annotDate

    #
    #  initialize caches
    #

    db.useOneConnection(1)
    db.set_sqlLogFunction(db.sqlLogAll)

    mgi_to_uniprotFile = os.getenv('MGI_UNIPROT_LOAD_FILE')

    uniprot2ipFile = os.getenv('UNIPROT_IP_ASSOC_FILE')

    markerIPFile = os.getenv('MARKER_IP_ASSOC_FILE')
    markerIPRef = os.environ['MARKER_IP_ANNOT_REF']

    annotEvidence = os.environ['ANNOT_EVIDENCECODE']
    annotEditor = os.environ['ANNOT_EDITOR']
    annotDate = os.environ['ANNOT_DATE']

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

    if not markerIPFile:
        print 'Environment variable not set: MARKER_IP_ASSOC_FILE'
        rc = 1

    if not markerIPRef:
        print 'Environment variable not set: MARKER_IP_ANNOT_REF'
        rc = 1

    if not annotEvidence:
        print 'Environment variable not set: ANNOT_EVIDENCECODE'
        rc = 1

    if not annotEditor:
        print 'Environment variable not set: ANNOT_EDITOR'
        rc = 1

    if not annotDate:
        print 'Environment variable not set: ANNOT_DATE'
        rc = 1

    #
    # Initialize file pointers.
    #

    fpMGI2UNIPROT = None
    fpUNIPROT2IP = None

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
    readUNIPROT2IP()

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

        mgi_to_uniprot[key] = []
        for v in value1:
            mgi_to_uniprot[key].append(v)
        for v in value2:
            mgi_to_uniprot[key].append(v)

    return 0

#
# Purpose: Read UniProt-to-InterPro file & create lookup
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def readUNIPROT2IP():

    #
    # parse uniprot-to-interpro file
    #
    # a dictionary where:
    #	key = UniProt ID
    #   value = InterPro ID (IPR#####)
    #

    global fpUNIPROT2IP

    fpUNIPROT2IP = open(uniprot2ipFile,'r')

    for line in fpUNIPROT2IP.readlines():
	tokens = string.split(line[:-1], '\t')
	key = tokens[0]
	values = string.split(tokens[1], ',')

	uniprot_to_ip[key] = []
	for v in values:
	    uniprot_to_ip[key].append(v)

    return 0

#
# Purpose: Process Marker/InterPro data & create annotation file
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def processIP():

    #
    # Select all Marker/UniProt associations from the Marker/UniProt association file.
    # Generate an annotation file from the Marker/InterPro associations.
    #
    # each marker has one-or-more uniprot ids (mgi_to_uniprot[sp|tr]):
    #    each uniprot id has one-or-more interpro ids (uniprot_to_ip)
    #	    print out each unique marker/interpro annotation
    #

    fpIP = open(markerIPFile, 'w')

    markerIDs = mgi_to_uniprot.keys()
    markerIDs.sort()

    for m in markerIDs:

	# unique set of marker/ip associations for this marker
	markerIP = []

	# for each uniprot id of a given marker...

        for uniprotVal in mgi_to_uniprot[m]:

            # if there is no uniprot_to_ip mapping, then skip it

            if not uniprot_to_ip.has_key(uniprotVal):
                continue

	    # for each interpro id for given uniprot id...

	    for ipid in uniprot_to_ip[uniprotVal]:

		# store unique interpro id for this marker
		if ipid not in markerIP:
		    markerIP.append(ipid)

	# print out the unique interpro ids for this marker

	for ipid in markerIP:

            fpIP.write(ipid + '\t' + \
		       m + '\t' + \
	      	       markerIPRef + '\t' + \
	      	       annotEvidence + '\t' + \
	      	       '\t' + \
	      	       '\t' + \
	      	       annotEditor + '\t' + \
	      	       annotDate + '\t' + \
		       '\n')

    fpIP.close()

    return 0

#
# Main
#

if initialize() != 0:
    sys.exit(1)

if openFiles() != 0:
    sys.exit(1)

if processIP() != 0:
    sys.exit(1)

closeFiles()
sys.exit(0)

