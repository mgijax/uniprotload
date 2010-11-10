#!/usr/local/bin/python
#
#
# Program: makeGOAnnot.py
#
# Original Author: Lori Corbani
#
# Purpose:
#
#	Create GO annotation files for the following areas:
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
#	  UNIPROT_ACC_ASSOC_FILE
#	  MGI_ACC_ASSOC_FILE
#
#         EC2GOFILE
#         GO_EC_ASSOC_FILE
#         GO_EC_ANNOT_REF
#
#         IP2GOFILE
#         GO_IP_ASSOC_FILE
#         GO_IP_ANNOT_REF
#
#         SPKW2GOFILE
#         GO_SPKW_ASSOC_FILE
#         GO_SPKW_ANNOT_REF
#
#         ANNOT_EVIDENCECODE
#         ANNOT_EDITOR
#         ANNOT_DATE
#	  ANNOT_NOTE
#	  ANNOT_NOTEPREFIX
#
# Inputs:
#
#       - UniProt load file (${MGI_UNIPROT_LOAD_FILE})
#	  1: mgi id
#	  2: swiss-prot id
#	  3: trembl id
#	  5: ec
#
#       - UniProt Acc files (${UNIPROT_ACC_ASSOC_FILE})
#
#      - MGI association file ($MGI_ACC_ASSOC_FILE)
#        to be used by the TableDataSet class. 
#        It has the following tab-delimited fields:
#
#        1) MGI ID (for a marker)
#        2) Marker Symbol
#        3) Marker Type
#        4) EntrezGene IDs and NBCI gene model IDs (comma-separated)
#        5) Ensembl gene model IDs (comma-separated)
#
#	- EC-2-GO file ($EC2GOFILE)
#
#	  EC:1 > GO:oxidoreductase activity ; GO:0016491
#
#	- IP-2-GO file ($IP2GOFILE)
#
#	  InterPro:IPR000003 Retinoid X receptor > GO:DNA binding ; GO:0003677
#
#	- SPKW-2-GO file ($SPKW2GOFILE)
#
#	  SP_KW:KW-0001 2Fe-2S > GO:2 iron, 2 sulfur cluster binding ; GO:0051537
#
#       - GO/EC Reference ($GO_EC_ANNOT_REF)
#
#       - GO/InterPro Reference ($GO_IP_ANNOT_REF)
#
#       - GO/SPKW Reference ($GO_SPKW_ANNOT_REF)
#
#       - GO Evidence ($ANNOT_EVIDENCECODE)
#
#       - GO Editor ($ANNOT_EDITOR)
#
#       - GO Date ($ANNOT_DATE)
#
# Outputs:
#
#	A tab-delimtied file, one for each of these areas:
#
#	GO/EC		J:72245	GO_EC_ASSOC_FILE
#	GO/InterPro	J:72247	GO_IP_ASSOC_FILE
#	GO/UniProt	J:60000	GO_SPKW_ASSOC_FILE
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
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Initialize variables.
#      2) Open files, read files and create lookups.
#      3) Process EC-to-GO data & create annotation file.
#      4) Process IP-to-GO data & create annotation file.
#      5) Process SPKW-to-GO data & create annotation file.
#      6) Close files.
#
# History:
#
# 11/10/2010	lec
#	- TR 10443/attach correct uniprot ids to notes (go_to_uniprot) for IP and SP annotations
#
# 08/23/2010	lec
#	- TR 5430/change nonIEA_annot from list to dictionary for speed
#	  and remove the test query from the openFiles/nonIEA_annot dictionary
#
# 05/26/2010	lec
#	- TR 10231/output should contain marker type 'gene' only
#
# 03/25/2010	lec
#	- TR 9777; original program "swissecload"
#
# 07/29/2008	lec
# 01/24/2007	lec
# 05/11/2005	lec
#	- TR 8877; only select markers of type "gene"
#	- TR 8122; added EC id to "inferred from" field for GO annotations
#	- TR 6790
#

import sys
import os
import re
import string
import db

# globals

# file name MGI_UNIPROT_LOAD_FILE
mgi_to_uniprotFile = None

# file name UNIPROT_ACC_ASSOC_FILE
uniprotFile = None

# file name MGI_ACC_ASSOC_FILE
mgi_to_markertypeFile = None

# file name EC2GOFILE
ec2goFile = None

