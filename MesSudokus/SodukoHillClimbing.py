## Hill climing approach to solve a sudoku puzzle
## Inspired by Stochastic search / optimization methods from https://en.wikipedia.org/wiki/Sudoku_solving_algorithms
## Initial code copied from  http://norvig.com/sudoku.html

## Throughout this program we have:
##   r is a row,    e.g. 'A'
##   c is a column, e.g. '3'
##   s is a square, e.g. 'A3'
##   d is a digit,  e.g. '9'
##   u is a unit,   e.g. ['A1','B1','C1','D1','E1','F1','G1','H1','I1']
##   grid is a grid,e.g. 81 non-blank chars, e.g. starting with '.18...7...
##   grid_values is a dict of {square: char} with '0' or '.' for empties."""

##   values is a dict of possible values, e.g. {'A1':'12349', 'A2':'8', ...} #DGSCRAP

import re #DG Will be used for substring removal

def cross(A, B):
    "Cross product of elements in A and elements in B."
    return [a+b for a in A for b in B]

digits   = '123456789'
rows     = 'ABCDEFGHI'
cols     = digits
squares  = cross(rows, cols)
unitlist = ([cross(rows, c) for c in cols] +
            [cross(r, cols) for r in rows] +
            [cross(rs, cs) for rs in ('ABC','DEF','GHI') for cs in ('123','456','789')])
units = dict((s, [u for u in unitlist if s in u])
             for s in squares)
peers = dict((s, set(sum(units[s],[]))-set([s]))
             for s in squares)

global counttotalsearches, countnakedimprovements, emptydigits
counttotalsearches = 0
countnakedimprovements = 0 #Number of naked pairs or triples found
emptydigits = '0.'

#Text color management
from colorama import Fore, Back, Style #DGREVIEW
colorBrightGreenOnBlack = "\033[1;32;40m" #DG from https://ozzmaker.com/add-colour-to-text-in-python/
# print(Fore.BLUE + displaystring) #DGTEMP
# print("\033[1;32;40m Bright Green on black  \033[1;31;43m Red on yellow \033[1;34;42m Blue on green \033[1;37;40m") #DGTEMP

################ Unit Tests ################
def test():
    "A set of tests that must pass."
    assert len(squares) == 81
    assert len(unitlist) == 27
    assert all(len(units[s]) == 3 for s in squares)
    assert all(len(peers[s]) == 20 for s in squares)
    assert units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'],
                           ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
                           ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']]
    assert peers['C2'] == set(['A2', 'B2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2',
                               'C1', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9',
                               'A1', 'A3', 'B1', 'B3'])
    print ('All tests pass.')

################ Parse a Grid ################
# def parse_grid(grid):
#     """Convert grid to a dict of possible values, {square: digits}, or
#     return False if a contradiction is detected."""
#     ## To start, every square can be any digit; then assign values from the grid.
#     values = dict((s, digits) for s in squares)
#     for s,d in grid_values(grid).items():
#         if d in digits and not assign(values, s, d):
#             return False ## (Fail if we can't assign d to square s.)
#     return values

def grid_values(grid):
    """Convert grid into a dict of {square: char} with '0' or '.' for empties.""" #DG example: {'A1': '4', 'A2': '.', 'A3': '.', 'A4': '.', 'A5': '.', 'A6': '.', 'A7': '8', 'A8': '.', 'A9': ...
    chars = [c for c in grid if c in digits or c in '0.']
    assert len(chars) == 81
    return dict(zip(squares, chars))

################ Constraint Propagation ################ #DGTEMP Should we call this differently?
#def assigndigit(grid, s, d)
#"""Will return a new grid with the digit added in the specified square, and  ."""
#    newgrid

