#DAVID QUICK NOTES 2021-03-05 (since I cannot use GitHub)
#Update on hill climbing.
#First approach: (implemented but not efficient. Will only do 3 to 6 swaps in average)
#   Swap randomly a square causing the highest number of conflicts. (implemented but not efficient)
#
#2nd approach: (in progress)
#   Identify all swappable pairs and chose the one decreasing the number of conflicts to the lowest (in progress)

## Hill climing approach to solve a sudoku puzzle
## Inspired by Stochastic search / optimization methods from https://en.wikipedia.org/wiki/Sudoku_solving_algorithms
## Initial code copied from  http://norvig.com/sudoku.html

## Throughout this program we have:
##   r is a row,    e.g. 'A'
##   c is a column, e.g. '3'
##   s is a square, e.g. 'A3'
##   d is a digit,  e.g. '9'
##   u is a unit,   e.g. ['A1','B1','C1','D1','E1','F1','G1','H1','I1'] # unit_type can be 'row', 'column', or 'unit3x3'
##   grid is a grid,e.g. 81 non-blank chars, e.g. starting with '.18...7...
##   gv = grid_values is a dict of {square: char} with '0' or '.' for empties."""

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

# new variables created
firstsquaresofunit3x3 = cross('ADG','147')  # list containing 9 squares. The first one per unit: ['A1', 'A4', 'A7', 'D1', 'D4', 'D7', 'G1', 'G4', 'G7']
searchMethods = {'Brute Force', 'Norvig Heuristic', 'Norvig Improved', 'Hill Climbing'}  #Could be used if we want to include this code in the first one
#global emptydigits
emptydigits = '0.' # The digit values representing an empty square
unit_types = ['row', 'column', 'unit3x3'] # unit_type can be 'row', 'column', or 'unit3x3'
#print_display = 'minimum' # Possible values: ["nothing", "minimum", "init grid", "init and final grids", "all solution grids"] ## To manage print output
#print_display = 'init and final grids' # Possible values: ["nothing", "minimum", "init grid", "init and final grids", "all solution grids"] ## To manage print output
print_display = 'all solution grids' # Possible values: ["nothing", "minimum", "init grid", "init and final grids", "all solution grids"] ## To manage print output

#Text color management
from colorama import Fore, Back, Style # example: print(Fore.BLUE + displaystring) or colorBrightGreenOnBlack = "\033[1;32;40m" #DG from https://ozzmaker.com/add-colour-to-text-in-python/

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
def grid_values(grid):
    """Convert grid into a dict of {square: char} with '0' or '.' for empties.""" #DG example: {'A1': '4', 'A2': '.', 'A3': '.', 'A4': '.', 'A5': '.', 'A6': '.', 'A7': '8', 'A8': '.', 'A9': ...
    chars = [c for c in grid if c in digits or c in '0.']
    assert len(chars) == 81
    return dict(zip(squares, chars))

################ Constraint functions ################
def squares_causing_max_conflicts(gv_init, gv_current, conflicts_grid_values):
    """Will receive a grid filled with values and a conflicts_grid_values and will return:
       - a set of all squares having the maximum number of conflits
       - the number of conflicts (int) for this maximum"""
    maxconflicts = max(conflicts_grid_values)
    return conflicts_grid_values[maxconflicts], maxconflicts

def is_initial_squares(gv_init, s):
    """Will receive the initial grid and a square and return True if filled in the initial puzzle"""
    # loop trough all squares and list unempty squares (initial puzzle)
    return gv_init[s] not in emptydigits

def non_initial_squares_set(gv_init):
    """Will return a set of the squares that were empty in the original puzzle"""
    #return {r+c for r in rows for c in cols if is_initial_squares(gv_init, r+c)} #DGHERE Can write in one line?
    set_of_squares = set()
    for r in rows:
        for c in cols:
            if not is_initial_squares(gv_init, r+c):
                set_of_squares.add(r+c)
    return set_of_squares

def remove_initial_squares_from_set(gv_init, set_of_squares):
    """Will receive a set of squares and will return this set, without the initial squares"""
    return set_of_squares - initial_squares_set(gv_init)

def squares_within_unit_list(s, unit_type): #DGHERE Can use more this function. Look for "units[" and replace
    """Returns a list of the squares within the same unit as s.
       unit_type can be 'row', 'column', or 'unit3x3' """
    assert unit_type in unit_types
    if   unit_type == 'row'    : return(setunits[s][0])
    elif unit_type == 'column' : return(units[s][1])
    elif unit_type == 'unit3x3': return(units[s][2])
    else: raise ValueError(f"Unit type {unit_type} not implemented.")