# file name GO_EC_ASSOC_FILE
goECFile = None

# file name IP2GOFILE
ip2goFile = None

# file name GO_IP_ASSOC_FILE
goIPFile = None

# file name SPKW2GOFILE
spkw2goFile = None

# file name GO_SPKW_ASSOC_FILE
goSPKWFile = None

# variable name GO_EC_ANNOT_REF 
goECRef = None

# variable name GO_IP_ANNOT_REF
goIPRef = None

# variable name GO_SPKW_ANNOT_REF
goSPKWRef = None

# variable name ANNOT_EVIDENCECODE
annotEvidence = None

# variable name ANNOT_EDITOR
annotEditor = None

# variable name ANNOT_DATE
annotDate = None

# variable name ANNOT_NOTE
annotNote = None

# variable name ANNOT_NOTEPREFIX
annotNotePrefix = None

# MGI UniProt load mapping/SP/TR (MGI id -> UniProt id)
mgi_to_uniprot_sptr = {}

# MGI UniProt load mapping/SP only (MGI id -> UniProt id)
mgi_to_uniprot_sp = {}

# MGI / Marker Type (MGI id -> Marker Type)
mgi_to_markertype = {}

# EC to GO mapping (EC id -> GO id)
ec_to_go = {}		

# InterPro to GO mapping (InterPro id -> GO id)
ip_to_go = {}		

# uniprot keyword to GO mapping (SPKW name -> GO id)
spkw_to_go = {}		

# UniProt to InterPro mapping (UniProt id -> InterPro ids)
uniprot_to_ip = {}

# UniProt to SPKW mapping (UniProt id -> SPKW name)
uniprot_to_spkw = {}

# non-IEA MGI Marker/GO ID annotations
# where list key = mgiID + accID
nonIEA_annotations = {}

