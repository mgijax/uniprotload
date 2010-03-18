import sys
import os

#
# CLASS: UniProtRecord
# IS: An object that holds specific attributes from a UniProt record.
# HAS: UniProt record attributes
# DOES: Nothing
#
class Record:

    #
    # Purpose: Constructor
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Initializes the attributes
    # Throws: Nothing
    #
    def __init__ (self):
        self.clear()


    #
    # Purpose: Clears the attributes
    # Returns: Nothing
    # Assumes: Nothing
    # Effects: Clears the attributes
    # Throws: Nothing
    #
    def clear (self):
        self.uniprotID = ''
        self.ensemblID = []
        self.entrezgeneID = []


    #
    # The following methods are used to set/get the attributes.
    #

    def setUniProtID (self, uniprotID):
        self.uniprotID = uniprotID

    def getUniProtID (self):
        return self.uniprotID

    def addEnsemblID (self, ensemblID):
        self.ensemblID.append(ensemblID)

    def getEnsemblID (self):
        return self.ensemblID

    def hasEnsemblID (self, id):
        if self.ensemblID.count(id) > 0:
            return 1
        else:
            return 0

    def addEntrezGeneID (self, entrezgeneID):
        self.entrezgeneID.append(entrezgeneID)

    def getEntrezGeneID (self):
        return self.entrezgeneID

    def hasEntrezGeneID (self, id):
        if self.entrezgeneID.count(id) > 0:
            return 1
        else:
            return 0


    #
    # Purpose: Return all the attributes as one string (for debugging).
    # Returns: String of all objects.
    # Assumes: Nothing
    # Effects: Nothing
    # Throws: Nothing
    #
    def debug (self):
        return '|uniprotID=' + self.uniprotID + \
               '|ensemblID=' + ','.join(self.ensemblID) + \
               '|entrezgeneID=' + ','.join(self.entrezgeneID) + '|'
