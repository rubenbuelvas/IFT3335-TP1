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
import random
from math import exp
#import copy
from colorama import Fore, Back, Style # example: print(Fore.BLUE + displaystring)

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

firstsquaresofunit3x3 = cross('ADG','147')  # list containing 9 squares: first per unit: ['A1', 'A4', 'A7', 'D1', ... ]
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

def solve(grid, printoutput=False, initial_temperature_sa=3):
    if args.method == "hc":
        return hill_climbing(parse_grid(grid), printoutput)
    elif args.method == "sa":
        return simulated_annealing(parse_grid(grid), printoutput, initial_temperature_sa)
    elif args.method == "rf":
        return random_initial_fill(parse_grid(grid), printoutput)
    elif args.method == "dfs":
        return search(parse_grid(grid))
    else:
        raise ValueError(f"Unknown method: {args.method}")
    
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

# def swappable_pairs(state, constraints, unit): #DGNOTWORKING
#     """Receives a unit and the constraint values and returns a list of pairs that can be swapped.
#     For example, will receive ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3'] and
#     return [('A1', 'A2'), ('A1', 'B2'), ('B2', 'C2')]
#     """
#     list_of_swappable_pairs = []
#     listofswappablesquares = [s for s in unit if len(constraints[s]) > 1]  # excludes the initial values
#     for i in range(0, len(listofswappablesquares) - 1): # Loop trough all swappablesquares except the last one
#         for j in range(i+1, len(listofswappablesquares)): # Loop trough all swappablesquares after i
#             s1, s2 = listofswappablesquares[i], listofswappablesquares[j]
#             if (state[s1] in constraints[s2]) and (state[s1] in constraints[s2]):
#                 list_of_swappable_pairs.append((s1, s2))
#
#     #print(f"list_of_swappable_pairs for listofswappablesquares is : {list_of_swappable_pairs}")  # DGTEMP
#
#     return(list_of_swappable_pairs)


