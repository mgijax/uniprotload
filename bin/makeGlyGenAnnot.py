#
#
# Program: makeGlyGenAnnot.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	Create Marker/GlyGen (J:345062) annotation file.
#
# Usage:
#
#      makeGlyGenAnnot.py
#
# Env Vars:
#
#      The following environment variables are set by the configuration
#      file that is sourced by the wrapper script:
#
#	  MGI_UNIPROT_LOAD_FILE
#	  UNIPROT_GG_ASSOC_FILE
#
#         MARKER_GG_ASSOC_FILE
#         MARKER_GG_ASSOC_ERR_FILE
#         MARKER_GG_ANNOT_REF
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
#       - UniProt/GlyGen (${UNIPROT_GG_ASSOC_FILE})
#
#	- Marker/GlyGen Reference (${MARKER_GG_ANNOT_REF})
#
#       - Marker Evidence (${ANNOT_EVIDENCECODE})
#
#       - Marker Editor (${ANNOT_EDITOR})
#
#       - Marker Date (${ANNOT_DATE})
#
# Outputs:
#
#	A tab-delimited annotation file in the format
#
#       MARKER_GG_ASSOC_FILE
#	(see dataload/annotload)
#
#               field 1: Accession ID of Vocabulary Term being Annotated to
#               field 2: ID of MGI Object being Annotated (ex. MGI ID)
#               field 3: J: (J:#####)
#               field 4: Evidence Code Abbreviation (max length 5)
#               field 5: Inferred From
#               field 6: Qualifier
#               field 7: Editor (max length 30)
#               field 8: Date (MM/DD/YYYY)
#               field 9: Notes
#
#       MARKER_GG_ASSOC_ERR_FILE
#       sanity check error log
#
# History:
#
# 02/15/2024	lec
#	- wts2-575/fl2-743/Add GlyGen links to MGI gene detail pages/more Analysis
#       - copied from makeInterProAnnot.py
#
#

import sys
import os
import re
import db
import mgi_utils

# globals

# turn of for debugging
#db.setTrace(True)

# file name MGI_UNIPROT_LOAD_FILE
mgi_to_uniprotFile = None

# file name MARKER_GG_ASSOC_FILE
markerGGFile = None

# file name MARKER_GG_ASSOC_ERR_FILE
markerGGErrFile = None

# file name MARKER_GG_ANNOT_REF
markerGGRef = None

# variable name ANNOT_EVIDENCECODE
annotEvidence = None

# variable name ANNOT_EDITOR
annotEditor = None

# variable name ANNOT_DATE
annotDate = None

# MGI UniProt load mapping/SP/TR (MGI id -> UniProt id)
mgi_to_uniprot = {}

# MGI to GlyGen/UniProt mapping (MGI id -> UniProt id)
mgi_to_gguniprot = {}

#
# Purpose: Initialization
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def initialize():
    global mgi_to_uniprotFile
    global uniprotGGFile
    global markerGGFile, markerGGErrFile
    global markerGGRef
    global annotEvidence, annotEditor, annotDate

    #
    #  initialize caches
    #

    db.set_sqlLogFunction(db.sqlLogAll)

    mgi_to_uniprotFile = os.getenv('MGI_UNIPROT_LOAD_FILE')
    uniprotGGFile = os.getenv('UNIPROT_GG_ASSOC_FILE')
    markerGGFile = os.getenv('MARKER_GG_ASSOC_FILE')
    markerGGErrFile = os.getenv('MARKER_GG_ASSOC_ERR_FILE')
    markerGGRef = os.environ['MARKER_GG_ANNOT_REF']
    annotEvidence = os.environ['ANNOT_EVIDENCECODE']
    annotEditor = os.environ['ANNOT_EDITOR']
    annotDate = os.environ['ANNOT_DATE']

    rc = 0

    #
    # Make sure the required environment variables are set.
    #
    if not mgi_to_uniprotFile:
        print('Environment variable not set: MGI_UNIPROT_LOAD_FILE')
        rc = 1

    if not uniprotGGFile:
        print('Environment variable not set: UNIPROT_GG_ASSOC_FILE')
        rc = 1

    if not markerGGFile:
        print('Environment variable not set: MARKER_GG_ASSOC_FILE')
        rc = 1

    if not markerGGErrFile:
        print('Environment variable not set: MARKER_GG_ASSOC_ERR_FILE')
        rc = 1

    if not markerGGRef:
        print('Environment variable not set: MARKER_GG_ANNOT_REF')
        rc = 1

    if not annotEvidence:
        print('Environment variable not set: ANNOT_EVIDENCECODE')
        rc = 1

    if not annotEditor:
        print('Environment variable not set: ANNOT_EDITOR')
        rc = 1

    if not annotDate:
        print('Environment variable not set: ANNOT_DATE')
        rc = 1

    return rc