#
# Purpose: Initialization
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def initialize():
    global mgi_to_uniprotFile
    global mgi_to_markertypeFile
    global uniprotFile
    global ec2goFile, goECFile
    global ip2goFile, goIPFile
    global spkw2goFile, goSPKWFile
    global goECRef, goIPRef, goSPKWRef
    global annotEvidence, annotEditor, annotDate, annotNote, annotNotePrefix

    #
    #  initialize caches
    #

    db.useOneConnection(1)
    db.set_sqlLogFunction(db.sqlLogAll)

    mgi_to_uniprotFile = os.getenv('MGI_UNIPROT_LOAD_FILE')
    mgi_to_markertypeFile = os.getenv('MGI_ACC_ASSOC_FILE')

    uniprotFile = os.getenv('UNIPROT_ACC_ASSOC_FILE')

    ec2goFile = os.getenv('EC2GOFILE')
    goECFile = os.getenv('GO_EC_ASSOC_FILE')
    goECRef = os.environ['GO_EC_ANNOT_REF']

    ip2goFile = os.getenv('IP2GOFILE')
    goIPFile = os.getenv('GO_IP_ASSOC_FILE')
    goIPRef = os.environ['GO_IP_ANNOT_REF']

    spkw2goFile = os.getenv('SPKW2GOFILE')
    goSPKWFile = os.getenv('GO_SPKW_ASSOC_FILE')
    goSPKWRef = os.environ['GO_SPKW_ANNOT_REF']

    annotEvidence = os.environ['ANNOT_EVIDENCECODE']
    annotEditor = os.environ['ANNOT_EDITOR']
    annotDate = os.environ['ANNOT_DATE']
    annotNote = os.environ['ANNOT_NOTE']
    annotNotePrefix = os.environ['ANNOT_NOTEPREFIX']

    rc = 0

    #
    # Make sure the required environment variables are set.
    #
    if not mgi_to_uniprotFile:
        print 'Environment variable not set: MGI_UNIPROT_LOAD_FILE'
        rc = 1

    if not uniprotFile:
        print 'Environment variable not set: UNIPROT_ACC_ASSOC'
        rc = 1

    if not mgi_to_markertypeFile:
        print 'Environment variable not set: MGI_ACC_ASSOC_FILE'
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

    if not goIPFile:
        print 'Environment variable not set: GO_IP_ASSOC_FILE'
        rc = 1

    if not goIPRef:
        print 'Environment variable not set: GO_IP_ANNOTREF'
        rc = 1

    if not goSPKWFile:
        print 'Environment variable not set: GO_SPKW_ASSOC_FILE'
        rc = 1

    if not goSPKWRef:
        print 'Environment variable not set: GO_SPKW_ANNOTREF'
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

    if not annotNote:
        print 'Environment variable not set: ANNOT_NOTE'
        rc = 1

    if not annotNotePrefix:
        print 'Environment variable not set: ANNOT_NOTEPREFIX'
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

    global nonIEA_annotations

    readMGI2UNIPROT()
    readMGI2MARKERTYPE()
    readEC2GO()
    readIP2GO()
    readSPKW2GO()
    readUNIPROTACC()

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
	''', 'auto')
    for r in results:
        key = r['mgiID'] + r['accID']
        nonIEA_annotations[key] = []

    return 0

#
# Purpose: Read MGI-to-UniProt file & create lookup
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def readMGI2UNIPROT():

    #
    # parse mgi-to-uniprot1 file
    # parse mgi-to-uniprot2 file
    #
    # dictionary contains:
    #	key = MGI id
    #   value = list of uniprot ids, either SP or TrEMBL
    #
    # mgi_to_uniprot_sptr contains swissprot + trembl
    # mgi_to_uniprot_sp contains swissprot only
    #

    global mgi_to_uniprot_sptr, mgi_to_uniprot_sp
    global mgi_to_uniprotFile

    fp = open(mgi_to_uniprotFile,'r')

    lineNum = 0
    for line in fp.readlines():

	if lineNum == 0:
	    lineNum = lineNum + 1
	    continue

	tokens = string.split(line[:-1], '\t')
	key = tokens[0]
	value1 = string.split(tokens[1], ',')
	value2 = string.split(tokens[2], ',')

	# swissprot + trembl

	if not mgi_to_uniprot_sptr.has_key(key):
	    mgi_to_uniprot_sptr[key] = []

	for v in value1:
	    mgi_to_uniprot_sptr[key].append(v)
	for v in value2:
	    mgi_to_uniprot_sptr[key].append(v)

	# swissprot only

	if not mgi_to_uniprot_sp.has_key(key):
	    mgi_to_uniprot_sp[key] = []

	for v in value1:
	    mgi_to_uniprot_sp[key].append(v)

    fp.close()

    return 0

#
# Purpose: Read MGI-to-MarkerType file & create lookup
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def readMGI2MARKERTYPE():

    #
    # parse mgi-to-markertype file
    #
    # dictionary contains:
    #	key = MGI id
    #   value = marker type key
    #

    global mgi_to_markertype
    global mgi_to_markertypeFile

    fp = open(mgi_to_markertypeFile,'r')

    lineNum = 0
    for line in fp.readlines():

	if lineNum == 0:
	    lineNum = lineNum + 1
	    continue

	tokens = string.split(line[:-1], '\t')
	key = tokens[0]
	value = tokens[2]

	mgi_to_markertype[key] = value

    fp.close()

    return 0

#
# Purpose: Read EC-to-GO file & create lookup
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def readEC2GO():

    #
    # parse ec2go file...one EC ID can have many GO mappings
    #
    # dictionary contains:
    #   key = EC id
    #   value = list of GO ids
    #

    global ec_to_go, ec2goFile

    ec2gore = re.compile("(^EC:.+) +> +GO:.* +; +(GO:[0-9]+)")

    fp = open(ec2goFile,'r')

    for line in fp.readlines():

        r = ec2gore.match(line)

        if (r is not None):
            ecid = r.group(1)
            goid = r.group(2)
            if not ec_to_go.has_key(ecid):
                ec_to_go[ecid] = []
            ec_to_go[ecid].append(goid)

    fp.close()

    return 0

#
# Purpose: Read IP-to-GO file & create lookup
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def readIP2GO():

    #
    # parse ip2go file
    #
    # dictiionary contains:
    #	key = InterPro id (IPR#####)
    #   value = 2-member tuple of the expanded 
    #           InterPro:IPR####) and GO id (GO:#####)
    #
    # will use the expanded IPR ID in the annotation "inferred from" field
    #

    global ip_to_go
    global ip2goFile

    ip2gore = re.compile("(^InterPro:(IPR[0-9]+)) +.* +> +GO:.* +; +(GO:[0-9]+)")

    fp = open(ip2goFile,'r')

    for line in fp.readlines():

        r = ip2gore.match(line)

        if (r is not None):

            ipid = r.group(1)	      # IPR#####
            ipName = r.group(2)       # InterPro:IPR####
            goid = r.group(3)         # GO:#####

            #
            # Exclude associations to these GO IDs:
            #    GO:0005575 cellular_component unknown
            #    GO:0005554 molecular_function unknown
            #    GO:0008150 biological_process unknown
            #
            if goid not in ['GO:0005575', 'GO:0003674', 'GO:0008150']:

                if not ip_to_go.has_key(ipName):
                    ip_to_go[ipName] = []
                ip_to_go[ipName].append((ipid, goid))

    fp.close()

    return 0

#
# Purpose: Read SPKW-to-GO file & create lookup
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def readSPKW2GO():

    #
    # parse spkw2go file
    #
    # dictionary contains:
    #	key = SP keyword
    #   value = 2-member tuple of the expanded 
    #           SPKW id (SP_KW:KW-001) and GO id (GO:#####)
    #
    # will use the expanded SP KW id in the annotation "inferred from" field
    #

    global spkw_to_go
    global spkw2goFile

    spkw2gore = re.compile("(^SP_KW:KW-[0-9]+) (.+) +> +GO:.* +; +(GO:[0-9]+)")

    fp = open(spkw2goFile,'r')

    for line in fp.readlines():

        r = spkw2gore.match(line)

        if (r is not None):

            spkwid = r.group(1)        # SP_KW:####
            spkwName = r.group(2)      # "Cytoplasm,Phosphoprotein"
            goid = r.group(3)        # GO:#####

            if not spkw_to_go.has_key(spkwName):
                spkw_to_go[spkwName] = []
            spkw_to_go[spkwName].append((spkwid, goid))

    fp.close()

    return 0

#
# Purpose: Read UniProt-to-Acc file & create lookups
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def readUNIPROTACC():

    #
    # parse UniProt-to-InterPro associations via the UniProt/Acc file
    #
    # dictionary contains:
    #	key = UniProt id
    #	value = list of InterPro ids (IPR#####)
    #
    # parse UniProt-to-SPKW associations via the UniProt/Acc file
    #
    # dictionary contains:
    #	key = UniProt id
    #   value = list of SPKW key words
    #           (for example: 'Cell membrane')
    #

    fp = open(uniprotFile,'r')

    for line in fp.readlines():
	tokens = string.split(line[:-1], '\t')
	key = tokens[0]

	# not all uniprot ids have interpro ids...
	if len(tokens[5]) > 0:
	    values = string.split(tokens[5], ',')
	    if not uniprot_to_ip.has_key(key):
	        uniprot_to_ip[key] = []
	    for v in values:
	        uniprot_to_ip[key].append(v)

	# not all uniprot ids have spkw ids...
	if len(tokens[6]) > 0:
	    values = string.split(tokens[6], ',')
	    if not uniprot_to_spkw.has_key(key):
	        uniprot_to_spkw[key] = []
	    for v in values:
	        uniprot_to_spkw[key].append(v)

    fp.close()

    return 0

#
# Purpose: Process EC-to-GO data & create annotation file
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def processEC2GO():

    global goECFile

    #
    # Select all Marker/EC associations from MGD.
    # Some come from manual curation, some from the UniProt load.
    #
    # Generate a GO annotation file from the Marker/EC associations.
    #
    # Only consider loading a Marker/GO IEA EC annotation if a non-IEA GO annotation
    # to the same GO term does not already exist.
    #
    # for each Marker/EC association in MGD:
    #	if there is no EC-2-GO mapping for the EC ID, then skip it
    #   if the marker is not of type 'gene', then skip it
    #	else for each EC-2-GO mapping....
    #      if a non-IEA annotation exists, skip
    #      else we want to load this annotation
    #

    fp = open(goECFile, 'w')

    results = db.sql('''select markerID = a2.accID, accID = "EC:" + a.accID
                from ACC_Accession a, MRK_Marker m, ACC_Accession a2
                where a._MGIType_key = 2
                and a._LogicalDB_key = 8
                and a._Object_key = m._Marker_key
		and m._Organism_key = 1
                and m._Marker_Type_key = 1
		and a._Object_key = a2._Object_key
		and a2._MGIType_key = 2
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

	# if the marker is not of type 'gene', then skip it
	if mgi_to_markertype[markerID] != '1':
	    continue

	# for each EC-2-GO mapping....

	for goid in ec_to_go[ec]:

	    # if a non-IEA annotation exists, skip

	    nonIEAkey = markerID + goid
	    if nonIEA_annotations.has_key(nonIEAkey):
	        continue

	     # else we want to load this annotation.

	    fp.write(goid + '\t' + \
		         markerID + '\t' + \
	      	         goECRef + '\t' + \
	      	         annotEvidence + '\t' + \
	      	         ec + '\t' + \
	      	         '\t' + \
	      	         annotEditor + '\t' + \
	      	         annotDate + '\t' + \
	      	         '\n')

    fp.close()

    return 0

