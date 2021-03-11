"""
Hill climing approach to solve a sudoku puzzle
Inspired by Stochastic search / optimization methods from https://en.wikipedia.org/wiki/Sudoku_solving_algorithms
Initial code copied from  http://norvig.com/sudoku.html
Will work mostly with grid_values instead of values used in the Norvig sudoku.py (no possible values)

Throughout this program we have:
   r is a row,    e.g. 'A'
   c is a column, e.g. '3'
   s is a square, e.g. 'A3'
   d is a digit,  e.g. '9'
   u is a unit,   e.g. ['A1','B1','C1','D1','E1','F1','G1','H1','I1'] # unit_type can be 'row', 'column', or 'unit3x3'
   grid is a grid,e.g. 81 non-blank chars, e.g. starting with '.18...7...
   gv = grid_values is a dict of {square: char} with '0' or '.' for empties.

firstsquaresofunit3x3 = cross('ADG', '147')  # list containing 9 squares: first per unit: ['A1', 'A4', 'A7'...
searchMethods = {'Brute Force', 'Norvig Heuristic', 'Norvig Improved', 'Hill Climbing'}
emptydigits = '0.'  # The digit values representing an empty square
unit_types = ['row', 'column', 'unit3x3']  # unit_type can be 'row', 'column', or 'unit3x3'
print_display = 'nothing'  # Values: ["nothing", "minimum", "init grid", "init and final grids", "all solution grids"]

"""
import random
import time
from colorama import Back, Style  # example: print(Fore.BLUE + displaystring)