def possible_replacements_within_unit(gv_init, s, unit_type):
    """Returns the squares within the same unit as s that can be replaced, excluding s.
       unit_type can be 'row', 'column', or 'unit3x3' """
    return (set(squares_within_unit_list(s, unit_type)) - set(s)) - initial_squares_set(gv_init)

def initial_squares_set(gv_init):
    """Will receive the initial grid and return a set of all squares not empty"""
    # loop trough all squares and list unempty squares (initial puzzle)
    set_initialsquares = set()
    for r in rows:
        for c in cols:
            if is_initial_squares(gv_init, r+c):
                set_initialsquares.add(r+c)
    return set_initialsquares

def swap2numbers(gv_init, gv_current, conflicts_grid_values):
    """Will take a square with a maximum number of conflicts and swap it randomly within the 3x3 unit with another square that isn't part of the initial puzzle. Will then return the new grid_value"""

    # Selects randomly one of the squares with the maximum number of conflicts
    s_withmaxconflicts, maxconflicts = squares_causing_max_conflicts(gv_init, gv_current, conflicts_grid_values)
    s1toswap = some(shuffled(s_withmaxconflicts)) # random selection

    #Find another square within 3x3 unit and swap randomly without considering the number of conflicts (TO IMPROVE?)
    s2toswap = some(shuffled(possible_replacements_within_unit(gv_init, s1toswap, 'unit3x3')))
    s1value = gv_current[s1toswap]
    gv_current[s1toswap] = gv_current[s2toswap]
    gv_current[s2toswap] = s1value

    if print_display != "nothing":  # Possible values: ["nothing", "minimum", "init grid", "init and final grids", "all solution grids"] ## To manage print output
        print(f"Swapped {s1toswap }={gv_current[s1toswap]} and {s2toswap}={gv_current[s2toswap]} (values after the swap)")

    return gv_current

def fillgridrandomly(initialgridvalues):
    """Will return a new gridvalues with all empty squares filled randomly without putting the same digit twice in a 3x3 unit."""
    # Reminder:   units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'], #column
    #                             ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'], #line
    #                             ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']] #unit 3x3
    newgridvalues = initialgridvalues.copy() # dictionnary of initial values. Ex: {'A1': '4', 'A2': '.', 'A3': '.', 'A4': '.', 'A5': '.', 'A6': '.', 'A7': '8', 'A8': '.', 'A9': '5', ... }

    #Go through all 3x3 units and fill empty squares with random unused digits
    for fsou in firstsquaresofunit3x3: #loop through the 9 units. firstsquaresofunit3x3 is a list containing 9 squares. The first one per unit: ['A1', 'A4', 'A7', 'D1', 'D4', 'D7', 'G1', 'G4', 'G7']
        currentunit = units[fsou][2] # index 3 gives the 3x3 unit

        #loop trough all squares within a unit in order to extract initial squares with digits and digits used
        listofsquareswithinitialvalue, listofsquareswithoutvalue, digitsused = [], [], ''
        for s in currentunit: # loops trough the 9 values of the 3x3 unit
            d = initialgridvalues[s]
            if d in emptydigits: # no value      emptydigits = '0.'
                listofsquareswithoutvalue.append(s)
            else:
                listofsquareswithinitialvalue.append(s)
                digitsused += d #capture all values from initial grid (cannot be replaced)

        #Fill empty squares randomly
        remainingdigits = list(shuffled(digits.translate({ord(ch): '' for ch in digitsused}))) # removes the digits used, shuffles randomly and converts to a list
        #print(f"DG2: firstsquaresofunit={fsou} - currentunit={currentunit} - digitsused={digitsused} - remainingdigits={remainingdigits} - listofsquareswithinitialvalue={listofsquareswithinitialvalue}")

        for s in listofsquareswithoutvalue:
            newgridvalues[s] = remainingdigits.pop()
        if len(remainingdigits) != 0: raise ValueError(f"Programming error: remaining digits should be empty but contains: {remainingdigits}")
        #print(f"digitsused={digitsused} - remainingdigits={remainingdigits} = newgridvalues={newgridvalues}")

    return newgridvalues

def is_solved(gv_init, gv_current):
    """Returns True is puzzle is solved and False otherwise"""
    tmp, conflictvaluestotal, tmp = evalconflicts(gv_init, gv_current)
    return conflictvaluestotal == 0