#
# Purpose: Open Files
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def openFiles():

    readMGIGLYGEN()

    return 0

def readMGIGLYGEN():

    #
    # parse UniProt-to-GlyGen associations via the database
    #
    # dictionary contains:
    #	key = uniprot id
    #   value = uniprot id
    #

    fp = open(uniprotGGFile,'r')

    for line in fp.readlines():

        tokens = str.split(line[:-1], '\t')

        key = tokens[1]
        value = tokens[0]

        if key == "mgi_id":
                continue

        if key not in mgi_to_gguniprot:
            mgi_to_gguniprot[key] = []
        mgi_to_gguniprot[key].append(value)

    fp.close()
    #print(mgi_to_gguniprot)

    return 0

#
# Purpose: Process Marker/GlyGen data & create annotation file
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def processGlyGen():

    #
    # Select all Marker/UniProt associations from the GG/Marker association file.
    # Generate an annotation file from the Marker/GlyGen associations.
    #
    # each uniprot id has one uniprot ids (mgi_to_gguniprot)
    #   if uniprot_to_go/marker/uniprot id does not match mgi_to_uniprot:
    #       print discrepency
    #   else:
    #	    print out each unique marker/uniprot annotation
    #

    badMatch = ''

    fp1 = open(markerGGFile, 'w')
    fp2 = open(markerGGErrFile, 'w')

    for ggMgiId in mgi_to_gguniprot:

        for ggUniProtId in mgi_to_gguniprot[ggMgiId]:
                results = db.sql('''
                        select a1.accid from acc_accession a1, acc_accession a2
                        where a1._mgitype_key = 2 and a1.accid = '%s'
                        and a1._accession_key != a2._accession_key
                        and a1._object_key = a2._object_key
                        and a2._mgitype_key = 2
                        and a2._logicaldb_key = 1
                        and a2.accid = '%s'
                        ''' % (ggUniProtId, ggMgiId), 'auto')
                if len(results) > 0:
                                fp1.write(ggUniProtId + '\t' + \
                                ggMgiId + '\t' + \
                                markerGGRef + '\t' + \
                                'NA\t' + \
                                '\t' + \
                                '\t' + \
                                annotEditor + '\t' + \
                                annotDate + '\t' + \
                                '\n')
                else:
                        badMatch += '%s, %s\n' % (ggMgiId,ggUniProtId)

    fp2.write('#\n# Date Generated: %s\n' % (mgi_utils.date()))
    fp2.write('# (server = %s, database = %s)\n#\n\n' % (db.get_sqlServer(), db.get_sqlDatabase()))
    fp2.write('\nGlyGene Marker/UniProt does not match MGI-UniProt file:\n\n')
    fp2.write(badMatch)

    fp1.close()
    fp2.close()

    return 0

#
# Main
#

if initialize() != 0:
    sys.exit(1)

if openFiles() != 0:
    sys.exit(1)

if processGlyGen() != 0:
    sys.exit(1)

sys.exit(0)
