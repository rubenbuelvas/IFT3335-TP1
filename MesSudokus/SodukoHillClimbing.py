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
##   values is a dict of possible values, e.g. {'A1':'12349', 'A2':'8', ...} #DGSCRAP

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

global counttotalsearches, countnakedimprovements
counttotalsearches = 0
countnakedimprovements = 0 #Number of naked pairs or triples found

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

################ Display as 2-D grid ################
def displaygrid(grid):
    """Display these values as a 2-D grid."""
    width = 1+max(len(grid[i]) for i in range(80))
    line = '+'.join(['-'*(width*3)]*3)
    for r in rows:
        print (''.join(grid[1].center(width)+('|' if c in '36' else '') #DGHERE MUST REMOVE the 1
                      for c in cols))
        if r in 'CF': print(line)

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

# def shuffled(seq):
#     "Return a randomly shuffled copy of the input sequence."
#     seq = list(seq)
#     random.shuffle(seq)
#     return seq

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

################ Main routine ################
if __name__ == '__main__':
    test()
    grid2 = '4.....8.5' + '.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......' #DGSCRAP
    print(f"grid_values(grid2)={grid_values(grid2)}")
    displaygrid(grid2)
    #print(f"parse_grid(grid2)={parse_grid(grid2)}")
    print('Must remove #DGSCRAP')

## References used:
## http://www.scanraid.com/BasicStrategies.htm
## http://www.sudokudragon.com/sudokustrategy.htm
## http://www.krazydad.com/blog/2005/09/29/an-index-of-sudoku-strategies/
## http://www2.warwick.ac.uk/fac/sci/moac/currentstudents/peter_cock/python/sudoku/
## https://www.sudokuoftheday.com/techniques/naked-pairs-triples/ (DG)



