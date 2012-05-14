import sys
import os

#
# 05/14/2012    lec
#       - TR11071/add 'uniprotName' parsing
#

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
	self.isTrembl = 0
        self.ensemblID = []
        self.entrezgeneID = []
        self.pdbID = []
        self.ecID = []
        self.kwName = []
        self.interproID = []
        self.uniprotName = []


    #
    # The following methods are used to set/get the attributes.
    #

    def setUniProtID (self, uniprotID):
        self.uniprotID = uniprotID

    def getUniProtID (self):
        return self.uniprotID

    def getIsTrembl (self):
	return self.isTrembl

    #
    # Name (Name=)
    #

    def setUniProtName (self, uniprotName):
        self.uniprotName = uniprotName

    def getUniProtName (self):
        return self.uniprotName

    #
    # Ensembl ids
    #

    def addEnsemblID (self, ensemblID):
        self.ensemblID.append(ensemblID)

    def getEnsemblID (self):
        return self.ensemblID

    def hasEnsemblID (self, id):
        if self.ensemblID.count(id) > 0:
            return 1
        else:
            return 0

    #
    # EntrezGene ids
    #

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
    # PDB ids (protein data bank)
    #

    def addPDBID (self, pdbID):
        self.pdbID.append(pdbID)

    def getPDBID (self):
        return self.pdbID

    def hasPDBID (self, id):
        if self.pdbID.count(id) > 0:
            return 1
        else:
            return 0

    #
    # ED ids
    #

    def addECID (self, ecID):
        self.ecID.append(ecID)

    def getECID (self):
        return self.ecID

    def hasECID (self, id):
        if self.ecID.count(id) > 0:
            return 1
        else:
            return 0

    #
    # GO keyword name
    #

    def addKWName (self, kwName):
        self.kwName.append(kwName)

    def getKWName (self):
        return self.kwName

    def hasKWName (self, id):
        if self.kwName.count(id) > 0:
            return 1
        else:
            return 0

    #
    # InterPro ids
    #

    def addInterProID (self, interproID):
        self.interproID.append(interproID)

    def getInterProID (self):
        return self.interproID

    def hasInterProID (self, id):
        if self.interproID.count(id) > 0:
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
               '|entrezgeneID=' + ','.join(self.entrezgeneID) + '|' + \
               '|pdbID=' + ','.join(self.pdbID) + '|' + \
               '|ecID=' + ','.join(self.ecID) + '|' + \
               '|kwName=' + ','.join(self.kwName) + '|' + \
               '|interproID=' + ','.join(self.interproID) + '|' + \
	       '|uniprotName=' + self.uniprotName

