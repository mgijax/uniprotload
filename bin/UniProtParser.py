import os
import re

import UniProtRecord

#
# 10/20/2014	lec
#	- TR11817/DE changes
#
# 06/04/2012	lec
#	- TR11071/remove 'uniprotName', add emblID instead
#
# 05/14/2012	lec
#	- TR11071/add 'uniprotName' parsing
#

#
# CLASS: Parser
# IS: An object that knows how to parse the mouse-only UniProt file and extract
#     specific attributes.
# HAS: A UniProt record object to hold attributes from one UniProt record.
# DOES: Parses the mouse-only UniProt file.
#
class Parser:

    #
    # Purpose: Constructor
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Initializes the file pointer and the UniProt record object.
    # Throws: Nothing
    #
    def __init__(self, fp):

        self.fp = fp

        #
        # Create a UniProt record object.
        #
        self.record = UniProtRecord.Record()


    #
    # Purpose: Parser the next record from the UniProt file and load the
    #          necessary attributes into the record object.
    # Returns: Next record object
    # Assumes: Nothing
    # Effects: Nothing
    # Throws: Nothing
    #
    def nextRecord (self):
        self.record.clear()

        #
        # Start reading the lines of the UniProt record and continue to process
        # the lines until the record terminator ("//") is found or EOF is
        # reached.
        #
        self.line = self.fp.readline()
        while self.line and self.line[0:2] != '//':
            self.line = self.line[:-1]

            #
            # Determine if the UniProt ID is a TrEMBL ID or not
            #
            if self.line[0:2] == 'ID':
                if self.line.find('Unreviewed;') >= 0:
                    self.record.isTrembl = 1

            #
            # Save the UniProt ID.
            #
            if self.line[0:2] == 'AC' and self.record.getUniProtID() == '':
                self.record.setUniProtID(re.split(';', self.line[5:])[0].strip())

            #
            # Save an Ensembl ID. If the input line looks like this:
            #
            # DR   Ensembl; ID1; ID2; ID3; Mus musculus.
            # DR   Ensembl; ID1; ID2; ID3; Mus musculus. [xxxxx]
            #
            # need to split by ";" and "."
            #
            # We want to extract any IDs that begin with 'ENSMUSG'. Do not
            # add an ID that has already been added.
            #
            if self.line[0:13] == 'DR   Ensembl;':
                for t1 in re.split(';',self.line[13:]):
                    if t1.strip()[0:7] == 'ENSMUSG':
                        for t2 in re.split('\.',t1):
                            if t2.strip()[0:7] == 'ENSMUSG':
                                if not self.record.hasEnsemblID(t2.strip()):
                                    self.record.addEnsemblID(t2.strip())

            #
            # Save an EntrezGene ID. If the input line looks like this:
            #
            # DR   GeneID; 12345; -.
            #
            # We want to extract the 12345. Do not add an ID that has already
            # been added.
            #
            if self.line[0:12] == 'DR   GeneID;':
                id = re.split(';', self.line[5:])[1].strip()
                if not self.record.hasEntrezGeneID(id):
                    self.record.addEntrezGeneID(id)

            #
            # Save an EMBL ID. If the input line looks like this:
            #
            # DR   EMBL; 12345; -.
            #
            # We want to extract the 12345. Do not add an ID that has already
            # been added.
            #
            if self.line[0:10] == 'DR   EMBL;':
                if self.line.find('mRNA') >= 0:
                  id = re.split(';', self.line[5:])[1].strip()
                  if not self.record.hasEMBLID(id):
                      self.record.addEMBLID(id)

            #
            # Save an PDB ID. If the input line looks like this:
            #
            # DR   PDB; 2PF4; X-ray; 3.10 A; A/B/C/D=1-589.
            #
            # We want to extract the 2PF4.
            #
            if self.line[0:9] == 'DR   PDB;':
                id = re.split(';', self.line[5:])[1].strip()
                if not self.record.hasPDBID(id):
                    self.record.addPDBID(id)

            #
            # Save an EC ID. If the input line looks like this:
            #
            # DE            EC=1.1.1.284;
            # DE            EC=2.7.11.21 {....};
            # note : the EC does not always appear at the same line number
            #
            # We want to extract the 2.3.1.41
            #
            # TR11817 : added "{...}" handling
            #
            if self.line[0:5] == 'DE   ':
                #if self.record.isTrembl == 0 and
                if self.line.find('EC=') >= 0:
                  id = re.split('=', self.line)[1].strip()
                  id = re.split(' {', id)[0]
                  id = str.replace(id.strip(), ';', '')
                  if not self.record.hasECID(id):
                      self.record.addECID(id)

            #
            # Save an UniProt/SwissProt Keyword Name. If the input line looks like this:
            #
            # KW   Acetylation; Alternative initiation; Cytoplasm;
            #
            # We want to extract any keyword.
            #
            if self.line[0:5] == 'KW   ':
                for s in re.split(';',self.line[5:]):
                    s = str.replace(s.strip(), '.', '')
                    if s.strip() != '':
                        if not self.record.hasKWName(s.strip()):
                            self.record.addKWName(s.strip())

            #
            # Save an InterPro ID. If the input line looks like this:
            #
            # DR   InterPro; IPR000308; 14-3-3.
            #
            # We want to extract the IPR000308. 
            #
            if self.line[0:14] == 'DR   InterPro;':
                id = re.split(';', self.line[5:])[1].strip()
                if not self.record.hasInterProID(id):
                    self.record.addInterProID(id)

            #
            # Read the next line from the UniProt file.
            #
            self.line = self.fp.readline()

        #
        # If the record terminator was found, return the record object.
        # Otherwise, EOF must have been reached, so return None.
        #
        if self.line[0:2] == '//':
            return self.record
        else:
            return None
