## Solve Every Sudoku Puzzle

## See http://norvig.com/sudoku.html

## Throughout this program we have:
##   r is a row,    e.g. 'A'
##   c is a column, e.g. '3'
##   s is a square, e.g. 'A3'
##   d is a digit,  e.g. '9'
##   u is a unit,   e.g. ['A1','B1','C1','D1','E1','F1','G1','H1','I1']
##   grid is a grid,e.g. 81 non-blank chars, e.g. starting with '.18...7...
##   values is a dict of possible values, e.g. {'A1':'12349', 'A2':'8', ...}

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

searchMethods = {'Brute Force', 'Norvig Heuristic', 'Norvig Improved'}  #DGNEW the available search methods
global counttotalsearches, countnakedimprovements #DGTEMP The total number of searches and the maximum depth (not sure if implemented correctly)
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

def parse_grid(grid):
    """Convert grid to a dict of possible values, {square: digits}, or
    return False if a contradiction is detected."""
    ## To start, every square can be any digit; then assign values from the grid.
    values = dict((s, digits) for s in squares)
    for s,d in grid_values(grid).items():
        if d in digits and not assign(values, s, d):
            return False ## (Fail if we can't assign d to square s.)
    return values

def grid_values(grid):
    """Convert grid into a dict of {square: char} with '0' or '.' for empties."""
    chars = [c for c in grid if c in digits or c in '0.']
    assert len(chars) == 81
    return dict(zip(squares, chars))

################ Constraint Propagation ################

def assign(values, s, d):
    """Eliminate all the other values (except d) from values[s] and propagate.
    Return values, except return False if a contradiction is detected."""
    global counttotalsearches #DGTEMP
    counttotalsearches += 1   #DGTEMP

    other_values = values[s].replace(d, '')
    if all(eliminate(values, s, d2) for d2 in other_values):
        return values
    else:
        return False

def eliminate(values, s, d):
    """Eliminate d from values[s]; propagate when values or places <= 2.
    Return values, except return False if a contradiction is detected."""
    global counttotalsearches #DGTEMP
    counttotalsearches += 1   #DGTEMP

    if d not in values[s]:
        return values ## Already eliminated
    values[s] = values[s].replace(d,'')
    ## (1) If a square s is reduced to one value d2, then eliminate d2 from the peers.
    if len(values[s]) == 0:
        return False ## Contradiction: removed last value
    elif len(values[s]) == 1:
        d2 = values[s]
        if not all(eliminate(values, s2, d2) for s2 in peers[s]):
            return False
    ## (2) If a unit u is reduced to only one place for a value d, then put it there.
    for u in units[s]:
        dplaces = [s for s in u if d in values[s]]
        if len(dplaces) == 0:
            return False ## Contradiction: no place for this value
        elif len(dplaces) == 1:
            # d can only be in one place in unit; assign it there
            if not assign(values, dplaces[0], d):
                return False
    return values

################ Display as 2-D grid ################

def display(values):
    """Display these values as a 2-D grid."""
    width = 1+max(len(values[s]) for s in squares)
    line = '+'.join(['-'*(width*3)]*3)
    for r in rows: 
        print (''.join(values[r+c].center(width)+('|' if c in '36' else '')
                      for c in cols))
        if r in 'CF': print(line)

################ Search ################

def solve(grid, searchMethod):
    return search(parse_grid(grid), searchMethod)