#
# Purpose: Process IP-to-GO data & create annotation file
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def processIP2GO():

    global goIPFile

    #
    # Select all Marker/UniProt associations from the Marker/UniProt association file.
    # Generate a GO annotation file from the Marker/InterPro associations.
    #
    # each marker has one-or-more uniprot ids (mgi_to_uniprot_sp):
    #    each uniprot id has one-or-more interpro ids (uniprot_to_ip)
    #        each interpro id has one-or-more go ids (ip_to_go)
    #              go id 1
    #              go id 2
    #	           etc...
    #
    # Uses mgi_to_uniprot_sp, swissprot only.
    # Only consider loading a Marker/GO IEA InterPro annotation if a non-IEA GO annotation
    # to the same GO term does not already exist.
    #
    # for each Marker/UniProt association in the Marker/UniProt association file:
    #   if the marker is not of type 'gene', then skip it
    # 	for the given marker, collect a set of GO id -> interpro ids
    # 	the GO annotation loader is driven by Marker/GO id/set of interpro ids
    # 	we want one set of interpro ids per GO id per Marker
    #	
    #	for each uniProt value in the MGI-to-UniProtSP
    #		if there is no uniprot_to_ip mapping, then skip
    #		for each UNIPROT-2-IP mapping....
    #			if a non-IEA annotation exists, skip
    #			else we want to load this annotation
    #

    fp = open(goIPFile, 'w')

    markerIDs = mgi_to_uniprot_sp.keys()
    markerIDs.sort()

    for m in markerIDs:

        #
        # for the given marker, collect a set of GO id -> interpro ids
	# the GO annotation loader is driven by Marker/GO id/set of interpro ids
	# we want one set of interpro ids per GO id per Marker
        #
    
	# if the marker is not of type 'gene', then skip it
	if mgi_to_markertype[m] != '1':
	    continue

        go_to_ip = {}		

	# the uniprot id where this interpro id was found
        go_to_uniprot = {}		

        for uniprotVal in mgi_to_uniprot_sp[m]:

            # if there is no uniprot_to_ip mapping, then skip it

            if not uniprot_to_ip.has_key(uniprotVal):
                continue

	    # for each UNIPROT-2-IP mapping....

	    for ipName in uniprot_to_ip[uniprotVal]:

                # if there is no ip_to_go mapping, then skip it

	        if not ip_to_go.has_key(ipName):
		    continue

	        # for each IP-2-GO mapping...

                for r in ip_to_go[ipName]:

		    ipid = r[0]
		    goid = r[1]

	            # if a non-IEA annotation exists, skip
	            nonIEAkey = m + goid
	            if nonIEA_annotations.has_key(nonIEAkey):
		        continue

		    # else we want to load this annotation.

	            if not go_to_ip.has_key(goid):
	                go_to_ip[goid] = []
                    if ipid not in go_to_ip[goid]:
                        go_to_ip[goid].append(ipid)

	            if not go_to_uniprot.has_key(goid):
	                go_to_uniprot[goid] = []
                    if annotNotePrefix + uniprotVal not in go_to_uniprot[goid]:
                        go_to_uniprot[goid].append(annotNotePrefix + uniprotVal)

	#
	# the GO annotation loader is driven by Marker/GO id/set of interpro ids
	# we want one set of interpro ids per GO id per Marker
	#

        for goid in go_to_ip.keys():

	    # ip list must be <= 255 to fit into inferredFrom field
	    #while (string.join(go_to_ip[goid], ',') > 255)
	    #ipList = string.join(go_to_ip[goid], ',')
	    #while ipList > 255:
	    #    go_to_ip[goid].remove(ipid)
	    #    ipList = string.join(go_to_ip[goid], ',')
            #for i in go_to_ip[goid]:
	    #    if len(ipList + ',' + i) > 255:
	    #        break
	    #    ipList = i + ','
	    #        ipList[:-1]

            fp.write(goid + '\t' + \
		     m + '\t' + \
	      	     goIPRef + '\t' + \
	      	     annotEvidence + '\t' + \
	      	     string.join(go_to_ip[goid], ',') + '\t' + \
	      	     '\t' + \
	      	     annotEditor + '\t' + \
	      	     annotDate + '\t' + \
	      	     annotNote + string.join(go_to_uniprot[goid], ':') + '\n')

    fp.close()

    return 0

