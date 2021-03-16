

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
from itertools import combinations
import math


def cross(A, B):
    "Cross product of elements in A and elements in B."
    return [a + b for a in A for b in B]


digits   = '123456789'
rows     = 'ABCDEFGHI'
cols     = digits
squares  = cross(rows, cols)
unitlist = ([cross(rows, c) for c in cols] +
            [cross(r, cols) for r in rows] +
            [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI')
                           for cs in ('123', '456', '789')])
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
    assert peers['C2'] ==  {'A2', 'B2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2',
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
    Return values, except return False if a contradiction is detected.
    If a unit is specified, propagate within that unit only"""
    other_values = values[s].replace(d, '')
    if all(eliminate(values, s, d2, unit) for d2 in other_values):
        return values
    else:
        return False


def eliminate(values, s, d, unit=None):
    """Eliminate d from values[s]; propagate when values or places <= 2.
    Return values, except return False if a contradiction is detected.
    if a unit is specified, propagate within that unit only"""
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

def solve(grid, printoutput=False, show_solution=False):

    if args.method == "hc":
        result = hill_climbing(parse_grid(grid), printoutput)
    
    elif args.method == "sa":
        result = simulated_annealing(parse_grid(grid), printoutput=printoutput)
    
    elif args.method == "dfs":
        result = search(parse_grid(grid))
    
    elif args.method == "rf":
        result = random_fill(parse_grid(grid), printoutput=printoutput)
        
    if show_solution: #display before and after
        display(grid_values(grid))
        print()
        display(result)
        print("remaining conflicts: ", nb_conflicts(result))
        
    return result

    
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
blocklist = unitlist[18:] # list of blocks (3x3 units)
blocks = dict((s,u) for u in blocklist for s in squares if s in u)
linelist = unitlist[0:18]
cols_rows = dict(zip(cols+rows, linelist)) #all row and column units


iterations = []
def hill_climbing(values, printoutput=False):
    """Hill climbing algorithm. 
    The initial state has each square filled with one randomly chosen possible
    value such that each 3x3 unit has the complete set of digits. This may cause
    conflicts within rows and columns. 
    Hill climbing will seek to iteratively improve the current state by swapping 
    two values at a time within a 3x3 unit."""
    
    constraints = values               #initial parsed grid serves as constraints
    state = random_fill(values.copy()) #state initialization
    conflicts = nb_conflicts(state)    #nb of conflicts in current state
    all_pairs = get_all_pairs(constraints)

    if printoutput:
        print("constraints:")
        display(constraints)
        print("***initial grid***")
        display(state)
        print("initial nb of conflicts", nb_conflicts(state))
    nb_iterations = 0
    while (True):
        
        # if no conflicts => sudoku is solved. otherwise keep improving state
        if conflicts == 0:
            break
        nb_iterations += 1
        max_improvement = 0
        a, b = None, None #best pair found for swap (for debug/demo purposes)

        for s1, s2 in all_pairs:
            #calculate improvement from swapping (s1, s2)
            improvement = net_improvement_from_swap(state, s1, s2)

            if improvement > max_improvement:
                max_improvement = improvement
                a, b = s1, s2
                   
        if max_improvement: #found improvement
           
            conflicts -= max_improvement
            state[a], state[b] = state[b], state[a]

            if printoutput:
                print("\nswapping {}, {} for a max improvement of {}".format(
                    a,b,max_improvement))
                display(state)
                print(f"number of conflicts left:\t {nb_conflicts(state)}")
             
        else: #else there was no improvement from previous state
            break
    iterations.append(nb_iterations)
    #algorithm ends if the sudoku is solved or when it can no longer improve score
    return state



def simulated_annealing(values, a=0.99, t=3.0, printoutput=False):
    if args.t:
        t = args.t

    solution = random_fill(values.copy()) #state initialization
    conflicts = nb_conflicts(solution)    #nb of conflicts in current state

    while t > 0.001:
        # if no conflicts => sudoku is solved. otherwise keep changing state
        if conflicts == 0:
            break
    
        #pick a pair to swap
        s1, s2 = get_random_pair(values)

        #calculate potential improvement 
        improvement = net_improvement_from_swap(solution, s1, s2)

        # a swap is due:
        # 1) if it improves the solution or;
        # 2) with a certain probability depending on temperature and improvement
        #    suggested by the pair.
        # improvement == 0 will always lead to a swap
        if improvement >= 0 or random.uniform(0, 1) <= math.exp(improvement/t):
            solution[s1], solution[s2] = solution[s2], solution[s1]
            conflicts -= improvement

            if printoutput:
                cause = "improvement" if improvement > 0 else "temperature"
                print(f"Swapping {s1} and {s2} because {cause} allows."
                      + f" Improvement = {improvement}")
                display(solution)
                print(f"number of conflicts left:\t {nb_conflicts(solution)}")
                #decrease temperature at each iteration

        t *= a

    return solution



def get_all_pairs(values):
    """return list of all pairs of squares in each 3x3 unit whose values are 
    not fixed.
    The pairs are not necessarily 'swappable'. Their present-state values must be 
    evaluated before each swap if constraints must be met"""
    pairs = []
    for block in blocklist:
        # list of non-fixed squares in the block
        mutables = [s for s in block if len(values[s]) > 1] 
        # add pairs of non-fixed squares in the block to result
        pairs.extend([pair for pair in combinations(mutables, 2)])

    return pairs



def get_random_pair(values):
    """return a pair of squares in the same 3x3 block whose values are not fixed"""
    s1, s2 = None, None
    while True:
        s1 = random.choice([k for k in values.keys()])

        if len(values[s1]) > 1:
            s2 = random.choice(
                        [s for s in blocks[s1] if len(values[s]) > 1 and s != s1])
            break

    return s1,s2
    
    

def net_improvement_from_swap(solution, s1, s2):
    """return the difference in the number of conflicts in a grid (values) from
    before and after swapping the values in s1, s2
    Total improvements vary from -4 to +4 and the higher the number the better:
        + 1 if a digit leaves   a row/column in which its duplicate exist 
        - 1 if a digit lands in a row/column that already has a copy of it
    """
    improvement = 0
    for i in range(2):        #for row, column lines
        if s1[i] != s2[i]:    #if the pair doesn't share lines
            # line of s1
            l = [solution[s] for s in cols_rows[s1[i]]]   
            # 1) if digit from s2 was already in s1's line, the swap will worsen the state
            improvement -= 1 if solution[s2] in l else 0 

            # 2) if s1 was a duplicate digit in its line, the swap will improve the state
            improvement += 1 if l.count(solution[s1]) > 1 else 0 

            #do the same for the line of s2
            l = [solution[s] for s in cols_rows[s2[i]]]
            improvement -= 1 if solution[s1] in l else 0 
            improvement += 1 if l.count(solution[s2]) > 1 else 0

    return improvement


        
#not used in hill-climbing except to compare values before and after running algorithm
def nb_conflicts(solution):
    """number of conflicts i.e. the total number of missing digits per row and
    column units in the entire grid """
    conflicts = 0
    for unit in unitlist:
        #conflicts = nb of missing digits in line
        values_in_unit = [solution[s] for s in unit]
        conflicts += len([d for d in digits if d not in values_in_unit])
    return conflicts



def random_fill(values, printoutput=False):
    """fill each 3x3 unit randomly in such a way that there are no conflict 
    within each unit"""
    for block in blocklist:
        values = random_fill_unit(values, block)
    if printoutput:
        print("*** initial grid (hill climbing) ***")
        display(values)
        print("initial nb of conflicts", nb_conflicts(values))
    return values


def random_fill_unit(values, unit):
    """fill a unit with random numbers, without conflict within that unit"""
    if values is False:
        return False
    
    if all(len(values[s]) == 1 for s in unit):
        return values #unit is filled
    #s = random.choice([s for s in unit if len(values[s]) > 1])
    n,s = min([(len(values[s]), s) for s in unit if len(values[s]) > 1])
        
    return some(random_fill_unit(assign(values.copy(), s, d, unit),unit)
                                 for d in shuffled(values[s]))

#another random_fill method implemented the 'dumb' way that doesn't improve on the other one
def random_fill_unit2(values, unit):
    #display(values)
    result = values.copy()
    remaining_digits = list(digits)
    squares_to_assign = []
    for s in unit:
        if len(values[s]) == 1:
            #print(values[s])
            #print(digits_to_assign)
            remaining_digits.remove(values[s])
        else:
            squares_to_assign.append(s)
            
    #until each square has a digit that respects its values constraints,
    #put the remaining digits in random order and try to assign them to
    #the squares whose values are not fixed. 
    assigned = False
    while(not assigned):
        assigned = True
        ds = shuffled(remaining_digits)
        for i in range(len(ds)):
            if ds[i] in values[squares_to_assign[i]]:
                result[squares_to_assign[i]] = ds[i]
            else:
                assigned = False
                break
        
    return(result)
            

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

    method_descriptions = {'hc' : 'Hill-Climbing',
                               'dfs' : 'Backtracking',
                               'sa' : 'Simulated Annealing',
                               'rf' : 'randomly filling after parsing the grid'}

    def time_solve(grid):
        # start = time.clock()
        start = time.process_time()
        values = solve(grid)
        t = time.process_time() - start
        conflicts = 0
        # Keep a count of unresolved conflicts
        got_solved = solved(values)
        if not got_solved: conflicts = nb_conflicts(values)
        ## Display puzzles that take long enough
        if showif is not None and t > showif:
            display(grid_values(grid))
            print()
            if values: display(values)
            print('(%.2f seconds)\n' % t)
        return (t, got_solved, conflicts)

    times, results, conflicts = zip(*[time_solve(grid) for grid in grids])
    
    N = len(grids)
    if N > 1:
        
        print(f"* Method: {method_descriptions[args.method]} *")
        if args.method == 'dfs':
            print(f'Heuristic: {args.heuristic}')
        print("Solved %d of %d %s puzzles within %.2f secs (avg %.2f secs (%d Hz), max %.2f secs)." % (
            sum(results), N, name, sum(times), sum(times) / N, N / sum(times),
                  max(times)))
        
        
        print("Number of conflicts remaining after solve attempt:"
                  + " avg %.2f, min %i, max %i\n"%(
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
grid3 = '4..27.6..798156234.2.84...7237468951849531726561792843.82.15479.7..243....4.87..2' #Easy grid to test
hard1 = '.....6....59.....82....8....45........3........6..3.54...325..6..................'



def demo(grid=grid2):
    
    # Local test with display
    print('-------------------- Test with one grid START --------------------')
    #values = solve(grid3, True) # Quick test with grid almost complete
    values = solve(grid, True) # Longer test
    print("FINAL number of conflicts left:\t", nb_conflicts(values))
    print('--------------------  Test with one grid END  --------------------')


def benchmarks():
    solve_all(from_file("./MesSudokus/top95.txt"),    "   top95   ", args.showif)
    solve_all(from_file("MesSudokus/easy50.txt"),     "  easy50   ", args.showif)
    solve_all(from_file("MesSudokus/hardest.txt"),    "  hardest  ", args.showif)
    solve_all(from_file("MesSudokus/100sudoku.txt"),  " 100sudoku ", args.showif)
    #solve_all(from_file("MesSudokus/1000sudoku.txt"), "1000sudoku ", args.showif)
    solve_all([random_puzzle() for _ in range(100)],  "   random  ",  args.showif)

        
if __name__ == '__main__':
    random.seed(10)
    test()
    #command line arguments and options 
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('method',
                        choices=['dfs','hc','sa','rf'],
                        default = 'dfs',
                        help='Available methods are:\n\
                        -Depth-first-search with a choice of heuristic function;\n\
                        -Hill-climbing.')
    
    parser.add_argument('sudoku', nargs='?', type=str, help="A string representing a sudoku "
                        + "problem instance, where\nthe unknown values are either "
                        + "'.' or '0'.\nExample:2000600000070040860000013000000000"
                        + "400900000004\n80000710900078000000050002020600501")
    
    parser.add_argument('--heuristic',
                        default='random',
                        choices=['random', 'norvig', 'naked_pairs'],
                        help='choice of heuristics fonction')

    parser.add_argument('--alpha', type=float, help="To specify the value of the "
                        + "cooling schedule alpha\nwhen the simulated annealing "
                        + "method is chosen. \nDefault = 0.99")
    parser.add_argument('--t', type=float, help="To specify the initial temperature"
                        + " when the simulated\nannealing algorithm is chosen.\n"
                        + "Default = 3.0")
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--benchmarks', action='store_true')
    parser.add_argument('--file', type=argparse.FileType('r'))
    
   
    parser.add_argument('--showif', type=float, default=None)
    args = parser.parse_args()

    #simulate commandline arguments 
    #args = parser.parse_args(['hc']) #for hill climbing
    #args = parser.parse_args(['dfs', '--heuristic', 'naked_pairs']) # for dfs, norvig
    #args = parser.parse_args(['sa']) #for simulated annealing
    
    if args.file:
        solve_all(args.file.read().strip().split('\n'), "sudoku", args.showif)
    elif args.sudoku:
        solve(args.sudoku, False, True)
        
    if args.demo:
        if args.sudoku:
            demo(args.sudoku)
        else:
            demo()

    if args.benchmarks:
        benchmarks()

    
        
    

## References used:
## http://www.scanraid.com/BasicStrategies.htm
## http://www.sudokudragon.com/sudokustrategy.htm
## http://www.krazydad.com/blog/2005/09/29/an-index-of-sudoku-strategies/
## http://www2.warwick.ac.uk/fac/sci/moac/currentstudents/peter_cock/python/sudoku/