def simulated_annealing(values, printoutput=False, initial_temperature=3):
    """Simulated annealing algorithm.
    This algorithm will work similarly than hill_climbing, but will allow to move "downward" by accepting to move to
    a state having more conflicts, if the temperature allows it."""

    debug = False #DGTEMP

    ########STEP 1: INITIALIZE VARIABLES (schedule could be passed as parameters)
    #initial_temperature = .5 #DG TO REVIEW. I can change this number to 100,000 or 0.1 and I get the same results
    max_iterations = 30000 #DG TO REVIEW. I asked a question about this. A number between 10,000 and 30,000 seems perfect here
    schedule = [initial_temperature] # Temperature schedule with t[i+1] = t[i] * a. For example, if T=3 and a=0.99: so T0 = 3, T1 = 3 * 0.99, T2 = 3 * 0.99 * 0.99, ...
    a = 0.99  # strategy to decrease temperature
    for t in range(1,max_iterations): #Initializes the temperature schedule  #DGTEMP: UNSURE WHEN TO STOP THE TEMPERATURE DECREASE SINCE schedule[1000]= 0.000129514
        schedule.append(schedule[t-1] * a)

    # Initialize current_state by populating all digits, creating conflicts in rows and columns
    constraints = values  # initial parsed grid serves as constraints

    current_state = random_fill(values.copy())  # state initialization
    conflicts = nb_conflicts(current_state)  # nb of conflicts in current state

    # if printoutput:
    #     print("*** initial grid (simulated annealing) ***")
    #     display(current_state)
    #     print("initial nb of conflicts", nb_conflicts(current_state))

    if conflicts == 0:  # solved!
        return current_state

    ########STEP 2: LOOK FOR NEXT STATE BY GOING THROUGH THE TEMPERATURE SCHEDULE
    for t in range(len(schedule)): #go through the temperature schedule

        T = schedule[t]
        if debug: print(f"----- LOOP # {t} of {len(schedule)} with T={T} -------------------------------------------------------------------------------------")  # DGTEMP

        if T < 0.001: return current_state # DGTEMP: Hugo Larochelle's algorithm doesn't stop if T is ZERO. It simply goes through all steps of the schedule

        ########STEP 3: SELECT RANDOMLY ANOTHER STATE (BETTER OR NOT)
        # Select 2 squares randomly within a 3x3unit
        s1, s2 = None, None
        fsou = shuffled(firstsquaresofunit3x3) # Finds a 3x3unit randomly and ensures it can have a swap
        for fs in fsou: #Will loop through all 3x3units until if finds one with at least 2 swappable squares

            #DGNOTWORKING
            # list_of_swappable_pairs = swappable_pairs(current_state, constraints, units[fs][2]) # Within 3x3 unit
            # if len(list_of_swappable_pairs) > 0: #found a swappable pair within constraints
            #     current_pair = shuffled(list_of_swappable_pairs.pop())
            #     s1, s2 = current_pair[0], current_pair[1]
            #     break
            # DGNOTWORKING

            listofswappablesquares = [s for s in units[fs][2] if len(values[s]) > 1] # will look through each squares within unit and add it if swappable
            if debug: print(f"DGTEMP: Looks if swappable squares in unit containing {fs}. Swappable squares are: {listofswappablesquares}") #DGTEMP
            if len(listofswappablesquares) >= 2: # Will swap 2 randomly selected squares
                listofswappablesquares = shuffled(listofswappablesquares)
                s1, s2 = listofswappablesquares.pop(), listofswappablesquares.pop()
                if debug: print(f"DGTEMP: s1={s1} s2={s2}. Swappable squares are now: {listofswappablesquares}")  # DGTEMP
                break
        assert s1 != None and s2 != None #ensures 2 squares are found

        ########STEP 4: EVALUATE IMPROVEMENT AND DETERMINE IF CURRENT STATE BECOMES NEXT STATE
        improvement = net_improvement_from_swap(current_state, s1, s2)
        # if not (current_state[s1] in constraints[s2]) or not (current_state[s2] in constraints[s1]): #DGSCRAP
        #     improvement = -999999 #Invalid swap #DGSCRAP
        #     print(f"invalid swap at iteration {t}: current_state[s1]={current_state[s1]} and constraints[s2]={constraints[s2]} + current_state[s2]={current_state[s2]} and constraints[s1]={constraints[s1]}") #DGSCRAP

        if improvement > 0: # current state will become next state, so we do the swap
            if printoutput: print(f"Swapping {s1} and {s2} because improvement of {improvement}")
            to_swap = True
        else:
            # Will change only within probability based on the temperature
            r = random.uniform(0, 1)
            to_swap = r <= exp(improvement/T)
            if printoutput and to_swap: print(f"Swapping {s1} and {s2} because temperature allows it. Improvement={improvement}, T={T}, math.exp(improvement/T) = {exp(improvement/T)} and r={r}")
            #if printoutput and not to_swap: print(f"No swap because temperature doesn't allow it. Improvement={improvement}, T={T}, math.exp(improvement/T) = {exp(improvement / T)} and r={r}")  # DGTEMP

        if to_swap: # current state = next state
            current_state[s1], current_state[s2] = current_state[s2], current_state[s1]

            if printoutput:
                display(current_state)
                print(f"number of conflicts left:\t {nb_conflicts(current_state)} after iteration {t}")
            # if no conflicts => sudoku is solved. otherwise keep improving state
            if nb_conflicts(current_state) == 0:
                return current_state

    return current_state


def random_initial_fill(values, printoutput=False):
    """Random fill.
    This algorithm will simply solve sudokus by doing a random fill with the 9 digits within each 3x3unit, respecting
    the constraints determined by parse grid. It will not do anything else after the initial random fill."""

    state = random_fill(values.copy())  # state initialization

    if printoutput:
        print("*** initial grid (hill climbing) ***")
        display(state)
        print("initial nb of conflicts", nb_conflicts(state))

    return state


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

    if printoutput:
        print("*** initial grid (hill climbing) ***")
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
            if printoutput: print("\nswapping {}, {} for a max improvement of {}".format(a,b,max_improvement))
            conflicts -= max_improvement
            state[a], state[b] = state[b], state[a]

            if printoutput:
                display(state)
                print(f"number of conflicts left:\t {nb_conflicts(state)}")
            
            # if no conflicts => sudoku is solved. otherwise keep improving state
            if conflicts == 0:
                break
            
        else:     #else there was no improvement from previous state
            break
        
    #algorithm has ended when it can no longer improve score
    return state


