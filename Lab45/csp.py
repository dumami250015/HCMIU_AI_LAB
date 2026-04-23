# CLASS DESCRIPTION FOR CONSTRAINT SATISFACTION PROBLEM (CSP)

from util import *

class csp:

    # INITIALIZING THE CSP
    def __init__(self, domain=digits, grid=""):
        """
        Unitlist consists of the 27 lists of peers
        Units is a dictionary consisting of the keys and the corresponding lists of peers
        Peers is a dictionary consisting of the 81 keys and the corresponding set of 27 peers
        Constraints denote the various all-different constraints between the variables
        """
        self.variables = squares

        # 27 units: 9 rows + 9 columns + 9 boxes
        self.unitlist = ([cross(rows, c) for c in cols] +
                         [cross(r, cols) for r in rows] +
                         [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI')
                                        for cs in ('123', '456', '789')])

        # For each square, the list of units it belongs to
        self.units = dict((s, [u for u in self.unitlist if s in u])
                          for s in squares)

        # For each square, the set of all peers (squares sharing a unit)
        self.peers = dict((s, set(sum(self.units[s], [])) - {s})
                          for s in squares)

        # Binary all-different constraints: pairs of squares sharing a unit
        self.constraints = {(variable, peer)
                            for variable in squares
                            for peer in self.peers[variable]}

        # Initialize domain values from the grid string
        self.values = self.getDict(grid)



    def getDict(self, grid=""):
        """
        Getting the string as input and returning the corresponding dictionary
        """
        i = 0
        values = dict()
        for cell in self.variables:
            if grid[i] != '0':
                values[cell] = grid[i]
            else:
                values[cell] = digits
            i = i + 1
        return values