def findbettersquarewithpairsandtriplesOLD(s, values, printwhenfound=True): #DGNEW    <--------------- THIS CODE CAN BE OPTIMIZED
    """Will use naked pairs in order to identify a better square to use if possible.
       Inspired by https://www.sudokuoftheday.com/techniques/naked-pairs-triples/"""

    global countnakedimprovements #Ensures the use of the global variable

    #Reminder: assert units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'],
                                    # ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
                                    # ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']]

    if not (len(values[s]) == 2): #Only looks for pairs for now
        return None, None

    #Look for other square with the same values within a unit
    for unit in units[s]: #Will loop through the 3 units tied to the square
        for square_in_same_unit in unit: #We could optimize here and avoid looking at squares with only one possible value
            # Looks for pairs
            if (len(values[s]) == 2) and (square_in_same_unit != s) and values[square_in_same_unit] == values[s]: # a naked pair is found
                #if printwhenfound:
                #    print(f"Naked pair ''{values[s]}'' found for squares {s} and {square_in_same_unit}")

                #Since a naked pair is found, we can remove the two digits from this pair in all other squares in this unit to see if we solve a square
                listofsquarestoreview = unit.copy()
                listofsquarestoreview.remove(s)
                listofsquarestoreview.remove(square_in_same_unit)
                for s2 in listofsquarestoreview:
                    numberofvaluesinitial = len(values[s2])
                    possibledigits = re.sub(values[s], '', values[s2]) #DG removes the values of the naked pair from the values of s2 (square to review)
                    numberofvaluesfinal = len(possibledigits)
                    #print(f"Found square {s2} with value {newvalue} because of naked pair ''{values[s]}'' found for squares {s} and {square_in_same_unit}")
                    if (numberofvaluesfinal < numberofvaluesinitial) and (numberofvaluesfinal == 1): #DG we solved a square because of the naked pair, which makes it a better candidate
                        countnakedimprovements += 1  # Number of naked pairs or triples found
                        if printwhenfound:
                            print(f"Solved square {s2} with possible digits {possibledigits} because of naked pair ''{values[s]}'' found for squares {s} and {square_in_same_unit}")
                            values[s2] = possibledigits #DG update the possibilities for s2. In this case, only one possibilily
                        return s2, possibledigits
                #break # NOT SURE WE NEED A BREAK HERE. We found a naked pair, but it doesn't mean it will solve another square
    return None, None # No better square found

def findbettersquarewithpairsandtriples(values_in, printwhenfound=True): #DGNEW    <--------------- THIS CODE CAN BE OPTIMIZED
    """Will use naked pairs in order to identify a better square to use if possible.
       Inspired by https://www.sudokuoftheday.com/techniques/naked-pairs-triples/"""

    global countnakedimprovements #Ensures the use of the global variable

    #Reminder: assert units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'],
                                    # ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
                                    # ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']]

    values_pairs = filterTheDict(values_in, lambda elem: len(elem[1]) == 2) #Only the keys with 2 digits
    #print(values_pairs) #DGTEMP

    #Will loop through all the keys with 2 digits in order to search for naked pairs
    for s in values_pairs:
        #Look for other square with the same values within a unit
        for unit in units[s]: #Will loop through the 3 units tied to the square
            for square_in_same_unit in unit: #We could optimize here and avoid looking at squares with only one possible value
                # Looks for pairs
                if (len(values_in[s]) == 2) and (square_in_same_unit != s) and values_in[square_in_same_unit] == values_in[s]: # a naked pair is found
                    #if printwhenfound:
                    #    print(f"Naked pair ''{values[s]}'' found for squares {s} and {square_in_same_unit}")

                    #Since a naked pair is found, we can remove the two digits from this pair in all other squares in this unit to see if we solve a square
                    listofsquarestoreview = unit.copy()
                    listofsquarestoreview.remove(s)
                    listofsquarestoreview.remove(square_in_same_unit)
                    for s2 in listofsquarestoreview:
                        numberofvaluesinitial = len(values_in[s2])
                        possibledigits = re.sub(values_in[s], '', values_in[s2]) #DG removes the values of the naked pair from the values of s2 (square to review)
                        numberofvaluesfinal = len(possibledigits)
                        #print(f"Found square {s2} with value {newvalue} because of naked pair ''{values[s]}'' found for squares {s} and {square_in_same_unit}")
                        if (numberofvaluesfinal < numberofvaluesinitial) and (numberofvaluesfinal == 1): #DG we solved a square because of the naked pair, which makes it a better candidate
                            countnakedimprovements += 1  # Number of naked pairs or triples found
                            if printwhenfound:
                                print(f"Solved square {s2} with possible digits {possibledigits} because of naked pair ''{values_in[s]}'' found for squares {s} and {square_in_same_unit}")
                                values_in[s2] = possibledigits #DG update the possibilities for s2. In this case, only one possibilily
                            return s2, possibledigits
                    #break # NOT SURE WE NEED A BREAK HERE. We found a naked pair, but it doesn't mean it will solve another square
    return None, None # No better square found