def net_improvement_from_swap(values, s1, s2):
    """This fonction will return the difference in the number of conflicts between a grid (values) before a swap and after
    Total improvements will vary from -4 to +4 and the highest number is the best:
        + 1 if s1 leaves   a line/column in which the digit was already there (possibles improvements of 0, +1 and +2)
        + 1 if s2 leaves   a line/column in which the digit was already there (possibles improvements of 0, +1 and +2)
        - 1 if s1 lands in a line/column in which the digit was already there (possibles improvements of 0, -1 and -2)
        - 1 if s2 lands in a line/column in which the digit was already there (possibles improvements of 0, -1 and -2)
    """

    improvement = 0
    for i in range(2):        #for rows, columns
        if s1[i] != s2[i]:    #if the pair doesn't share lines
            l = [values[s] for s in cols_rows[s1[i]]] # line of s1
            #if s2 was not in s1's col_rows, then the swap will improve the state
            improvement += 0 if values[s2] not in l else -1 # arrival of s2: -1 if conflict and 0 otherwise

            #if s1 was a duplicate digit in its col_rows, the swap will improve the state
            improvement += 1 if l.count(values[s1]) > 1 else 0 # departure of s1: +1 if decreases conflict and 0 otherwise

            #do the same for the col_rows of s2
            l = [values[s] for s in cols_rows[s2[i]]]
            improvement += 0 if values[s1] not in l else -1 # arrival of s1: -1 if conflict and 0 otherwise
            improvement += 1 if l.count(values[s2]) > 1 else 0 # departure of s2: +1 if decreases conflict and 0 otherwise

    return improvement
        
        
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


