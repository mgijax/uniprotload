import sys
import os
import re

import UniProtRecord

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
            # Save the UniProt ID.
            #
            if self.line[0:2] == 'AC' and self.record.getUniProtID() == '':
                self.record.setUniProtID(re.split(';', self.line[5:])[0].strip())

            #
            # Save an Ensembl ID. If the input line looks like this:
            #
            # DR   Ensembl; ID1; ID2; ID3; Mus musculus.
            #
            # We want to extract any IDs that begin with 'ENSMUSG'. Do not
            # add an ID that has already been added.
            #
            if self.line[0:13] == 'DR   Ensembl;':
                for str in re.split(';',self.line[13:]):
                    if str.strip()[0:7] == 'ENSMUSG':
                        if not self.record.hasEnsemblID(str.strip()):
                            self.record.addEnsemblID(str.strip())

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