def fillgridrandomly(initialgrid):
    """Will return a new grid with all empty squares filled randomly without putting the same digit twice in a 3x3 unit."""
    # Reminder:   units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'], #column
    #                             ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'], #line
    #                             ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']] #unit 3x3
    initialgridvalues = grid_values(initialgrid) # dictionnary of initial values. Ex: {'A1': '4', 'A2': '.', 'A3': '.', 'A4': '.', 'A5': '.', 'A6': '.', 'A7': '8', 'A8': '.', 'A9': '5', ... }
    newgrid = initialgrid

    #Go through all 3x3 units and fill empty squares with random unused digits
    firstsquaresofunit = cross('ADG', '147') # one square in each unit: ['A1', 'A4', 'A7', 'D1', 'D4', 'D7', 'G1', 'G4', 'G7']
    for fsou in firstsquaresofunit: #loop through the 9 units
        currentunit = units[fsou][2]

        #loop trough all squares within a unit in order to extract initial squares with digits and digits used
        listofsquareswithinitialvalue, listofsquareswithoutvalue, digitsused = [], [], ''
        for s in currentunit:
            d = initialgridvalues[s]
            if d in emptydigits: # no value      emptydigits = '0.'
                listofsquareswithoutvalue.append(s)
            else:
                listofsquareswithinitialvalue.append(s)
                digitsused += d #capture all values from initial grid (cannot be replaced)

        #Fill empty squares randomly
        digitsused = shuffled(digitsused)
        print(f"firstsquaresofunit={fsou} - currentunit = {currentunit} - digitsused={digitsused} - listofsquareswithinitialvalue={listofsquareswithinitialvalue}")

        #for s in listofsquareswithoutvalue:
        #    newgrid = assigndigit(s, digitsused.pop())  #DG could be replaced by a function assigndigit that could also update other things if needed.
        #DGHERE


    print(f"firstsquaresofunit={firstsquaresofunit}")
    # for r in rows step 3:
    #     for c in cols step 3:
    #         print(f"RC={r+c}")


    #print(f"unitlist['A1']={unitlist['A1']}")
    print(f"units['A1']={units['A1']}")
    print(f"units['A1'][2]={units['A1'][2]}")




    print("newgrid WITH FUN: %s", newgrid)
    print("initialgrid NO FUN: %s", initialgrid)
    return newgrid
    


################ Display as 2-D grid ################
def displaygrid(initialgrid, currentgrid, showconflicts=True):
    """Display these values as a 2-D grid. If only display a initialgrid, you can pass currentgrid = initialgrid"""
    width = 3 # No need to display the possible values
    line = '+'.join(['-'*(width*3)]*3)
    i = 0 #the position between 0 and 80 of the square in the 9x9 grid

    displaystring = ''
    for r in rows:
        for c in cols:
            displaystring += (Back.BLACK if initialgrid[i] not in emptydigits else Style.RESET_ALL) #DG will highlight numbers from initial grid   emptydigits = '0.'
            displaystring += ' ' + currentgrid[i] + ' '
            displaystring += Style.RESET_ALL +  ('|' if c in '36' else '') + ('\n' if c in '9' else '') #display for a column
            i += 1
        if r in 'CF': displaystring = displaystring + line + '\n'

    print(displaystring)
    print(currentgrid)  # DGTEMP

        #print (''.join(grid[i].center(width)+('|' if c in '36' else '') #DGHERE MUST REMOVE the 1
        #              for c in cols))
        #i += 1
        #if r in 'CF': print(line)

# def display(values):
#     """Display these values as a 2-D grid."""
#     width = 1+max(len(values[s]) for s in squares)
#     line = '+'.join(['-'*(width*3)]*3)
#     for r in rows:
#         print (''.join(values[r+c].center(width)+('|' if c in '36' else '')
#                       for c in cols))
#         if r in 'CF': print(line)

################ Utilities ################
# def some(seq):
#     "Return some element of seq that is true."
#     for e in seq:
#         if e: return e
#     return False

def from_file(filename, sep='\n'):
    "Parse a file into a list of strings, separated by sep."
    return open(filename).read().strip().split(sep)

def shuffled(seq):
    "Return a randomly shuffled copy of the input sequence."
    seq = list(seq)
    random.shuffle(seq)
    return seq

def filterTheDict(dictObj, callback): #DGTEMP - Not useful anymore
    """ Fonction copied from https://thispointer.com/python-filter-a-dictionary-by-conditions-on-keys-or-values/
    Iterate over all the key value pairs in dictionary and call the given
    callback function() on each pair. Items for which callback() returns True,
    add them to the new dictionary. In the end return the new dictionary."""
    newDict = dict()
    # Iterate over all the items in dictionary
    for (key, value) in dictObj.items():
        # Check if item satisfies the given condition then add to new dict
        if callback((key, value)):
            newDict[key] = value
    return newDict

