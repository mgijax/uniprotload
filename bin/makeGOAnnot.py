#!/usr/local/bin/python
#
#
# Program: makeGOAnnot.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	Create/load GO annotation files for the following groups:
#
#	  GO/EC		J:72245
#	  GO/InterPro	J:72247
#	  GO/UniProt	J:60000
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
#	  MGI_UNIPROT_LOAD_FILE
#
#         EC2GOFILE
#         GO_EC_ASSOC_FILE
#         GO_EC_ANNOTREF
#
#         IP2GOFILE
#	  UNIPROT_GOIP_ASSOC_FILE
#         GO_IP_ASSOC_FILE
#         GO_IP_ANNOTREF
#
#         SP2GOFILE
#	  UNIPROT_GOKW_ASSOC_FILE
#         GO_UP_ASSOC_FILE
#         GO_UP_ANNOTREF
#
#         GO_EVIDENCECODE
#         GO_ANNOTEDITOR
#         GO_ANNOTDATE
#
# Inputs:
#
#       - UniProt load file (${MGI_UNIPROT_LOAD_FILE})
#	  1: mgi id
#	  2: swiss-prot id
#	  3: trembl id
#	  5: ec
#
#	- EC-2-GO file ($EC2GOFILE)
#
#	  EC:1 > GO:oxidoreductase activity ; GO:0016491
#
#	- IP-2-GO file ($IP2GOFILE)
#
#	  InterPro:IPR000003 Retinoid X receptor > GO:DNA binding ; GO:0003677
#
#	- SP-2-GO file ($SP2GOFILE)
#
#	  SP_KW:KW-0001 2Fe-2S > GO:2 iron, 2 sulfur cluster binding ; GO:0051537
#
#       - UniProt/InterPro files (${UNIPROT_GOIP_ASSOC_FILE})
#
#       - GO/EC Reference ($GO_ECANNOTREF)
#
#       - GO Evidence ($GO_EVIDENCECODE)
#
#       - GO Editor ($GO_ANNOTEDITOR)
#
#       - GO Date ($GO_ANNOTDATE)
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
import string
import db

# globals

# MGI UniProt load mapping/SP/TR (MGI id -> UniProt id)
mgi_to_uniprot = {}

# EC to GO mapping (EC id -> GO id)
ec_to_go = {}		

# InterPro to GO mapping (InterPro id -> GO id)
ip_to_go = {}		

# UniProt to InterPro mapping (UniProt id -> InterPro ids)
uniprot_to_ip = {}

# non-IEA MGI Marker/GO ID annotations
nonIEA_annotations = []	

#
# Purpose: Initialization
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def initialize():
    global mgi_to_uniprotFile
    global ec2goFile, goECFile
    global ip2goFile, goIPFile
    global uniprot2ipFile
    global fpMGI2UNIPROT
    global fpEC2GO, fpIP2GO
    global fpGOEC, fpGOIP, fpUNIPROT2IP
    global goECRef, goIPRef
    global goEvidence, goEditor, goDate, goNote

    #
    #  initialize caches
    #

    db.useOneConnection(1)
    db.set_sqlLogFunction(db.sqlLogAll)

    mgi_to_uniprotFile = os.getenv('MGI_UNIPROT_LOAD_FILE')

    ec2goFile = os.getenv('EC2GOFILE')
    goECFile = os.getenv('GO_EC_ASSOC_FILE')
    goECRef = os.environ['GO_EC_ANNOTREF']

    ip2goFile = os.getenv('IP2GOFILE')
    uniprot2ipFile = os.getenv('UNIPROT_GOIP_ASSOC_FILE')
    goIPFile = os.getenv('GO_IP_ASSOC_FILE')
    goIPRef = os.environ['GO_IP_ANNOTREF']

    goEvidence = os.environ['GO_EVIDENCECODE']
    goEditor = os.environ['GO_ANNOTEDITOR']
    goDate = os.environ['GO_ANNOTDATE']
    goNote = os.environ['GO_ANNOTNOTE']

    rc = 0

    #
    # Make sure the required environment variables are set.
    #
    if not mgi_to_uniprotFile:
        print 'Environment variable not set: MGI_UNIPROT_LOAD_FILE'
        rc = 1

    if not ec2goFile:
        print 'Environment variable not set: EC2GOFILE'
        rc = 1

    if not goECFile:
        print 'Environment variable not set: GO_EC_ASSOC_FILE'
        rc = 1

    if not goECRef:
        print 'Environment variable not set: GO_EC_ANNOTREF'
        rc = 1

    if not ip2goFile:
        print 'Environment variable not set: IP2GOFILE'
        rc = 1

    if not uniprot2ipFile:
        print 'Environment variable not set: UNIPROT_GOIP_ASSOC'
        rc = 1

    if not goIPFile:
        print 'Environment variable not set: GO_IP_ASSOC_FILE'
        rc = 1

    if not goIPRef:
        print 'Environment variable not set: GO_IP_ANNOTREF'
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

    if not goNote:
        print 'Environment variable not set: GO_ANNOTNOTE'
        rc = 1

    #
    # Initialize file pointers.
    #

    fpMGI2UNIPROT = None
    fpEC2GO = None
    fpIP2GO = None
    fpGOEC = None
    fpGOIP = None
    fpUNIPROT2IP = None

    return rc

