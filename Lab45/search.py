"""
In search.py, you will implement Backtracking and AC3 searching algorithms
for solving Sudoku problem which is called by sudoku.py
"""

from csp import *
from copy import deepcopy
import util

def Backtracking_Search(csp):
    """
    Backtracking search initialize the initial assignment
    and calls the recursive backtrack function
    """
    # First run AC3 to reduce the domains
    AC3(csp)

    # Build initial assignment from cells that already have a single value
    assignment = {}
    for var in csp.variables:
        if len(csp.values[var]) == 1:
            assignment[var] = csp.values[var]

    return Recursive_Backtracking(assignment, csp)

def Recursive_Backtracking(assignment, csp):
    """
    The recursive function which assigns value using backtracking
    """
    if isComplete(assignment):
        return assignment

    var = Select_Unassigned_Variables(assignment, csp)

    for value in Order_Domain_Values(var, assignment, csp):
        if isConsistent(var, value, assignment, csp):
            assignment[var] = value
            # Save current domain values for restoration on backtrack
            saved_values = deepcopy(csp.values)
            inferences = Inference(assignment, {}, csp, var, value)
            if inferences != "FAILURE":
                result = Recursive_Backtracking(assignment, csp)
                if result != "FAILURE":
                    return result
            # Undo: remove assignment and restore domains
            del assignment[var]
            csp.values = saved_values

    return "FAILURE"

def Inference(assignment, inferences, csp, var, value):
    """
    Forward checking using concept of Inferences
    """

    inferences[var] = value

    for neighbor in csp.peers[var]:
        if neighbor not in assignment and value in csp.values[neighbor]:
            if len(csp.values[neighbor]) == 1:
                return "FAILURE"

            remaining = csp.values[neighbor] = csp.values[neighbor].replace(value, "")

            if len(remaining) == 1:
                flag = Inference(assignment, inferences, csp, neighbor, remaining)
                if flag == "FAILURE":
                    return "FAILURE"

    return inferences

def Order_Domain_Values(var, assignment, csp):
    """
    Returns string of values of given variable
    """
    return csp.values[var]

def Select_Unassigned_Variables(assignment, csp):
    """
    Selects new variable to be assigned using minimum remaining value (MRV)
    """
    unassigned_variables = dict((squares, len(csp.values[squares])) for squares in csp.values if squares not in assignment.keys())
    mrv = min(unassigned_variables, key=unassigned_variables.get)
    return mrv

def isComplete(assignment):
    """
    Check if assignment is complete
    """
    return set(assignment.keys()) == set(squares)

def isConsistent(var, value, assignment, csp):
    """
    Check if assignment is consistent
    """
    for neighbor in csp.peers[var]:
        if neighbor in assignment.keys() and assignment[neighbor] == value:
            return False
    return True

def forward_checking(csp, assignment, var, value):
    csp.values[var] = value
    for neighbor in csp.peers[var]:
        csp.values[neighbor] = csp.values[neighbor].replace(value, '')

def AC3(csp):
    """
    AC-3 arc consistency algorithm.
    Reduces domains by enforcing arc consistency on all constraints.
    """
    queue = list(csp.constraints)

    while queue:
        (xi, xj) = queue.pop(0)
        if Revise(csp, xi, xj):
            if len(csp.values[xi]) == 0:
                return False
            for peer in csp.peers[xi]:
                if peer != xj:
                    queue.append((peer, xi))
    return True

def Revise(csp, xi, xj):
    """
    Remove values from the domain of xi that are inconsistent with xj.
    Returns True if the domain of xi was revised.
    """
    revised = False
    for value in csp.values[xi]:
        # If no value in xj's domain allows xi to take this value
        if not any(v != value for v in csp.values[xj]):
            csp.values[xi] = csp.values[xi].replace(value, '')
            revised = True
    return revised

def display(values):
    """
    Display the solved sudoku on screen
    """
    width = 1 + max(len(values[s]) for s in squares)
    line = '+'.join(['-' * (width * 3)] * 3)
    for row in rows:
        if row in 'DG':
            print(line)
        print(''.join(
            values[row + col].center(width) + ('|' if col in '36' else '')
            for col in cols
        ))

def write(values):
    """
    Write the string output of solved sudoku to file
    """
    output = ""
    for variable in squares:
        output = output + values[variable]
    return output