class Sudoku:

    def __init__(self, grid, showif=0.0):
        self.showif = showif
        self.cols = '123456789'
        self.digits = '123456789'
        self.empty_digits = '0. '
        self.rows = 'ABCDEFGHI'
        self.unit_types = ['row', 'column', 'unit3x3']
        self.squares = self.cross(self.rows, self.cols)
        self.unit_list = (
                [self.cross(self.rows, c) for c in self.cols] +
                [self.cross(r, self.cols) for r in self.rows] +
                [self.cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')]
        )
        self.units = dict(
            (s, [u for u in self.unit_list if s in u]) for s in self.squares
        )
        self.peers = dict(
            (s, set(sum(self.units[s], [])) - {s}) for s in self.squares
        )
        # Convert grid into a dict of {square: char} with '0' or '.' for empties.
        # Example: {'A1': '4', 'A2': '.', 'A3': '.', 'A4': '.', 'A5': '.', 'A6': '.', 'A7': '8', 'A8': '.', 'A9': ...
        chars = [c for c in grid if c in self.cols or c in '0.']
        assert len(chars) == 81
        self.grid = grid
        self.gv_init = self.grid_values()
        self.gv_current = self.gv_init.copy() # Need to use function copy()
        self.gv_conflicts = None
        self.conflictsDict = None
        self.total_conflicts = 0
        self.first_squares_of_unit3x3 = self.cross('ADG', '147')
        self.search_methods = {'Brute Force', 'Norvig Heuristic', 'Norvig Improved', 'Hill Climbing'}
        self.search_method = 'Hill Climbing'

    def cross(self, A, B):
        # Cross product of elements in A and elements in B.
        return [a + b for a in A for b in B]

    # Unit Tests
    def test(self):
        # A set of tests that must pass.
        assert len(self.squares) == 81
        assert len(self.unit_list) == 27
        assert all(len(self.units[s]) == 3 for s in self.squares)
        assert all(len(self.peers[s]) == 20 for s in self.squares)

        assert self.units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'],
                                    ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
                                    ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']]

        assert self.peers['C2'] == {'A2', 'B2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2', 'C1', 'C3',
                                    'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'A1', 'A3', 'B1', 'B3'}

        return 'All tests pass.'

    ################ Parse a Grid ################
    def grid_values(self):
        """Convert grid into a dict of {square: char} with '0' or '.' for empties."""
        # Example: {'A1': '4', 'A2': '.', 'A3': '.', 'A4': '.', 'A5': '.', 'A6': '.', 'A7': '8', 'A8': '.', 'A9': ...
        chars = [c for c in self.grid if c in self.digits or c in '0.']
        assert len(chars) == 81
        return dict(zip(self.squares, chars))

    # Constraint functions
    def squares_causing_max_conflicts(self):
        # Will receive a grid filled with values and a conflicts_grid_values and will return:
        #   - a set of all squares having the maximum number of conflits
        #   - the number of conflicts (int) for this maximum"""
        max_conflicts = max(self.gv_conflicts)
        return self.gv_conflicts[max_conflicts], max_conflicts

    def is_initial_squares(self, s):
        # Will receive the initial grid and a square and return True if filled in the initial puzzle
        # loop trough all squares and list non-empty squares (initial puzzle)
        return self.gv_init[s] not in self.empty_digits

    def non_initial_squares_set(self):
        # Will return a set of the squares that were empty in the original puzzle
        # return {r+c for r in rows for c in cols if is_initial_squares(gv_init, r+c)}
        set_of_squares = set()
        for r in self.rows:
            for c in self.cols:
                if not self.is_initial_squares(r + c):
                    set_of_squares.add(r + c)
        return set_of_squares

    def remove_initial_squares_from_set(self, set_of_squares):
        # Will receive a set of squares and will return this set, without the initial squares
        return set_of_squares - self.initial_squares_set()

    def squares_within_unit_list(self, s, unit_type):
        # Returns a list of the squares within the same unit as s.
        # unit_type can be 'row', 'column', or 'unit3x3'
        assert unit_type in self.unit_types
        if unit_type == 'row':
            return self.units[s][0]
        elif unit_type == 'column':
            return self.units[s][1]
        elif unit_type == 'unit3x3':
            return self.units[s][2]
        else:
            raise ValueError(f"Unit type {unit_type} not implemented.")

    def possible_replacements_within_unit(self, s, unit_type):
        # Returns the squares within the same unit as s that can be replaced, excluding s.
        # unit_type can be 'row', 'column', or 'unit3x3'
        return (set(self.squares_within_unit_list(s, unit_type)) - set(s)) - self.initial_squares_set()

    def initial_squares_set(self):
        # Will receive the initial grid and return a set of all squares not empty
        # loop trough all squares and list non-empty squares (initial puzzle)
        set_initial_squares = set()
        for r in self.rows:
            for c in self.cols:
                if self.is_initial_squares(r + c):
                    set_initial_squares.add(r + c)
        return set_initial_squares

    def is_solved(self):
        # Returns True is puzzle is solved and False otherwise.
        return self.total_conflicts == 0

    def fill_grid_randomly(self):
        """Will return a new gridvalues with all empty squares filled randomly without putting the
           same digit twice in a 3x3 unit."""
        # Reminder:   units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'], #column
        #                             ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'], #line
        #                             ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']] #unit 3x3
        new_grid_values = self.gv_init.copy()  # dict of initial values. Ex: {'A1': '4', 'A2': '.', 'A3': '.', ...

        # Go through all 3x3 units and fill empty squares with random unused digits
        for fsou in self.first_squares_of_unit3x3:  # loop through the 9 units.
            current_unit = self.units[fsou][2]  # index 3 gives the 3x3 unit

            # Loop trough all squares within a unit in order to extract initial squares with digits and digits used
            list_of_squares_with_initial_value, list_of_squares_without_value, digits_used = [], [], ''
            for s in current_unit:  # loops trough the 9 values of the 3x3 unit
                d = self.gv_init[s]
                if d in self.empty_digits:  # no value
                    list_of_squares_without_value.append(s)
                else:
                    list_of_squares_with_initial_value.append(s)
                    digits_used += d  # capture all values from initial grid (cannot be replaced)

            # Fill empty squares randomly
            remaining_digits = list(
                shuffled(self.digits.translate({ord(c): '' for c in digits_used}))  # removes digits + shuffle
            )
            for s in list_of_squares_without_value:
                self.gv_current[s] = remaining_digits.pop()
            if len(remaining_digits) != 0:
                raise ValueError(
                    f"Programming error: remaining digits should be empty but contains: {remaining_digits}"
                )

    def count_conflicts(self, grid):
        """Receives the initial grid and the current grid and returns a total evaluation of the
           conflicts in the grid (sum of all conflicts)"""
        tmp, self.total_conflicts, tmp = self.eval_conflicts()
        return self.total_conflicts

    def eval_conflicts(self):
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
        for r in self.rows:
            for c in self.cols:
                conflict_value = 0
                if (self.gv_init[r + c] not in self.empty_digits) or (self.gv_current[r + c] in self.empty_digits):
                    conflict_value = 0  # square filled in the initial puzzle or current grid with empty digits
                else:  # square randomly filled in the current grid
                    # Will calculate the number of conflict
                    # Conflicts in column and conflicts in line
                    u_column, u_line = self.units[r + c][0], self.units[r + c][1]
                    for s in u_column:
                        if (s != r + c) and self.gv_current[s] == self.gv_current[r + c]:
                            conflict_value += 1
                    for s in u_line:
                        if (s != r + c) and self.gv_current[s] == self.gv_current[r + c]:
                            conflict_value += 1

                # Update dictionaries
                conflicts_grid_values[r + c] = conflict_value  # Put the value (int) of the conflict in grid_value
                if not conflicts_dict.get(conflict_value):
                    conflicts_dict[conflict_value] = []  # List of squares (values) for this number of conflicts (key)
                conflicts_dict[conflict_value].append(r + c)
                conflictvaluestotal += conflict_value

        self.gv_conflicts = conflicts_grid_values
        self.total_conflicts = conflictvaluestotal
        self.conflictsDict = conflicts_grid_values

        return conflicts_grid_values, conflictvaluestotal, conflicts_dict

    # Display as 2-D grid
    def display_gv(self, show_conflicts=True):
        """Display grid_values as a 2-D grid. If only display a initialgrid, you can pass currentgrid = initialgrid.
           Same as displaygrid(), but used dictionnary gridvalues instead"""
        width = 3  # No need to display the possible values
        line = '+'.join(['-' * (width * 3)] * 3)

        if show_conflicts:  # Will evaluate conflicts in order to show them
            self.gv_conflicts, nb_conflicts, conflicts_grid_values = self.eval_conflicts()
            # Header of the grid
            displaystring = '-------- VALUE GRID ---------    --- CONFLICTS GRID (' + str(nb_conflicts).ljust(
                3) + ') ----\n'  # header
        else:
            displaystring = '-------- VALUE GRID ---------\n'

        # Lines
        for r in self.rows:
            for c in self.cols:  # Will print all digits of the current row (all columns)
                # displays the value_grid
                # Will highlight numbers from initial grid   emptydigits = '0.'
                displaystring += (Back.BLACK if self.gv_init[r + c] not in self.empty_digits else Style.RESET_ALL)
                displaystring += ' ' + str(self.gv_current[r + c]) + ' '
                displaystring += Style.RESET_ALL + ('|' if c in '36' else '') + (
                    '\n' if (c in '9') and (not show_conflicts) else '')  # separator after a group of 3 columns
            if show_conflicts:  # displays the value_grid
                displaystring += '    '
                for c2 in self.cols:
                    # Will highlight numbers from initial grid   emptydigits = '0.'
                    displaystring += (Back.BLACK if self.gv_init[r + c2] not in self.empty_digits else Style.RESET_ALL)
                    displaystring += ' ' + str(self.gv_conflicts[r + c2]) + ' '
                    # Display for a column
                    displaystring += Style.RESET_ALL + ('|' if c2 in '36' else '') + ('\n' if c2 in '9' else '')

            if r in 'CF': displaystring = displaystring + line + ('    ' + line if show_conflicts else '') + '\n'
        print(displaystring)

    # Search
    def solve(self, search_method, verbose=False):
        self.search_method = search_method
        # Will solve a puzzle with the appropriate search method
        self.fill_grid_randomly()  # Fills all the 3x3 units randomly with unused numbers in unit

        if verbose in ['init grid', 'init and final grids', 'all solution grids']:
            self.display_gv(True)

        if self.search_method == 'Hill Climbing':
            self.gv_current = self.improve_solution_hill_climb_calc_all_swaps3x3(verbose)
            if verbose in ['init and final grids', 'all solution grids']:
                self.display_gv()
        else:
            raise ValueError(
                f'Unknown search method {self.search_method}. Available search methods are {self.search_methods}'
            )
        return self.gv_init, self.gv_current

    def improve_solution_hill_climb_calc_all_swaps3x3(self, verbose):
        """Receives a puzzle with conflicts and tries to decrease the number of conflicts by swapping 2 values
           using the Hill Climbing method.
           Will calculate total conflict for all possible swaps of a pair within a 3x3 unit and then choose the best"""

        # Create a list of swappable pairs (tuple) for each unit (not part of initial square)
        all_swappables_squares = self.non_initial_squares_set()  # Will only consider non initial squares as swappable
        set_of_swappable_pairs = set()  # Example: {('A3', 'B1'), ('A3', 'B3'), ('A3', 'C3')...
        for r in self.rows:
            for c in self.cols:
                if r + c in all_swappables_squares:
                    # Will loop for all combinations within units
                    possible_swaps = set(
                        self.squares_within_unit_list(r + c, 'unit3x3')
                    ) - {r + c}  # squares in unit, except current
                    possible_swaps = possible_swaps.intersection(all_swappables_squares)  # only swappable squares
                    for s in possible_swaps:
                        # Will insert the pairs in a set, and the first element of the pair will always be the smallest.
                        if r + c < s:
                            set_of_swappable_pairs.add((r + c, s))
                        else:
                            set_of_swappable_pairs.add((s, r + c))

        # Will simulate each swap, calculate the total conflicts for each swap and choose the best
        best_puzzle = self.gv_current
        current_total_conflicts = self.count_conflicts(best_puzzle)
        best_total_conflicts = current_total_conflicts

        while True:  # Loop until a maximum is found
            for pair in set_of_swappable_pairs:
                test_puzzle = self.gv_current.copy()
                # swap the 2 values
                test_puzzle[pair[0]], test_puzzle[pair[1]] = self.gv_current[pair[1]], self.gv_current[pair[0]]
                if self.count_conflicts(test_puzzle) < best_total_conflicts:  # found a better candidate
                    best_total_conflicts = self.count_conflicts(test_puzzle)
                    best_puzzle = test_puzzle

            if best_total_conflicts == current_total_conflicts:  # no improvement (local maximum or solution)
                if verbose:
                    print(f'FINAL SOLUTION: found maximum with {best_total_conflicts} conflicts.')
                return self.gv_current
            else:  # will try to improve
                self.gv_current = best_puzzle
                current_total_conflicts = best_total_conflicts
                if verbose:
                    print(f'Swapping{pair} and total conflicts is now {best_total_conflicts}')
                if verbose:
                    self.display_gv()


# Utilities
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


# System test


def solve_all(grids, name='', showif=0.0, search_method='Hill Climbing'):
    """Attempt to solve a sequence of grids. Report results.
    When showif is a number of seconds, display puzzles that take longer.
    When showif is None, don't display any puzzles."""

    def time_solve(grid):
        start = time.process_time()
        sudoku = Sudoku(grid)
        gv_init, gv_current = sudoku.solve(search_method)
        t = time.process_time() - start

        # Display puzzles that take long enough
        if showif is not None and t > showif:
            sudoku.display_gv()
            print('(%.2f seconds)\n' % t)

        return t, sudoku.is_solved()

    times, results = zip(*[time_solve(grid) for grid in grids])
    len_grids = len(grids)

    # Will avoid division by zero if time is too short (0.0).
    if sum(times) != 0.0:
        hz = len_grids / sum(times)
    else:
        hz = 999

    if len_grids >= 1:
        print("Solved %d of %d %s puzzles in %.2f secs (avg %.2f secs (%d Hz), max %.2f secs). - %s" % (
            sum(results), len_grids, name, sum(times), sum(times) / len_grids, hz, max(times), search_method))


if __name__ == '__main__':


    # Test with different files
    solve_all(from_file("MesSudokus/NakedPair.txt"), "NakedPT", -1.0, 'Hill Climbing')
    solve_all(from_file("MesSudokus/1puzzle.txt"), "1puzzle", 9.0, 'Hill Climbing')
    solve_all(from_file("MesSudokus/easy50.txt"), "easy50 ", 9.0, 'Hill Climbing')
    solve_all(from_file("MesSudokus/top95.txt"),      "top95  ", 9.0, 'Hill Climbing')
    solve_all(from_file("MesSudokus/hardest.txt"),    "hardest", 9.0, 'Hill Climbing')
    solve_all(from_file("MesSudokus/100sudoku.txt"),  "100puz ", 9.0, 'Hill Climbing')
    #solve_all(from_file("MesSudokus/1000sudoku.txt"), "1000puz", 9.0, 'Hill Climbing')


## References used:
## http://www.scanraid.com/BasicStrategies.htm
## http://www.sudokudragon.com/sudokustrategy.htm
## http://www.krazydad.com/blog/2005/09/29/an-index-of-sudoku-strategies/
## http://www2.warwick.ac.uk/fac/sci/moac/currentstudents/peter_cock/python/sudoku/
## https://www.sudokuoftheday.com/techniques/naked-pairs-triples/