################ System test ################

import time, random

# def solve_all(grids, name='', showif=0.0, searchMethod='ToSpecify'):
#     """Attempt to solve a sequence of grids. Report results.
#     When showif is a number of seconds, display puzzles that take longer.
#     When showif is None, don't display any puzzles."""
#     global counttotalsearches, countnakedimprovements #DGTEMP
#     counttotalsearches = 0  #DGTEMP the total of searches
#     countnakedimprovements = 0 #DGTEMP the total of searches

#     def time_solve(grid):
#         #start = time.clock()
#         start = time.process_time()
#         values = solve(grid, searchMethod)
#         t = time.process_time()-start
#
#         #display(grid_values(grid)) #DGREMOVED
#         #if values: display(values) #DGREMOVED
#
#         ## Display puzzles that take long enough
#         if showif is not None and t > showif:
#             display(grid_values(grid))
#             if values: display(values)
#             print ('(%.2f seconds)\n' % t)
#         return (t, solved(values))
#
#     if searchMethod not in searchMethods: raise ValueError(f"Unknown search method {searchMethod}. Available search methods are {searchMethods}")  # DGNEW
#
#     times, results = zip(*[time_solve(grid) for grid in grids])
#     N = len(grids)
#
#     #DG Will avoid division by zero if time is too short (0.0).
#     if sum(times) != 0.0:
#         hz = N / sum(times)
#     else:
#         hz = 999
#
#     if N >= 1:
# #        print ("Solved %d of %d %s puzzles (avg %.2f secs (%d Hz), max %.2f secs)." % (
# #            sum(results), N, name, sum(times)/N, N/sum(times), max(times))) #DG REMOVED
#         print ("Solved %d of %d %s puzzles in %.2f secs (avg %.2f secs (%d Hz), max %.2f secs). Total searches %d - Naked improvements %d - %s" % (
#             sum(results), N, name, sum(times), sum(times)/N, hz, max(times), counttotalsearches, countnakedimprovements, searchMethod)) #DGNEW Added parameter for search method

def solved(values):
    "A puzzle is solved if each unit is a permutation of the digits 1 to 9."
    def unitsolved(unit): return set(values[s] for s in unit) == set(digits)
    return values is not False and all(unitsolved(unit) for unit in unitlist)

# def random_puzzle(N=17):
#     """Make a random puzzle with N or more assignments. Restart on contradictions.
#     Note the resulting puzzle is not guaranteed to be solvable, but empirically
#     about 99.8% of them are solvable. Some have multiple solutions."""
#     values = dict((s, digits) for s in squares)
#     for s in shuffled(squares):
#         if not assign(values, s, random.choice(values[s])):
#             break
#         ds = [values[s] for s in squares if len(values[s]) == 1]
#         if len(ds) >= N and len(set(ds)) >= 8:
#             return ''.join(values[s] if len(values[s])==1 else '.' for s in squares)
#     return random_puzzle(N) ## Give up and make a new puzzle


################ Main routine ################
if __name__ == '__main__':
    test()
    grid2 = '4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......' #DGSCRAP
    gridSCRAP = '4551158.5.3..........7..111.2.....6.....8.4......1..222..6.3.7.5..2.....1.4......'  # DGSCRAP
    print(f"grid_values(grid2)={grid_values(grid2)}")
    displaygrid(grid2, gridSCRAP)
    #print(f"parse_grid(grid2)={parse_grid(grid2)}")
    displaygrid(grid2, grid2)
    gridSCRAP = fillgridrandomly(grid2)
    print('grid2: %s', grid2)
    #print('gridSCRAP: %s', gridSCRAP)
    print('Must remove #DGSCRAP + rule for color management + SHOWCONFLICTS')

## References used:
## http://www.scanraid.com/BasicStrategies.htm
## http://www.sudokudragon.com/sudokustrategy.htm
## http://www.krazydad.com/blog/2005/09/29/an-index-of-sudoku-strategies/
## http://www2.warwick.ac.uk/fac/sci/moac/currentstudents/peter_cock/python/sudoku/
## https://www.sudokuoftheday.com/techniques/naked-pairs-triples/ (DG)