def evalconflicts(gv_init, gv_current):
    """Receives the initial grid and the current grid and returns:
       - A grid_values of conflicts in which the initial puzzle squares show zero conflict (dict of {square: char} with a INT showing number of conflicts
       - A total evaluation of the conflicts in the grid (sum of all conflicts with possible factor
       - A dictionary representing a list of squares (values) with the number of conflicts (int) as a key
       Assumption: there are no conflicts in a 3x3 unit and there is a digit in each square"""
    # Reminder:   units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'], #column
    #                             ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'], #line
    #                             ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']] #unit 3x3

    conflicts_grid_values = {} # A grid_values of conflicts in which the initial puzzle squares show zero conflict (dict of {square: char} with a INT showing number of conflicts
    conflicts_dict = {} #- A dictionary representing a list of squares (values) with the number of conflicts as a key

    conflictvaluestotal = 0 #evaluation of the conflicts in the grid

    #Will loop through each square
    for r in rows:
        for c in cols:
            conflictvalue = 0
            if (gv_init[r+c] not in emptydigits) or (gv_current[r+c] in emptydigits): conflictvalue = 0 # square filled in the initial puzzle or current grid with empty digits
                #print(f"INITIAL r={r} c={c} gv_init[r+c]={gv_init[r+c]}")
            else:  # square randomly filled in the current grid
                # Will calculate the number of conflict
                u_column, u_line = units[r+c][0], units[r+c][1] # conflicts in column and conflicts in line
                #print(f"CURRENT r={r} c={c}, u_column={u_column}")
                for s in u_column:
                    if (s != r+c) and gv_current[s] == gv_current[r+c]: conflictvalue +=1
                for s in u_line:
                    if (s != r+c) and gv_current[s] == gv_current[r+c]: conflictvalue +=1

            # Update dictionaries
            conflicts_grid_values[r+c] = conflictvalue # put the value (int) of the conflict in grid_value
            if not conflicts_dict.get(conflictvalue): conflicts_dict[conflictvalue] = [] #Initializes a list of squares for this number of conflicts ex: {0: ['A1','A3, 'A7' ...], 1: ['A2','A5, 'A6' ...] }
            conflicts_dict[conflictvalue].append(r+c)

            conflictvaluestotal += conflictvalue

    #print(f"DGSCRAP max(conflicts_dict)={max(conflicts_dict)} with squares ={conflicts_dict[max(conflicts_dict)]} len(conflicts_dict)={len(conflicts_dict)} conflicts_dict={conflicts_dict}")

    return conflicts_grid_values, conflictvaluestotal, conflicts_dict

################ Display as 2-D grid ################
def displaygridv(gv_init, gv_current, showconflicts=True):
    """Display these values as a 2-D grid. If only display a initialgrid, you can pass currentgrid = initialgrid. Same as displaygrid, but used dictionnary gridvalues instead"""
    width = 3 # No need to display the possible values
    line = '+'.join(['-'*(width*3)]*3)

    if showconflicts: # Will evaluate conflicts in order to show them
        gv_conflicts, nbconflicts, conflicts_grid_values = evalconflicts(gv_init, gv_current) # Will initiale a grid_value containing number of conflicts

    # Header of the grid
    if showconflicts: displaystring = '-------- VALUE GRID ---------    --- CONFLICTS GRID (' + str(nbconflicts).ljust(3) + ') ----\n' # header
    else:             displaystring = '-------- VALUE GRID ---------\n'

    for r in rows:
        for c in cols: # Will print all digits of the current row (all columns)
            # displays the value_grid
            displaystring += (Back.BLACK if gv_init[r+c] not in emptydigits else Style.RESET_ALL) # Will highlight numbers from initial grid   emptydigits = '0.'
            displaystring += ' ' + str(gv_current[r+c]) + ' '
            displaystring += Style.RESET_ALL +  ('|' if c in '36' else '') + ('\n' if (c in '9') and (not showconflicts) else '') # separator after a group of 3 columns
            #displaystring += Style.RESET_ALL + ('|' if c in '36' else '') # separator after a group of 3 columns
        if showconflicts: # displays the value_grid
            displaystring += '    '
            for c2 in cols:
                displaystring += (Back.BLACK if gv_init[r+c2] not in emptydigits else Style.RESET_ALL) # Will highlight numbers from initial grid   emptydigits = '0.'
                displaystring += ' ' + str(gv_conflicts[r+c2]) + ' '
                displaystring += Style.RESET_ALL +  ('|' if c2 in '36' else '') + ('\n' if c2 in '9' else '') #display for a column

        if r in 'CF': displaystring = displaystring + line + ('    ' + line if showconflicts else '') + '\n'
    print(displaystring)

