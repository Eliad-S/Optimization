"""Generic utility functions
"""
# from __future__ import print_function
from random import shuffle
from threading import Thread
from queue import Queue
import time
import copy

from connect_4.consts import BOARD_ROWS, BOARD_COLS, OPPONENT_COLOR

INFINITY = float(6000)


class ExceededTimeError(RuntimeError):
    """Thrown when the given function exceeded its runtime.
    """
    pass


def function_wrapper(func, args, kwargs, result_queue):
    """Runs the given function and measures its runtime.

    :param func: The function to run.
    :param args: The function arguments as tuple.
    :param kwargs: The function kwargs as dict.
    :param result_queue: The inter-process queue to communicate with the parent.
    :return: A tuple: The function return value, and its runtime.
    """
    start = time.process_time()
    try:
        result = func(*args, **kwargs)
    except MemoryError as e:
        result_queue.put(e)
        return

    runtime = time.process_time() - start
    result_queue.put((result, runtime))


def run_with_limited_time(func, args, kwargs, time_limit):
    """Runs a function with time limit

    :param func: The function to run.
    :param args: The functions args, given as tuple.
    :param kwargs: The functions keywords, given as dict.
    :param time_limit: The time limit in seconds (can be float).
    :return: A tuple: The function's return value unchanged, and the running time for the function.
    :raises PlayerExceededTimeError: If player exceeded its given time.
    """
    q = Queue()
    t = Thread(target=function_wrapper, args=(func, args, kwargs, q))
    t.start()

    # This is just for limiting the runtime of the other thread, so we stop eventually.
    # It doesn't really measure the runtime.
    t.join(time_limit)

    if t.is_alive():
        raise ExceededTimeError

    q_get = q.get()
    if isinstance(q_get, MemoryError):
        raise q_get
    return q_get


def count_sequence(board, player, length):
    """ Given the board state , the current player and the length of Sequence you want to count
        Return the count of Sequences that have the give length
    """

    def vertical_seq(row, col):
        """Return 1 if it found a vertical sequence with the required length
        """
        count = 0
        for rowIndex in range(row, BOARD_ROWS):
            if board[rowIndex][col] == board[row][col]:
                count += 1
            else:
                break
        if count >= length:
            return 1
        else:
            return 0

    def horizontalSeq(row, col):
        """Return 1 if it found a horizontal sequence with the required length
        """
        count = 0
        for colIndex in range(col, BOARD_COLS):
            if board[row][colIndex] == board[row][col]:
                count += 1
            else:
                break
        if count >= length:
            return 1
        else:
            return 0

    def negDiagonalSeq(row, col):
        """Return 1 if it found a negative diagonal sequence with the required length
        """
        count = 0
        col_index = col
        for rowIndex in range(row, -1, -1):
            if col_index > BOARD_ROWS:
                break
            elif board[rowIndex][col_index] == board[row][col]:
                count += 1
            else:
                break
            col_index += 1 # increment column when row is incremented
        if count >= length:
            return 1
        else:
            return 0

    def posDiagonalSeq(row, col):
        """Return 1 if it found a positive diagonal sequence with the required length
        """
        count = 0
        colIndex = col
        for rowIndex in range(row, BOARD_ROWS):
            if colIndex > BOARD_ROWS:
                break
            elif board[rowIndex][colIndex] == board[row][col]:
                count += 1
            else:
                break
            colIndex += 1 # increment column when row incremented
        if count >= length:
            return 1
        else:
            return 0

    totalCount = 0
    # for each piece in the board...
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            # ...that is of the player we're looking for...
            if board[row][col] == player:
                # check if a vertical streak starts at (row, col)
                totalCount += vertical_seq(row, col)
                # check if a horizontal four-in-a-row starts at (row, col)
                totalCount += horizontalSeq(row, col)
                # check if a diagonal (both +ve and -ve slopes) four-in-a-row starts at (row, col)
                totalCount += (posDiagonalSeq(row, col) + negDiagonalSeq(row, col))
    # return the sum of sequences of length 'length'
    return totalCount