#
# Purpose: Oopen Files
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def openFiles():

    global nonIEA_annotations

    readMGI2UNIPROT()
    readEC2GO()
    readIP2GO()

    #
    # Non-IEA GO Annotations.
    #

    # get all GO annotations in MGD

    db.sql('''select a._Annot_key, a._Object_key, ac.accID 
	into #annots 
	from VOC_Annot a, ACC_Accession ac 
	where a._AnnotType_key = 1000 
	and a._Term_key = ac._Object_key 
	and ac._MGIType_key = 13 
	and a._Object_key = 3
	''', None)
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
	and m._Marker_Type_key = 1
	and m._Marker_key = 3
	''', 'auto')
    for r in results:
        key = r['mgiID'] + r['accID']
        nonIEA_annotations.append(key)

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

    global mgi_to_uniprot
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
	ecValue = string.split(tokens[4], ',')

	mgi_to_uniprot[key] = []
	for v in value1:
	    mgi_to_uniprot[key].append(v)
	for v in value2:
	    mgi_to_uniprot[key].append(v)

    return 0

#
# Purpose: Read EC-to-GO file & create lookup
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

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

#
# Purpose: Read IP-to-GO file & create lookup
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def readIP2GO():

    #
    # parse ip2go file...one IP ID can have many GO mappings
    #

    global ip_to_go
    global ip2goFile
    global fpIP2GO, fpUNIPROT2IP

    ip2gore = re.compile("(^InterPro:(IPR[0-9]+)) +.* +> +GO:.* +; +(GO:[0-9]+)")

    fpIP2GO = open(ip2goFile,'r')

    for line in fpIP2GO.readlines():
        r = ip2gore.match(line)

        if (r is not None):

            ipid = r.group(2)         # IPR#####
            goid = r.group(3)         # GO:#####

            #
            # Exclude associations to these GO IDs:
            #    GO:0005575 cellular_component unknown
            #    GO:0005554 molecular_function unknown
            #    GO:0008150 biological_process unknown
            #
            if goid not in ['GO:0005575', 'GO:0003674', 'GO:0008150']:

                if not ip_to_go.has_key(ipid):
                    ip_to_go[ipid] = []
                ip_to_go[ipid].append(goid)

    #
    # lookup of uniprot ID -> ip id, ip id....
    #

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
# Purpose: Close files
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def closeFiles():

    if fpMGI2UNIPROT:
	fpMGI2UNIPROT.close()

    if fpEC2GO:
	fpEC2GO.close()

    if fpGOEC:
	fpGOEC.close()

    if fpIP2GO:
	fpIP2GO.close()

    if fpGOIP:
	fpGOIP.close()

    if fpUNIPROT2IP:
	fpUNIPROT2IP.close()

    return 0

#
# Purpose: Process EC-to-GO data & create annotation file
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def processEC2GO():

    global goECFile, fpGOEC

    #
    # Select all Marker/EC associations from MGD.
    # Some come from manual curation, some from the UniProt load.
    #
    # Generate a GO annotation file from the Marker/EC associations.
    #
    # Only consider loading a Marker/GO IEA EC annotation if a non-IEA GO annotation
    # to the same GO term does not already exist.
    #

    fpGOEC = open(goECFile, 'w')

    results = db.sql('''select markerID = a2.accID, accID = "EC:" + a.accID
                from ACC_Accession a, MRK_Marker m, ACC_Accession a2
                where a._MGIType_key = 2
                and a._LogicalDB_key = 8
                and a._Object_key = m._Marker_key
		and m._Organism_key = 1
                and m._Marker_Type_key = 1
		and a._Object_key = a2._Object_key
                and a2._LogicalDB_key = 1
		and a2.prefixPart = "MGI:"
		and a2.preferred = 1
		''', 'auto')

    for r in results:

	markerID = r['markerID']
	ec = r['accID']

        # if there is no EC-2-GO mapping for the EC ID, then skip it

        if not ec_to_go.has_key(ec):
            continue

	# for each EC-2-GO mapping....

	for goid in ec_to_go[ec]:

	    # if a non-IEA annotation exists, skip

	    nonIEAkey = markerID + goid
	    if nonIEAkey in nonIEA_annotations:
	        continue

	     # else we want to load this annotation.

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
# Purpose: Process IP-to-GO data & create annotation file
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def processIP2GO():

    global goIPFile, fpGOIP

    #
    # Select all Marker/UniProt associations from the Marker/UniProt association file.
    # Generate a GO annotation file from the Marker/InterPro associations.
    #
    # each marker has one-or-more uniprot ids (mgi_to_uniprot):
    #    each uniprot id has one-or-more interpro ids (uniprot_to_ip)
    #        each interpro id has one-or-more go ids (ip_to_go)
    #              go id 1
    #              go id 2
    #	           etc...
    #
    # Only consider loading a Marker/GO IEA InterPro annotation if a non-IEA GO annotation
    # to the same GO term does not already exist.
    #

    fpGOIP = open(goIPFile, 'w')

    markerIDs = mgi_to_uniprot.keys()
    markerIDs.sort()

    for m in markerIDs:

        #
        # for the given marker, collect a set of GO id -> interpro ids
	# the GO annotation loader is driven by Marker/GO id/set of interpro ids
	# we want one set of interpro ids per GO id per Marker
        #
    
        go_to_ip = {}		

        for uniprotVal in mgi_to_uniprot[m]:

            # if there is no uniprot_to_ip mapping, then skip it

            if not uniprot_to_ip.has_key(uniprotVal):
                continue

	    # for each UNIPROT-2-IP mapping....

	    for ipid in uniprot_to_ip[uniprotVal]:

                # if there is no ip_to_go mapping, then skip it

	        if not ip_to_go.has_key(ipid):
		    continue

	        # for each IP-2-GO mapping...

                for goid in ip_to_go[ipid]:

	            # if a non-IEA annotation exists, skip
	            nonIEAkey = m + goid
	            if nonIEAkey in nonIEA_annotations:
		        continue

		    # else we want to load this annotation.

		    ipidPrint = 'InterPro:' + ipid

	            if not go_to_ip.has_key(goid):
	                go_to_ip[goid] = []
                    if ipidPrint not in go_to_ip[goid]:
                        go_to_ip[goid].append(ipidPrint)

	#
	# the GO annotation loader is driven by Marker/GO id/set of interpro ids
	# we want one set of interpro ids per GO id per Marker
	#

        for goid in go_to_ip.keys():
            fpGOIP.write(goid + '\t' + \
		         m + '\t' + \
	      	         goIPRef + '\t' + \
	      	         goEvidence + '\t' + \
	      	         string.join(go_to_ip[goid], ',') + '\t' + \
	      	         '\t' + \
	      	         goEditor + '\t' + \
	      	         goDate + '\t' + \
		         goNote + '\n')

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

if processIP2GO() != 0:
    sys.exit(1)

closeFiles()
sys.exit(0)