#
# Purpose: Process SPKW-to-GO data & create annotation file
# Returns: 1 if file does not exist or is not readable, else 0
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#

def processSPKW2GO():

    global goSPKWFile

    #
    # Select all Marker/UniProt associations from the Marker/UniProt association file.
    # Generate a GO annotation file from the Marker/SPKW associations.
    #
    # each marker has one-or-more uniprot ids (mgi_to_uniprot_sptr):
    #    if the marker is not of type 'gene', then skip it
    #    each uniprot id has one-or-more sp-kw ids (uniprot_to_spkw)
    #        each sp-kw id has one-or-more go ids (spkw_to_go)
    #              go id 1
    #              go id 2
    #	           etc...
    #
    # Uses mgi_to_uniprot_sptr, swissprot + trembl.
    # Only consider loading a Marker/GO IEA SP-KW annotation if a non-IEA GO annotation
    # to the same GO term does not already exist.
    #

    fp = open(goSPKWFile, 'w')

    markerIDs = mgi_to_uniprot_sptr.keys()
    markerIDs.sort()

    for m in markerIDs:

	# if the marker is not of type 'gene', then skip it
	if mgi_to_markertype[m] != '1':
	    continue

        #
        # for the given marker, collect a set of GO id -> SP-KW ids
	# the GO annotation loader is driven by Marker/GO id/set of SP-KW ids
	# we want one set of SP-KW ids per GO id per Marker
        #
    
        go_to_spkw = {}		

	# the uniprot id where this SP-KW id was found
        go_to_uniprot = {}		

        for uniprotVal in mgi_to_uniprot_sptr[m]:

            # if there is no uniprot_to_spkw mapping, then skip it

            if not uniprot_to_spkw.has_key(uniprotVal):
                continue

	    # for each UNIPROT-2-SPKW mapping....

	    for spkwName in uniprot_to_spkw[uniprotVal]:

                # if there is no spkw_to_go mapping, then skip it

	        if not spkw_to_go.has_key(spkwName):
		    continue

	        # for each SPKW-2-GO mapping...

                for r in spkw_to_go[spkwName]:

		    spkwid = r[0]
		    goid = r[1]

	            # if a non-IEA annotation exists, skip
	            nonIEAkey = m + goid
	            if nonIEA_annotations.has_key(nonIEAkey):
		        continue

		    # else we want to load this annotation.

	            if not go_to_spkw.has_key(goid):
	                go_to_spkw[goid] = []
                    if spkwid not in go_to_spkw[goid]:
                        go_to_spkw[goid].append(spkwid)

	            if not go_to_uniprot.has_key(goid):
	                go_to_uniprot[goid] = []
                    if annotNotePrefix + uniprotVal not in go_to_uniprot[goid]:
                        go_to_uniprot[goid].append(annotNotePrefix + uniprotVal)

	#
	# the GO annotation loader is driven by Marker/GO id/set of SP-KW ids
	# we want one set of SP-KW ids per GO id per Marker
	#

        for goid in go_to_spkw.keys():
            fp.write(goid + '\t' + \
		     m + '\t' + \
	      	     goSPKWRef + '\t' + \
	      	     annotEvidence + '\t' + \
	      	     string.join(go_to_spkw[goid], ',') + '\t' + \
	      	     '\t' + \
	      	     annotEditor + '\t' + \
	      	     annotDate + '\t' + \
	      	     annotNote + string.join(go_to_uniprot[goid], ':') + '\n')

    fp.close()

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

if processSPKW2GO() != 0:
    sys.exit(1)

sys.exit(0)

