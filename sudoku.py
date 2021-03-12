

## example use from commandline
##
## for depth-first-search:
## `python sudoku.py dfs --heuristic [option]`
## where option = ['random', 'norvig', 'naked_pairs']
##
## for hill-climbing:
## `python sudoku.py hc`




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

import argparse
import copy


def cross(A, B):
    "Cross product of elements in A and elements in B."
    return [a + b for a in A for b in B]


digits   = '123456789'
rows     = 'ABCDEFGHI'
cols     = digits
squares  = cross(rows, cols)
unitlist = ([cross(rows, c) for c in cols] +
            [cross(r, cols) for r in rows] +
            [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')])
units = dict((s, [u for u in unitlist if s in u])
             for s in squares)
peers = dict((s, set(sum(units[s], [])) - set([s]))
             for s in squares)

args = None #to be initialized with some values

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
    assert peers['C2'] == {'A2', 'B2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2',
                           'C1', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 
                           'A1', 'A3', 'B1', 'B3'}
    print('All tests pass.')

################ Parse a Grid ################

def parse_grid(grid):
    """Convert grid to a dict of possible values, {square: digits}, or
    return False if a contradiction is detected."""
    ## To start, every square can be any digit; then assign values from the grid.
    values = dict((s, digits) for s in squares)
    for s,d in grid_values(grid).items():
        if d in digits and not assign(values, s, d):
            return False  ## (Fail if we can't assign d to square s.)
    return values


def grid_values(grid):
    """Convert grid into a dict of {square: char} with '0' or '.' for empties."""
    chars = [c for c in grid if c in digits or c in '0.']
    assert len(chars) == 81
    return dict(zip(squares, chars))


################ Constraint Propagation ################

def assign(values, s, d, unit=None):
    """Eliminate all the other values (except d) from values[s] and propagate.
    Return values, except return False if a contradiction is detected."""
    other_values = values[s].replace(d, '')
    if all(eliminate(values, s, d2, unit) for d2 in other_values):
        return values
    else:
        return False


def eliminate(values, s, d, unit=None):
    """Eliminate d from values[s]; propagate when values or places <= 2.
    Return values, except return False if a contradiction is detected."""
    p = peers[s]
    units_to_check = units[s]
    if unit:
        p = [s2 for s2 in unit if s2 != s]
        units_to_check = [unit]
    
    if d not in values[s]:
        return values  ## Already eliminated
    values[s] = values[s].replace(d, '')
    ## (1) If a square s is reduced to one value d2, then eliminate d2 from the peers.
    if len(values[s]) == 0:
        return False  ## Contradiction: removed last value
    elif len(values[s]) == 1:
        d2 = values[s]
        if not all(eliminate(values, s2, d2, unit) for s2 in p):
            return False
    ## (2) If a unit u is reduced to only one place for a value d, then put it there.
    for u in units_to_check:
        dplaces = [s for s in u if d in values[s]]
        if len(dplaces) == 0:
            return False  ## Contradiction: no place for this value
        elif len(dplaces) == 1:
            # d can only be in one place in unit; assign it there
            if not assign(values, dplaces[0], d, unit):
                return False
    return values


################ Display as 2-D grid ################

def display(values):
    """Display these values as a 2-D grid."""
    width = 1 + max(len(values[s]) for s in squares)
    line = '+'.join(['-' * (width * 3)] * 3)
    for r in rows:
        print(''.join(values[r + c].center(width) + ('|' if c in '36' else '')
                      for c in cols))
        if r in 'CF': print(line)


################ Search ################

def solve(grid):
    if args.method == "hc":
        return hill_climbing(parse_grid(grid))
    
    elif args.method == "dfs":
        return search(parse_grid(grid))

    
def search(values):
    """Using depth-first search and propagation, try all possible values."""
    if values is False:
        return False  ## Failed earlier
    if all(len(values[s]) == 1 for s in squares):
        return values ## Solved!

    if (args.heuristic == 'random'):
        s = random_square(values)
    elif (args.heuristic == 'norvig'):
        s = norvig(values)
    elif (args.heuristic == 'naked_pairs'):
        s = naked_pairs(values)
    #else raise ValueError

    # try possible numbers for s in random order
    return some(search(assign(values.copy(), s, d))
                for d in shuffled(values[s]))

    #return some(search(assign(values.copy(), s, d))
                #for d in values[s])


def random_square(values):
    """choose a random unfilled square"""
    s = random.choice(squares)
    while len(values[s]) == 1:
        s = random.choice(squares)
    return s


def norvig(values):
    """Choose the unfilled square s with the fewest possibilities"""
    n,s = min((len(values[s]), s) for s in squares if len(values[s]) > 1)
    return s


def naked_pairs(values):
    """choose a square belonging to naked pairs.
    If no naked pairs are found, use norvig"""
    #all squares having two candidate digits
    two_digits = {s:d for s,d in values.items() if len(d) == 2}
    while(two_digits):
        #pick a square. if any of its peers has the same 2 digits, it's a naked pair
        s,d = two_digits.popitem()
        if any({k:v for k,v in two_digits.items() if v==d and k in peers[s]}) :
            return s 
    return norvig(values)



################ Hill Climbing ################
linelist = unitlist[0:18]
#lines = dict(zip(cols+rows, unitlist[0:18]))
cols_rows = dict(zip(cols+rows, unitlist[0:18])) #all row and column units
#rows_dict = {(r, linelist[9:]) for r in rows}
#cols_dict = {(c, linelist[0:9]) for c in cols}
#lines = dict((s, [u for u in linelist if s in u])
             #for s in squares)
units3x3 = unitlist[18:] 


def hill_climbing(values):
    """Hill climbing algorithm. 
    The initial state has each square filled with one randomly chosen possible
    value such that each 3x3 unit has the complete set of digits. This may cause
    conflicts within rows and columns. 
    Hill climbing will seek to iteratively improve the current state by swapping 
    two values at a time within a 3x3 unit."""
    
    constraints = values               #initial parsed grid serves as constraints
    state = random_fill(values.copy()) #state initialization
    conflicts = nb_conflicts(state)    #nb of conflicts in current state

    print("***initial grid***")
    display(state)
    print("initial nb of conflicts", nb_conflicts(state))
    
    if conflicts == 0:   #solved!
        return state
    
    while (True):
        max_improvement = 0
        a, b = None, None

        for unit in units3x3:
            #go through all possible pairs to swap
            for i in range(len(unit)-1):
                if len(constraints[unit[i]]) > 1:
                    s1 = unit[i]
                    
                    for s2 in [s2 for s2 in unit[i+1:] if len(constraints[s2]) > 1]:
                        if (state[s1] in constraints[s2] and state[s2] in constraints[s1]):
                            #calculate improvement from swapping (s1, s2)
                            improvement = net_improvement_from_swap(state, s1, s2)

                            if improvement > max_improvement:
                                max_improvement = improvement
                                a, b = s1, s2

        if max_improvement: #found improvement
            print("\nswapping {}, {} for a max improvement of {}".format(a,b,max_improvement))
            conflicts -= max_improvement
            state[a], state[b] = state[b], state[a]

            display(state)
            print(f"number of conflicts left:\t {nb_conflicts(state)}") #DGNEW
            
            # if no conflicts => sudoku is solved. otherwise keep improving state
            if conflicts == 0:
                break
            
        else:     #else there was no improvement from previous state
            break
        
    #algorithm has ended when it can no longer improve score
    return state


def net_improvement_from_swap(values, s1, s2):
    """DOCUMENTATION TO REVIEW (DGTEMP) ---------------------------------------------------------------------------------------------------
    ORIGINAL APPROACH:
     + 1 if s1 line already has a duplicate of this value, and -1 otherwise
     + 1 if s1 column already has a duplicate of this value, and -1 otherwise
     + 1 if s1 new line doesn't have this value, and -1 otherwise
     + 1 if s1 new column doesn't have this value, and -1 otherwise
     ... and same for s2
    ... which gives a result between -8 and +8 for each possible swap, and we take the best improvement (highest value)
    PROPOSED APPROACH:
    + 0 if s1 leaves a line/column in which its number was and go to a line/column in which its number is
    + 1 if s1 leaves a line/column in which its number was and go to a line/column in which its number isn't
    - 1 if s1 leaves a line/column in which its number wasn't and go to a line/column in which its number is
    + 0 if s1 leaves a line/column in which its number wasn't and go to a line/column in which its number isn't
    Same for s2
     ... and same for s2
    ... which gives a result between -4 and +4 for each possible swap, and we take the best improvement (highest value)
    """ #DGTEMP

    improvement = 0
    for i in range(2):        #for rows, columns
        if s1[i] != s2[i]:    #if the pair doesn't share lines
            l = [values[s] for s in cols_rows[s1[i]]] # line of s1

            #if s2 was not in s1's line, then the swap will improve the state
            improvement += 1 if values[s2] not in l else -1

            #if s1 was a duplicate digit in its line, the swap will improve the state
            improvement += 1 if l.count(values[s1]) > 1 else -1

            #do the same for the line of s2
            l = [values[s] for s in cols_rows[s2[i]]]
            improvement += 1 if values[s1] not in l else -1
            improvement += 1 if l.count(values[s2]) > 1 else -1

    return improvement//2
        
        
#not used in hill-climbing except to compare values before and after running algorithm
def nb_conflicts(values):
    """number of conflicts i.e. the total number of missing digits per unit
    in the entire grid """
    conflicts = 0
    for unit in unitlist:
        #conflicts = nb of missing digits in line
        values_in_unit = [values[s] for s in unit]
        conflicts += len([d for d in digits if d not in values_in_unit])
    return conflicts



def random_fill(values):
    """fill each 3x3 unit randomly in such a way that there are no conflict 
    within each unit"""
    for unit in units3x3:
        values = random_fill_unit(values,unit)
    return values


def random_fill_unit(values, unit):
    """fill a unit with random numbers, without conflict within that unit"""
    if values is False:
        return False
    
    if all(len(values[s]) == 1 for s in unit):
        return values #unit is filled
    
    s = random.choice([s for s in unit if len(values[s]) > 1])
        
    return some(random_fill_unit(assign(values.copy(), s, d, unit),unit)
                                 for d in shuffled(values[s]))
                                


################ Utilities ################

def some(seq):
    """Return some element of seq that is true."""
    for e in seq:
        if e: return e
    return False


def from_file(filename, sep='\n'):
    """Parse a file into a list of strings, separated by sep."""
    return open(filename).read().strip().split(sep)


def shuffled(seq):
    """Return a randomly shuffled copy of the input sequence."""
    seq = list(seq)
    random.shuffle(seq)
    return seq


################ System test ################

import time, random


def solve_all(grids, name='', showif=0.0):
    """Attempt to solve a sequence of grids. Report results.
    When showif is a number of seconds, display puzzles that take longer.
    When showif is None, don't display any puzzles."""

    def time_solve(grid):
        # start = time.clock()
        start = time.process_time()
        values = solve(grid)
        t = time.process_time() - start
        conflicts = 0
        # Keep a count of unresolved conflicts for hill-climbing method
        if args.method == 'hc':
            conflicts = nb_conflicts(values)
        ## Display puzzles that take long enough
        if showif is not None and t > showif:
            display(grid_values(grid))
            print("\n")
            if values: display(values)
            print('(%.2f seconds)\n' % t)
        return (t, solved(values), conflicts)

    times, results, conflicts = zip(*[time_solve(grid) for grid in grids])
    
    N = len(grids)
    if N > 1:
        print("Solved %d of %d %s puzzles (avg %.2f secs (%d Hz), max %.2f secs)." % (
            sum(results), N, name, sum(times) / N, N / sum(times), max(times)))
        if args.method == "hc":
            print("number of conflicts remaining after solve attempt with Hill-Climbing: avg %.2f, min %i, max %i"%(
                       sum(conflicts)/N, min(conflicts), max(conflicts)))


def solved(values):
    """A puzzle is solved if each unit is a permutation of the digits 1 to 9."""
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
            return ''.join(values[s] if len(values[s]) == 1 else '.' for s in squares)
    return random_puzzle(N)  ## Give up and make a new puzzle


grid1 = '003020600900305001001806400008102900700000008006708200002609500800203009005010300'
grid2 = '4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......'
hard1 = '.....6....59.....82....8....45........3........6..3.54...325..6..................'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--heuristic',
                        default='random',
                        choices=['random', 'norvig', 'naked_pairs'],
                        help='choice of heuristics fonction')
    parser.add_argument('method',
                        choices=['dfs','hc'],
                        default = 'dfs',
                        help='available methods are:\n-Depth-first-search with a choice of heuristic function;\n-Hill-climbing.')
    
    #args = parser.parse_args()

    #set commandline arguments 
    args = parser.parse_args(['hc']) #for hill climbing
    #args = parser.parse_args(['dfs', '--heuristic', 'norvig']) # for dfs, norvig
    
    test()
    solve_all(from_file("top95.txt"), "95sudoku", 0.1)
    # solve_all(from_file("easy50.txt", '========'), "easy", None)
    #solve_all(from_file("easy50.txt", '========'), "easy", None)
    #solve_all(from_file("top95.txt"), "hard", None)
    #solve_all(from_file("hardest.txt"), "hardest", None)
    #solve_all([random_puzzle() for _ in range(100)], "random", 100.0)
    #solve_all(from_file("10_5sudoku.txt"),"", None)
    #solve_all(from_file("test.txt"), "", None)
    #values = solve(grid2)
    #print("number of conflicts left:\t", nb_conflicts(values))
    

## References used:
## http://www.scanraid.com/BasicStrategies.htm
## http://www.sudokudragon.com/sudokustrategy.htm
## http://www.krazydad.com/blog/2005/09/29/an-index-of-sudoku-strategies/
## http://www2.warwick.ac.uk/fac/sci/moac/currentstudents/peter_cock/python/sudoku/