def search(values, searchMethod):
    """Using depth-first search and propagation, try all possible values."""
    if values is False:
        return False ## Failed earlier
    if all(len(values[s]) == 1 for s in squares):
        return values ## Solved!

    global counttotalsearches #DGTEMP
    counttotalsearches += 1 ##DGTEMPIncreases to number of total searches

    #DG NEW CODE START ---------------------------------------------------
    #Will search differently depending on the search method
    if searchMethod not in searchMethods: raise ValueError(f"Unknown search method {searchMethod}. Available search methods are {searchMethods}") #DGNEW

    if searchMethod == 'Brute Force':
        # choose a random unfilled square
        s = random.choice([s_tmp for s_tmp in squares if len(values[s_tmp]) > 1]) #Will select a square in a list of squares with more than one possibility
        # s = random.choice(squares)
        # while len(values[s]) == 1:
        #     s = random.choice(squares)
    elif searchMethod == 'Norvig Heuristic':
        ## Chose the unfilled square s with the fewest possibilities
        n, s = min((len(values[s]), s) for s in squares if len(values[s]) > 1) #n is the number of possible values for this square
    elif searchMethod == 'Norvig Improved':
        s2, possibledigits = findbettersquarewithpairsandtriples(values, False) #DGHERE Will identify Naked Pairs/Triples in order to select a better value
        if s2: # If a better square is found (s2), will use it
            valuesnew = values.copy() #DGSCRAP
            valuesnew[s2] = possibledigits
            #print(f"Better square found: {s2} with possibledigits={valuesnew[s2]}") # DGTEMP
            return some(search(assign(valuesnew, s2, d), searchMethod)
                        for d in possibledigits) #DG uses values2, which is a result with less options than values for square s2

        #DG if no better square found, will take the Norvig Heuristic
        n, s = min((len(values[s]), s) for s in squares if len(values[s]) > 1) #n is the number of possible values for this square

        # s2, possibledigits = findbettersquarewithpairsandtriples(values, False) #DGHERE Will identify Naked Pairs/Triples in order to select a better value
        # if s2: # If a better square is found (s2), will use it
        #     #d2 = some(d for d in values2) #DGTEMP
        #     #print(f"Better square found: {s2} with possibledigits={possibledigits} and d2={d2}") # DGTEMP
        #     valuesnew = values.copy() #DGSCRAP
        #     valuesnew[s2] = possibledigits
        #     #print(f"Better square found: {s2} with possibledigits={valuesnew[s2]}") # DGTEMP
        #     return some(search(assign(valuesnew.copy(), s2, d), searchMethod)
        #                 for d in possibledigits) #DG uses values2, which is a result with less options than values for square s2
    else:
        raise ValueError(f"Search method {searchMethod} not implemented")
    #DGNEW CODE STOP ---------------------------------------------------

    # try possible numbers for s in random order
    return some(search(assign(values.copy(), s, d), searchMethod)
                for d in shuffled(values[s]))

################ Utilities ################

def some(seq):
    "Return some element of seq that is true."
    for e in seq:
        if e: return e
    return False

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

def solve_all(grids, name='', showif=0.0, searchMethod='ToSpecify'):
    """Attempt to solve a sequence of grids. Report results.
    When showif is a number of seconds, display puzzles that take longer.
    When showif is None, don't display any puzzles."""
    global counttotalsearches, countnakedimprovements #DGTEMP
    counttotalsearches = 0  #DGTEMP the total of searches
    countnakedimprovements = 0 #DGTEMP the total of searches

    def time_solve(grid):
        #start = time.clock()
        start = time.process_time()
        values = solve(grid, searchMethod)
        t = time.process_time()-start

        #display(grid_values(grid)) #DGREMOVED
        #if values: display(values) #DGREMOVED

        ## Display puzzles that take long enough
        if showif is not None and t > showif:
            display(grid_values(grid))
            if values: display(values)
            print ('(%.2f seconds)\n' % t)
        return (t, solved(values))

    if searchMethod not in searchMethods: raise ValueError(f"Unknown search method {searchMethod}. Available search methods are {searchMethods}")  # DGNEW

    times, results = zip(*[time_solve(grid) for grid in grids])
    N = len(grids)

    #DG Will avoid division by zero if time is too short (0.0).
    if sum(times) != 0.0:
        hz = N / sum(times)
    else:
        hz = 999

    if N >= 1:
#        print ("Solved %d of %d %s puzzles (avg %.2f secs (%d Hz), max %.2f secs)." % (
#            sum(results), N, name, sum(times)/N, N/sum(times), max(times))) #DG REMOVED
        print ("Solved %d of %d %s puzzles in %.2f secs (avg %.2f secs (%d Hz), max %.2f secs). Total searches %d - Naked improvements %d - %s" % (
            sum(results), N, name, sum(times), sum(times)/N, hz, max(times), counttotalsearches, countnakedimprovements, searchMethod)) #DGNEW Added parameter for search method