################ Search ################

def solve(grid, searchMethod, printdisplay=False):
    # Initializes a puzzle
    gv_init = grid_values(grid2)
    gv_current = fillgridrandomly(gv_init) #Fills all the 3x3 units randomly with unused numbers in unit

    if print_display in ["init grid", "init and final grids", "all solution grids"]:  # Possible values: ["nothing", "minimum", "init grid", "init and final grids", "all solution grids"] ## To manage print output
        displaygridv(gv_init, gv_current, True)

    if searchMethod == 'Hill Climbing':
        gv_new = improve_solution_hill_climb_highest_conflict(gv_init, gv_current)
        #gv new improve_solution_hill_climb_calc_all_swaps3x3(gv_init, gv_current)

    else:
        raise ValueError(f"Unknown search method {searchMethod}. Available search methods are {searchMethods}")

def all_swappables_squares_set(gv_init, gv_current):
    """Returns a set of all swappables squares withing current grid_value"""
    swappables_squares_set = {}

    raise ValueError('Not implemented') #DGHERE
    # for r in rows
    #     for c in cols

    #Go through all 3x3 units and fill empty squares with random unused digits
    for fsou in firstsquaresofunit3x3: #loop through the 9 units. firstsquaresofunit3x3 is a list containing 9 squares. The first one per unit: ['A1', 'A4', 'A7', 'D1', 'D4', 'D7', 'G1', 'G4', 'G7']
        currentunit = units[fsou][2] # index 3 gives the 3x3 unit

        #loop trough all squares within a unit in order to extract initial squares with digits and digits used
        listofsquareswithinitialvalue, listofsquareswithoutvalue, digitsused = [], [], ''
        for s in currentunit: # loops trough the 9 values of the 3x3 unit
            d = initialgridvalues[s]
            if d in emptydigits: # no value      emptydigits = '0.'
                listofsquareswithoutvalue.append(s)
            else:
                listofsquareswithinitialvalue.append(s)
                digitsused += d #capture all values from initial grid (cannot be replaced)

def improve_solution_hill_climb_calc_all_swaps3x3(gv_init, gv_current):
    """Receives a puzzle with conflicts and tries to decrease the number of conflicts by swapping 2 values
       using the Hill Climbing method.
       Will calculate total conflict for all possible swaps of a pair within a 3x3 unit and then choose the best"""

    #Determine all swappable squares and put them in a set
    #print(f"len={len(non_initial_squares_set(gv_init))} and non_initial_squares_set={non_initial_squares_set(gv_init)}")  # DGSCRAP
    all_swappables_squares = non_initial_squares_set(gv_init)
    print(f"len={len(all_swappables_squares)} and all_swappables_squares={all_swappables_squares}")  # DGSCRAP

    # For each swappable square, will create a tuple for each other swappable square in unit #DGHERE
    set_of_swappable_pairs = set() #DGHERE -> can move to another function
    i = 0 #DGSCRAP
    for r in rows:
        for c in cols:
            if r+c in all_swappables_squares:
                i += 1
                # Will loop for all combinations within units
                possible_swaps = set(squares_within_unit_list(r+c, "unit3x3")) - {r+c} # squares in unit, except current square
                possible_swaps = possible_swaps.intersection(all_swappables_squares) # only swappable squares
                if i == 1: print(f"{r+c} possible_swaps 2={possible_swaps}")  # DGSCRAP
    print(f"i={i} set_of_swappable_pairs={set_of_swappable_pairs}")

    # Go through all 3x3 units
    # for fsou in firstsquaresofunit3x3:  # loop through the 9 units. firstsquaresofunit3x3 is a list containing 9 squares. The first one per unit: ['A1', 'A4', 'A7', 'D1', 'D4', 'D7', 'G1', 'G4', 'G7']
    #     currentunit = units[fsou][2]  # index 3 gives the 3x3 unit

        # #DG FROM INITGRID
        # # loop trough all squares within a unit in order to extract initial squares with digits and digits used
        # listofsquareswithinitialvalue, listofsquareswithoutvalue, digitsused = [], [], ''
        # for s in currentunit:  # loops trough the 9 values of the 3x3 unit
        #     d = initialgridvalues[s]
        #     if d in emptydigits:  # no value      emptydigits = '0.'
        #         listofsquareswithoutvalue.append(s)
        #     else:
        #         listofsquareswithinitialvalue.append(s)
        #         digitsused += d  # capture all values from initial grid (cannot be replaced)

    # # Evaluates conflicts
    # gv_conflicts, totalconflicts, conflicts_grid_values = evalconflicts(gv_init, gv_current)
    # conflicts_gv_current = totalconflicts
    # count_swaps = 0
    #
    # while True: #Will stop only if unable to find a better successor
    #     #Swap 2 squares to try to improve
    #     gv_new = swap2numbers(gv_init, gv_current, conflicts_grid_values)
    #     if print_display == "all solution grids": # Possible values: ["nothing", "minimum", "init grid", "init and final grids", "all solution grids"] ## To manage print output
    #         displaygridv(gv_init, gv_new, True)
    #     gv_conflicts, totalconflicts, conflicts_grid_values = evalconflicts(gv_init, gv_new)
    #     if conflicts_gv_current <= totalconflicts: # didn't find a highest valued successor
    #         if print_display != "nothing": # Possible values: ["nothing", "minimum", "init grid", "init and final grids", "all solution grids"] ## To manage print output
    #             print(f"Found a local maximum with {conflicts_gv_current} conflicts after {count_swaps} swaps")
    #         return gv_current
    #     else: # found a highest valued successor and "climbs" there by replacing 'current' by 'neighbor'
    #         gv_current = gv_new
    #         conflicts_gv_current = totalconflicts
    #         count_swaps += 1