def solve_all(grids, name='', showif=0.0, initial_temperature_sa=3):
    """Attempt to solve a sequence of grids. Report results.
    When showif is a number of seconds, display puzzles that take longer.
    When showif is None, don't display any puzzles."""

    def time_solve(grid):
        # start = time.clock()
        start = time.process_time()
        values = solve(grid, False, initial_temperature_sa)
        t = time.process_time() - start
        conflicts = 0
        # Keep a count of unresolved conflicts for hill-climbing method
        if args.method in ['hc', 'sa', 'rf']:
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
        if sum(conflicts) / N < 2.4:
            printstring = Back.LIGHTGREEN_EX
        else:
            printstring = Style.RESET_ALL  # No color styles

        printstring += "Solved %d of %d %s puzzles within %.2f secs (avg %.3f secs (%d Hz), max %.3f secs). Method=%s " % (
            sum(results), N, name, sum(times), sum(times) / N, N / sum(times), max(times), args.method)

        if args.method == "hc": # Hill-Climbing
            printstring += "remaining conflicts min %i, max %i and avg %.3f"%(min(conflicts), max(conflicts), sum(conflicts)/N)
        if args.method == "sa": # Simulated Annealing
            printstring += "remaining conflicts min %i, max %i and avg %.3f (and init T=%.2f)"%(min(conflicts), max(conflicts), sum(conflicts)/N, initial_temperature_sa)
        if args.method == "rf": # Random initial fill
            printstring += "remaining conflicts min %i, max %i and avg %.3f"%(min(conflicts), max(conflicts), sum(conflicts)/N)
        print(printstring)

        # print("Solved %d of %d %s puzzles within %.2f secs (avg %.3f secs (%d Hz), max %.3f secs). Method=%s" % (
        #     sum(results), N, name, sum(times), sum(times) / N, N / sum(times), max(times), args.method))
        # if args.method == "hc": # Hill-Climbing
        #     print("Number of conflicts remaining after solve attempt with Hill-Climbing: avg %.3f, min %i, max %i"%(
        #                sum(conflicts)/N, min(conflicts), max(conflicts)))
        # if args.method == "sa": # Simulated Annealing
        #     print("Number of conflicts remaining after solve attempt with Simulated Annealing: avg %.3f, min %i, max %i and init T=%.2f"%(
        #                sum(conflicts)/N, min(conflicts), max(conflicts), initial_temperature_sa))
        # if args.method == "rf": # Random initial fill
        #     print(
        #         "Number of conflicts remaining after solve attempt with Random initial fill: avg %.3f, min %i, max %i" % (
        #             sum(conflicts) / N, min(conflicts), max(conflicts)))


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--heuristic',
                        default='random',
                        choices=['random', 'norvig', 'naked_pairs'],
                        help='choice of heuristics fonction')
    parser.add_argument('method',
                        choices=['dfs','hc', 'sa', 'rf'],
                        default = 'dfs',
                        help='available methods are:\n-Depth-first-search with a choice of heuristic function;\n-Hill-climbing.')
    
    #args = parser.parse_args()

    #set commandline arguments 
    args = parser.parse_args(['hc']) #for hill climbing
    #args = parser.parse_args(['dfs', '--heuristic', 'norvig']) # for dfs, norvig
    
    test()

    # print('-------------------- Test with one grid START - SIMULATED ANNEALING --------------------')
    # args = parser.parse_args(['sa']) #for simulated annealing
    # #values = solve(grid2, True) # Longer test
    # values = solve(grid3, True) # Quick test with grid almost complete
    # print('--------------------  Test with one grid END  - SIMULATED ANNEALING --------------------')

    # print('-------------------- Test with one grid START - HILL CLIMBING --------------------')
    # args = parser.parse_args(['hc'])  # for hill climbing
    # # values = solve(grid3, True) # Quick test with grid almost complete
    # values = solve(grid2, True) # Longer test
    # print('--------------------  Test with one grid END  - HILL CLIMBING --------------------')

    # print('--------------------  COMPARE THE 3 ALGORITHMS --------------------')
    # args = parser.parse_args(['dfs']) #for brute force
    # solve_all(from_file("MesSudokus/100sudoku.txt  "), "100sudoku ", None)
    # args = parser.parse_args(['rf']) #for random initial fill
    # solve_all(from_file("MesSudokus/100sudoku.txt  "), "100sudoku ", None)
    # args = parser.parse_args(['hc']) #for hill climbing
    # solve_all(from_file("MesSudokus/100sudoku.txt  "), "100sudoku ", None)
    # args = parser.parse_args(['sa']) #for simulated annealing
    # solve_all(from_file("MesSudokus/100sudoku.txt  "), "100sudoku ", None)

    # print('--------------------  TEST different temperatures for simulated annealing  --------------------')
    args = parser.parse_args(['sa']) #for simulated annealing
    for i in range(1,100): # Will loop bew
        solve_all(from_file("MesSudokus/1000sudoku.txt  "), "1000sudoku ", None, i/10)

    # print('--------------------  TEST many puzzles for simulated annealing  --------------------')
    #args = parser.parse_args(['hc']) #for simulated annealing
    args = parser.parse_args(['sa']) #for simulated annealing
    # solve_all(from_file("MesSudokus/top95.txt      "), "top95     ", 9.0)
    # solve_all(from_file("MesSudokus/easy50.txt     "), "easy50    ", None)
    # solve_all(from_file("MesSudokus/hardest.txt    "), "hardest   ", None)
    # solve_all(from_file("MesSudokus/100sudoku.txt  "), "100sudoku ", None)

    # print('--------------------  COMPARE THE 3 ALGORITHMS --------------------')
    # args = parser.parse_args(['dfs']) #for brute force
    # solve_all(from_file("MesSudokus/1000sudoku.txt  "), "1000sudoku ", None)
    # args = parser.parse_args(['rf']) #for random initial fill
    # solve_all(from_file("MesSudokus/1000sudoku.txt  "), "1000sudoku ", None)
    # random_initial_fill
    # args = parser.parse_args(['hc']) #for hill climbing
    # solve_all(from_file("MesSudokus/1000sudoku.txt  "), "1000sudoku ", None)
    # args = parser.parse_args(['sa']) #for simulated annealing
    # solve_all(from_file("MesSudokus/1000sudoku.txt  "), "1000sudoku ", None)


## References used:
## http://www.scanraid.com/BasicStrategies.htm
## http://www.sudokudragon.com/sudokustrategy.htm
## http://www.krazydad.com/blog/2005/09/29/an-index-of-sudoku-strategies/
## http://www2.warwick.ac.uk/fac/sci/moac/currentstudents/peter_cock/python/sudoku/