class MiniMaxWithAlphaBetaPruning:
    def __init__(self, utility, my_color, no_more_time):
        """Initialize a MiniMax algorithms with alpha-beta pruning.

        :param utility: The utility function. Should have state as parameter.
        :param my_color: The color of the player who runs this MiniMax search.
        :param no_more_time: A function that returns true if there is no more time to run this search, or false if
                             there is still time left.
        :param selective_deepening: A functions that gets the current state, and
                        returns True when the algorithm should continue the search
                        for the minimax value recursivly from this state.
        """
        self.utility = utility
        self.my_color = my_color
        self.no_more_time = no_more_time


    def search(self, game_state, depth, alpha, beta, maximizing_player):
        """Start the MiniMax algorithm.

        :param state: The state to start from.
        :param depth: The maximum allowed depth for the algorithm.
        :param alpha: The alpha of the alpha-beta pruning.
        :param alpha: The beta of the alpha-beta pruning.
        :param maximizing_player: Whether this is a max node (True) or a min node (False).
        :return: A tuple: (The alpha-beta algorithm value, The move in case of max node or None in min mode)
        """
        if self.no_more_time() or depth <= 0:
            return self.utility(game_state), None

        next_moves = game_state.get_possible_moves()
        if not next_moves:
            # This player has no moves. So the previous player is the winner.
            return INFINITY if game_state.curr_player != self.my_color else -INFINITY, None

        if maximizing_player:
            selected_move = next_moves[0]
            best_move_utility = -INFINITY
            for move in next_moves:
                new_state, _ = game_state.perform_move((move, 0))
                minimax_value, _ = self.search(new_state, depth - 1, alpha, beta, False)
                alpha = max(alpha, minimax_value)
                if minimax_value > best_move_utility:
                    best_move_utility = minimax_value
                    selected_move = move
                if beta <= alpha or self.no_more_time():
                    break
            return alpha, selected_move

        else:
            for move in next_moves:
                new_state, _ = game_state.perform_move((move, 0))
                beta = min(beta, self.search(new_state, depth - 1, alpha, beta, True)[0])
                if beta <= alpha or self.no_more_time():
                    break
            return beta, None

    # def MiniMaxAlphaBeta(self, game_state, depth):
    #     # get array of possible moves
    #     valid_moves = game_state.get_possible_moves()
    #     shuffle(valid_moves)
    #     best_move = valid_moves[0]
    #     best_score = float("-inf")
    #     # initial alpha & beta values for alpha-beta pruning
    #     alpha = float("-inf")
    #     beta = float("inf")
    #
    #     player = game_state.curr_player
    #     opponent = OPPONENT_COLOR[player]
    #
    #     # go through all of those boards
    #     for move in valid_moves:
    #         # create new board from move
    #         temp_state, _ = game_state.perform_move((move, 0))
    #         # call min on that new grid
    #         board_score = self.minimizeBeta(temp_state, depth - 1, alpha, beta, player, opponent)
    #         if board_score > best_score:
    #             best_score = board_score
    #             best_move = move
    #     return best_move
    #
    # def minimizeBeta(self, game_state, depth, a, b, player, opponent):
    #     valid_moves = []
    #     won = 0
    #     for col in range(7):
    #         # if column col is a legal move...
    #         if game_state.can_play(col):
    #             # make the move in column col for curr_player
    #             temp_state, player = game_state.perform_move((col, 0))
    #             if player != 0:
    #                 won = player
    #             valid_moves.append(col)
    #
    #     # check to see if game over
    #     if depth == 0 or len(valid_moves) == 0 or player != 0:
    #         return self.utility(game_state)
    #
    #     valid_moves = game_state.get_possible_moves()
    #     beta = b
    #
    #     # if end of tree evaluate scores
    #     for move in valid_moves:
    #         board_score = float("inf")
    #         # else continue down tree as long as ab conditions met
    #         if a < beta:
    #             temp_state, _ = game_state.perform_move((move, 0))
    #             board_score = self.maximizeAlpha(temp_state, depth - 1, a, beta, player, opponent)
    #
    #         if board_score < beta:
    #             beta = board_score
    #     return beta
    #
    # def maximizeAlpha(self, game_state, depth, a, b, player, opponent):
    #     valid_moves = []
    #     won = 0
    #     for col in range(7):
    #         # if column col is a legal move...
    #         if game_state.can_play(col):
    #             # make the move in column col for curr_player
    #             temp_state, player = game_state.perform_move((col, 0))
    #             if player != 0:
    #                 won = player
    #             valid_moves.append(col)
    #
    #     # check to see if game over
    #     if depth == 0 or len(valid_moves) == 0 or won != 0:
    #         return self.utility(game_state)
    #
    #     alpha = a
    #     # if end of tree, evaluate scores
    #     for move in valid_moves:
    #         board_score = float("-inf")
    #         if alpha < b:
    #             temp_state = game_state.perform_move(move)
    #             board_score = self.minimizeBeta(temp_state, depth - 1, alpha, b, player, opponent)
    #
    #         if board_score > alpha:
    #             alpha = board_score
    #     return alpha