def solved(values):
    "A puzzle is solved if each unit is a permutation of the digits 1 to 9."
    def unitsolved(unit): return set(values[s] for s in unit) == set(digits)
    return values is not False and all(unitsolved(unit) for unit in unitlist)

def random_puzzle(N=17):
    """Make a random puzzle with N or more assignments. Restart on contradictions.
    Note the resulting puzzle is not guaranteed to be solvable, but empirically
    about 99.8% of them are solvable. Some have multiple solutions."""
    values = dict((s, digits) for s in squares)
    for s in shuffled(squares):
        if not assign(values, s, random.choice(values[s])):
            break
        ds = [values[s] for s in squares if len(values[s]) == 1]
        if len(ds) >= N and len(set(ds)) >= 8:
            return ''.join(values[s] if len(values[s])==1 else '.' for s in squares)
    return random_puzzle(N) ## Give up and make a new puzzle

grid1  = '003020600900305001001806400008102900700000008006708200002609500800203009005010300'
grid2  = '4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......'
hard1  = '.....6....59.....82....8....45........3........6..3.54...325..6..................'

if __name__ == '__main__':
    test()
    #solve_all(from_file("top95.txt"), "95sudoku", None)
    #solve_all(from_file("easy50.txt", '========'), "easy", None)
    #solve_all(from_file("hardest.txt"), "hardest", None)
    #solve_all([random_puzzle() for _ in range(99)], "random", 100.0)

    #DG Added a parameter for search method. Note: decrease the decimal value in order to show longer puzzles
    print('-----------')
    solve_all(from_file("easy50.txt"),     "easy50 ", 1.0, 'Brute Force')
    solve_all(from_file("easy50.txt"),     "easy50 ", 1.0, 'Norvig Heuristic')
    solve_all(from_file("easy50.txt"),     "easy50 ", 1.0, 'Norvig Improved')
    print('-----------')
    solve_all(from_file("top95.txt"),      "top95  ", 1.0, 'Brute Force')
    solve_all(from_file("top95.txt"),      "top95  ", 1.0, 'Norvig Heuristic')
    solve_all(from_file("top95.txt"),      "top95  ", 1.0, 'Norvig Improved')
    print('-----------')
    solve_all(from_file("hardest.txt"),    "hardest", 1.0, 'Brute Force')
    solve_all(from_file("hardest.txt"),    "hardest", 1.0, 'Norvig Heuristic')
    solve_all(from_file("hardest.txt"),    "hardest", 1.0, 'Norvig Improved')
    print('-----------')
    solve_all(from_file("100sudoku.txt"),  "100puz ", 1.0, 'Brute Force')
    solve_all(from_file("100sudoku.txt"),  "100puz ", 1.0, 'Norvig Heuristic')
    solve_all(from_file("100sudoku.txt"),  "100puz ", 1.0, 'Norvig Improved')
    print('-----------')
    solve_all(from_file("1000sudoku.txt"), "1000puz", 1.0, 'Brute Force')
    solve_all(from_file("1000sudoku.txt"), "1000puz", 1.0, 'Norvig Heuristic')
    solve_all(from_file("1000sudoku.txt"), "1000puz", 1.0, 'Norvig Improved')
    print('-----------')
    solve_all(from_file("1puzzle.txt"),    "1puzzle", 1.0, 'Brute Force')
    solve_all(from_file("1puzzle.txt"),    "1puzzle", 1.0, 'Norvig Heuristic')
    solve_all(from_file("1puzzle.txt"),    "1puzzle", 1.0, 'Norvig Improved')
    print('-----------')
    solve_all(from_file("NakedPair.txt"),  "NakedPT", 1.0, 'Brute Force') #DG file created from https://www.sudokuoftheday.com/techniques/naked-pairs-triples/
    solve_all(from_file("NakedPair.txt"),  "NakedPT", 1.0, 'Norvig Heuristic')
    solve_all(from_file("NakedPair.txt"),  "NakedPT", 1.0, 'Norvig Improved')

## References used:
## http://www.scanraid.com/BasicStrategies.htm
## http://www.sudokudragon.com/sudokustrategy.htm
## http://www.krazydad.com/blog/2005/09/29/an-index-of-sudoku-strategies/
## http://www2.warwick.ac.uk/fac/sci/moac/currentstudents/peter_cock/python/sudoku/
## https://www.sudokuoftheday.com/techniques/naked-pairs-triples/ (DG)