def improve_solution_hill_climb_highest_conflict(gv_init, gv_current):
    """Receives a puzzle with conflicts and tries to decrease the number of conflicts by swapping 2 values
       using the Hill Climbing method. Will print each step if print_display = True
       Will always start by swapping the square showing the highest number of conflicts"""

    # Evaluates conflicts
    gv_conflicts, totalconflicts, conflicts_grid_values = evalconflicts(gv_init, gv_current)
    conflicts_gv_current = totalconflicts
    count_swaps = 0

    while True: #Will stop only if unable to find a better successor
        #Swap 2 squares to try to improve
        gv_new = swap2numbers(gv_init, gv_current, conflicts_grid_values)
        if print_display == "all solution grids": # Possible values: ["nothing", "minimum", "init grid", "init and final grids", "all solution grids"] ## To manage print output
            displaygridv(gv_init, gv_new, True)
        gv_conflicts, totalconflicts, conflicts_grid_values = evalconflicts(gv_init, gv_new)
        if conflicts_gv_current <= totalconflicts: # didn't find a highest valued successor
            if print_display in ["init and final grids", "all solution grids"] : # Possible values: ["nothing", "minimum", "init grid", "init and final grids", "all solution grids"] ## To manage print output
                print("Solution grid:")
                displaygridv(gv_init, gv_current)
            if print_display != "nothing": # Possible values: ["nothing", "minimum", "init grid", "init and final grids", "all solution grids"] ## To manage print output
                print(f"Found a local maximum with {conflicts_gv_current} conflicts after {count_swaps} swaps.")
            return gv_current
        else: # found a highest valued successor and "climbs" there by replacing 'current' by 'neighbor'
            gv_current = gv_new
            conflicts_gv_current = totalconflicts
            count_swaps += 1

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

################ System test ################

import time, random

# def solve_all(grids, name='', showif=0.0, searchMethod='ToSpecify'):
#     """Attempt to solve a sequence of grids. Report results.
#     When showif is a number of seconds, display puzzles that take longer.
#     When showif is None, don't display any puzzles."""

#     def time_solve(grid):
#         #start = time.clock()
#         start = time.process_time()
#         values = solve(grid, searchMethod)
#         t = time.process_time()-start
##
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

################ Main routine ################
if __name__ == '__main__':
    test()

    # Will work mostly with grid_values instead of values used in the Norvig sudoku.py (current values instead of possible values)
    grid2 = '4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......'

    solve(grid2, 'Hill Climbing')

    print('Review DGSCRAP and DGHERE')

## References used:
## http://www.scanraid.com/BasicStrategies.htm
## http://www.sudokudragon.com/sudokustrategy.htm
## http://www.krazydad.com/blog/2005/09/29/an-index-of-sudoku-strategies/
## http://www2.warwick.ac.uk/fac/sci/moac/currentstudents/peter_cock/python/sudoku/
## https://www.sudokuoftheday.com/techniques/naked-pairs-triples/ (DG)