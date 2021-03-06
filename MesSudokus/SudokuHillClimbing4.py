# Hill climing approach to solve a sudoku puzzle
# Inspired by Stochastic search / optimization methods from https://en.wikipedia.org/wiki/Sudoku_solving_algorithms
## Initial code copied from  http://norvig.com/sudoku.html
# Will work mostly with grid_values instead of values used in the Norvig sudoku.py (no possible values)

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
    return [a + b for a in A for b in B]


digits = '123456789'
rows = 'ABCDEFGHI'
cols = digits
squares = cross(rows, cols)
unitlist = ([cross(rows, c) for c in cols] +
            [cross(r, cols) for r in rows] +
            [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')])
units = dict((s, [u for u in unitlist if s in u])
             for s in squares)
peers = dict((s, set(sum(units[s], [])) - set([s]))
             for s in squares)

# new variables created
firstsquaresofunit3x3 = cross('ADG', '147')  # list containing 9 squares: first per unit: ['A1', 'A4', 'A7', 'D1', ...
searchMethods = {'Brute Force', 'Norvig Heuristic', 'Norvig Improved', 'Hill Climbing'}
emptydigits = '0.'  # The digit values representing an empty square
unit_types = ['row', 'column', 'unit3x3']  # unit_type can be 'row', 'column', or 'unit3x3'
print_display = 'nothing'  # Values: ["nothing", "minimum", "init grid", "init and final grids", "all solution grids"]

# Text color management
from colorama import Fore, Back, Style  # example: print(Fore.BLUE + displaystring)


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
    assert peers['C2'] == {'A2', 'B2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2', 'C1', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8',
                           'C9', 'A1', 'A3', 'B1', 'B3'}
    print('All tests pass.')


################ Parse a Grid ################
def grid_values(grid):
    """Convert grid into a dict of {square: char} with '0' or '.' for empties."""
    # Example: {'A1': '4', 'A2': '.', 'A3': '.', 'A4': '.', 'A5': '.', 'A6': '.', 'A7': '8', 'A8': '.', 'A9': ...
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
    # return {r+c for r in rows for c in cols if is_initial_squares(gv_init, r+c)}  #DGIMPROVE? Can write in one line?
    set_of_squares = set()
    for r in rows:
        for c in cols:
            if not is_initial_squares(gv_init, r + c):
                set_of_squares.add(r + c)
    return set_of_squares


def remove_initial_squares_from_set(gv_init, set_of_squares):
    """Will receive a set of squares and will return this set, without the initial squares"""
    return set_of_squares - initial_squares_set(gv_init)


def squares_within_unit_list(s, unit_type):
    """Returns a list of the squares within the same unit as s.
       unit_type can be 'row', 'column', or 'unit3x3' """
    assert unit_type in unit_types
    if unit_type == 'row':
        return (units[s][0])
    elif unit_type == 'column':
        return (units[s][1])
    elif unit_type == 'unit3x3':
        return (units[s][2])
    else:
        raise ValueError(f"Unit type {unit_type} not implemented.")


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
            if is_initial_squares(gv_init, r + c):
                set_initialsquares.add(r + c)
    return set_initialsquares


# def swap2numbers(gv_init, gv_current, conflicts_grid_values):
#     """Will take a square with a maximum number of conflicts and swap it randomly within the 3x3 unit with
#        another square that isn't part of the initial puzzle. Will then return the new grid_value"""
#
#     # Selects randomly one of the squares with the maximum number of conflicts
#     s_withmaxconflicts, maxconflicts = squares_causing_max_conflicts(gv_init, gv_current, conflicts_grid_values)
#     s1toswap = some(shuffled(s_withmaxconflicts)) # random selection
#
#     # Find another square within 3x3 unit and swap randomly without considering the number of conflicts (TO IMPROVE?)
#     s2toswap = some(shuffled(possible_replacements_within_unit(gv_init, s1toswap, 'unit3x3')))
#     s1value = gv_current[s1toswap]
#     gv_current[s1toswap] = gv_current[s2toswap]
#     gv_current[s2toswap] = s1value
#
#     if print_display != "nothing":
#         print(f"Swapped {s1toswap }={gv_current[s1toswap]} and {s2toswap}={gv_current[s2toswap]} (values after the swap)")
#
#     return gv_current

def fillgridrandomly(initialgridvalues):
    """Will return a new gridvalues with all empty squares filled randomly without putting the
       same digit twice in a 3x3 unit."""
    # Reminder:   units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'], #column
    #                             ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'], #line
    #                             ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']] #unit 3x3
    newgridvalues = initialgridvalues.copy()  # dictionnary of initial values. Ex: {'A1': '4', 'A2': '.', 'A3': '.', ...

    # Go through all 3x3 units and fill empty squares with random unused digits
    for fsou in firstsquaresofunit3x3:  # loop through the 9 units.
        currentunit = units[fsou][2]  # index 3 gives the 3x3 unit

        # Loop trough all squares within a unit in order to extract initial squares with digits and digits used
        listofsquareswithinitialvalue, listofsquareswithoutvalue, digitsused = [], [], ''
        for s in currentunit:  # loops trough the 9 values of the 3x3 unit
            d = initialgridvalues[s]
            if d in emptydigits:  # no value
                listofsquareswithoutvalue.append(s)
            else:
                listofsquareswithinitialvalue.append(s)
                digitsused += d  # capture all values from initial grid (cannot be replaced)

        # Fill empty squares randomly
        remainingdigits = list(shuffled(digits.translate({ord(c): '' for c in digitsused})))  # removes digits + shuffle
        for s in listofsquareswithoutvalue:
            newgridvalues[s] = remainingdigits.pop()
        if len(remainingdigits) != 0:
            raise ValueError(f"Programming error: remaining digits should be empty but contains: {remainingdigits}")
        # print(f"digitsused={digitsused} - remainingdigits={remainingdigits} = newgridvalues={newgridvalues}")

    return newgridvalues


def countconflicts(gv_init, gv_current):
    """Receives the initial grid and the current grid and returns a total evaluation of the
       conflicts in the grid (sum of all conflicts)"""
    tmp, total_conflicts, tmp = evalconflicts(gv_init, gv_current)
    return total_conflicts


def is_solved(gv_init, gv_current):
    """Returns True is puzzle is solved and False otherwise"""
    return countconflicts == 0


def evalconflicts(gv_init, gv_current):
    """Receives the initial grid and the current grid and returns:
       - # A grid_values of conflicts (dict of {square: nb_of_conflits}
       - A total evaluation of the conflicts in the grid (sum of all conflicts)
       - A dictionary representing a list of squares (values) with the number of conflicts (int) as a key
       Assumption: there are no conflicts in a 3x3 unit and there is a digit in each square"""
    # Reminder:   units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'], #column
    #                             ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'], #line
    #                             ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']] #unit 3x3

    conflicts_grid_values = {}  # A grid_values of conflicts (dict of {square: nb_of_conflits}
    conflicts_dict = {}  # A dictionary representing a list of squares (values) with the number of conflicts as a key

    conflictvaluestotal = 0  # Evaluation of the conflicts in the grid

    # Will loop through each square
    for r in rows:
        for c in cols:
            conflictvalue = 0
            if (gv_init[r + c] not in emptydigits) or (gv_current[r + c] in emptydigits):
                conflictvalue = 0  # square filled in the initial puzzle or current grid with empty digits
                # print(f"INITIAL r={r} c={c} gv_init[r+c]={gv_init[r+c]}")
            else:  # square randomly filled in the current grid
                # Will calculate the number of conflict
                u_column, u_line = units[r + c][0], units[r + c][1]  # conflicts in column and conflicts in line
                # print(f"CURRENT r={r} c={c}, u_column={u_column}")
                for s in u_column:
                    if (s != r + c) and gv_current[s] == gv_current[r + c]: conflictvalue += 1
                for s in u_line:
                    if (s != r + c) and gv_current[s] == gv_current[r + c]: conflictvalue += 1

            # Update dictionaries
            conflicts_grid_values[r + c] = conflictvalue  # Put the value (int) of the conflict in grid_value
            if not conflicts_dict.get(conflictvalue):
                conflicts_dict[conflictvalue] = []  # List of squares (values) for this number of conflicts (key)
            conflicts_dict[conflictvalue].append(r + c)

            conflictvaluestotal += conflictvalue

    return conflicts_grid_values, conflictvaluestotal, conflicts_dict


################ Display as 2-D grid ################
def displaygridv(gv_init, gv_current, showconflicts=True):
    """Display grid_values as a 2-D grid. If only display a initialgrid, you can pass currentgrid = initialgrid.
       Same as displaygrid(), but used dictionnary gridvalues instead"""
    width = 3  # No need to display the possible values
    line = '+'.join(['-' * (width * 3)] * 3)

    if showconflicts:  # Will evaluate conflicts in order to show them
        gv_conflicts, nb_conflicts, conflicts_grid_values = evalconflicts(gv_init,
                                                                          gv_current)  # Will initiale a grid_value containing number of conflicts

    # Header of the grid
    if showconflicts:
        displaystring = '-------- VALUE GRID ---------    --- CONFLICTS GRID (' + str(nb_conflicts).ljust(
            3) + ') ----\n'  # header
    else:
        displaystring = '-------- VALUE GRID ---------\n'

    # Lines
    for r in rows:
        for c in cols:  # Will print all digits of the current row (all columns)
            # displays the value_grid
            displaystring += (Back.BLACK if gv_init[
                                                r + c] not in emptydigits else Style.RESET_ALL)  # Will highlight numbers from initial grid   emptydigits = '0.'
            displaystring += ' ' + str(gv_current[r + c]) + ' '
            displaystring += Style.RESET_ALL + ('|' if c in '36' else '') + (
                '\n' if (c in '9') and (not showconflicts) else '')  # separator after a group of 3 columns
        if showconflicts:  # displays the value_grid
            displaystring += '    '
            for c2 in cols:
                displaystring += (Back.BLACK if gv_init[
                                                    r + c2] not in emptydigits else Style.RESET_ALL)  # Will highlight numbers from initial grid   emptydigits = '0.'
                displaystring += ' ' + str(gv_conflicts[r + c2]) + ' '
                displaystring += Style.RESET_ALL + ('|' if c2 in '36' else '') + (
                    '\n' if c2 in '9' else '')  # Display for a column

        if r in 'CF': displaystring = displaystring + line + ('    ' + line if showconflicts else '') + '\n'
    print(displaystring)


################ Search ################
def solve_grid_values(grid, searchMethod, printdisplay=False):
    """ Will solve a puzzle with the appropriate search method"""
    # Initializes a puzzle
    gv_init = grid_values(grid)
    gv_current = fillgridrandomly(gv_init)  # Fills all the 3x3 units randomly with unused numbers in unit

    if print_display in ["init grid", "init and final grids", "all solution grids"]:
        displaygridv(gv_init, gv_current, True)

    if searchMethod == 'Hill Climbing':
        gv_new = improve_solution_hill_climb_calc_all_swaps3x3(gv_init, gv_current)
        if print_display in ["init and final grids", "all solution grids"]: displaygridv(gv_init, gv_new)
    else:
        raise ValueError(f"Unknown search method {searchMethod}. Available search methods are {searchMethods}")
    return gv_init, gv_new


def improve_solution_hill_climb_calc_all_swaps3x3(gv_init, gv_current):
    """Receives a puzzle with conflicts and tries to decrease the number of conflicts by swapping 2 values
       using the Hill Climbing method.
       Will calculate total conflict for all possible swaps of a pair within a 3x3 unit and then choose the best"""

    # Create a list of swappable pairs (tuple) for each unit (not part of initial square)
    all_swappables_squares = non_initial_squares_set(gv_init)  # Will only consider non initial squares as swappable
    set_of_swappable_pairs = set()  # Example: {('A3', 'B1'), ('A3', 'B3'), ('A3', 'C3')...
    for r in rows:
        for c in cols:
            if r + c in all_swappables_squares:
                # Will loop for all combinations within units
                possible_swaps = set(squares_within_unit_list(r + c, "unit3x3")) - {
                    r + c}  # squares in unit, except current
                possible_swaps = possible_swaps.intersection(all_swappables_squares)  # only swappable squares
                for s in possible_swaps:
                    # Will insert the pairs in a set, and the first element of the pair will always be the smallest.
                    if r + c < s:
                        set_of_swappable_pairs.add((r + c, s))
                    else:
                        set_of_swappable_pairs.add((s, r + c))

    # Will simulate each swap, calculate the total conflicts for each swap and choose the best
    best_puzzle = gv_current
    current_total_conflicts = countconflicts(gv_init, gv_current)
    best_total_conflicts = current_total_conflicts

    while True:  # Loop until a maximum is found
        for pair in set_of_swappable_pairs:
            test_puzzle = gv_current.copy()
            test_puzzle[pair[0]], test_puzzle[pair[1]] = gv_current[pair[1]], gv_current[pair[0]]  # swap the 2 values
            if countconflicts(gv_init, test_puzzle) < best_total_conflicts:  # found a better candidate
                best_total_conflicts = countconflicts(gv_init, test_puzzle)
                best_puzzle = test_puzzle

        if best_total_conflicts == current_total_conflicts:  # no improvement (local maximum or solution)
            if print_display != 'nothing': print(
                f"FINAL SOLUTION: found maximum with {best_total_conflicts} conflicts.")
            return gv_current
        else:  # will try to improve
            if print_display != 'nothing': print(f"Swapping{pair} and total conflicts is now {best_total_conflicts}")
            if print_display == 'all solution grids': displaygridv(gv_init, best_puzzle)
            gv_current = best_puzzle
            current_total_conflicts = best_total_conflicts


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


def solve_all(grids, name='', showif=0.0, searchMethod='ToSpecify'):
    """Attempt to solve a sequence of grids. Report results.
    When showif is a number of seconds, display puzzles that take longer.
    When showif is None, don't display any puzzles."""

    def time_solve(grid):
        # start = time.clock()
        start = time.process_time()
        if searchMethod == 'Hill Climbing':
            gv_init, gv_current = solve_grid_values(grid, searchMethod)
        else:
            values = solve(grid, searchMethod)
        t = time.process_time() - start
        #
        ## Display puzzles that take long enough
        if showif is not None and t > showif:
            if searchMethod == 'Hill Climbing':
                displaygridv(gv_init, gv_current)
            else:
                display(grid_values(grid))
                if values: display(values)
            print('(%.2f seconds)\n' % t)

        if searchMethod == 'Hill Climbing':
            return (t, is_solved(gv_init, gv_current))
        else:
            return (t, solved(values))

    times, results = zip(*[time_solve(grid) for grid in grids])
    N = len(grids)

    # Will avoid division by zero if time is too short (0.0).
    if sum(times) != 0.0:
        hz = N / sum(times)
    else:
        hz = 999

    if N >= 1:
        print("Solved %d of %d %s puzzles in %.2f secs (avg %.2f secs (%d Hz), max %.2f secs). - %s" % (
            sum(results), N, name, sum(times), sum(times) / N, hz, max(times), searchMethod))


def solved(values):
    "A puzzle is solved if each unit is a permutation of the digits 1 to 9."

    def unitsolved(unit): return set(values[s] for s in unit) == set(digits)

    return values is not False and all(unitsolved(unit) for unit in unitlist)


################ Main routine ################
if __name__ == '__main__':
    test()

    # Demo one sudoku with display of each step
    grid2 = '4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......'
    print_display_old = print_display
    print_display = "all solution grids"
    solve_grid_values(grid2, 'Hill Climbing')
    print_display = print_display_old

    # Test with different files
    solve_all(from_file("1puzzle.txt"), "1puzzle", 9.0, 'Hill Climbing')
    solve_all(from_file("easy50.txt"), "easy50 ", 9.0, 'Hill Climbing')
    # solve_all(from_file("top95.txt"),      "top95  ", 9.0, 'Hill Climbing')
    # solve_all(from_file("hardest.txt"),    "hardest", 9.0, 'Hill Climbing')
    # solve_all(from_file("100sudoku.txt"),  "100puz ", 9.0, 'Hill Climbing')
    # solve_all(from_file("1000sudoku.txt"), "1000puz", 9.0, 'Hill Climbing')
    # solve_all(from_file("NakedPair.txt"),  "NakedPT", 9.0, 'Hill Climbing')

## References used:
## http://www.scanraid.com/BasicStrategies.htm
## http://www.sudokudragon.com/sudokustrategy.htm
## http://www.krazydad.com/blog/2005/09/29/an-index-of-sudoku-strategies/
## http://www2.warwick.ac.uk/fac/sci/moac/currentstudents/peter_cock/python/sudoku/
## https://www.sudokuoftheday.com/techniques/naked-pairs-triples/
