"""A game-specific implementations of utility functions.
"""
from __future__ import print_function, division

import copy

import numpy as np

from .consts import *


class GameState:
    def __init__(self):
        """ Initializing the board and current player.
        """

        self.board = np.zeros((BOARD_ROWS, BOARD_COLS), dtype=int)
        self.curr_player = RED_PLAYER
        self.mcts = None
        self.move = None

    def can_play(self, column):
        """
        Check if the given column is free
        """
        return np.sum(np.abs(self.board[:, column])) < len(self.board[:, column])

    def get_possible_moves(self):
        return [i for i in range(self.board.shape[1]) if self.can_play(i)]

    def perform_move(self, move):
        """
        Play at given column, if no player provided, calculate which player must play, otherwise force player to play
        Return new grid and winner
        """
        self.move = move[0]
        game_state = copy.deepcopy(self)
        column = move[0]
        if self.can_play(column):
            row = self.board.shape[0] - 1 - np.sum(np.abs(self.board[:, column]), dtype=int)
            game_state.board[row, column] = self.curr_player
        else:
            raise Exception('Error : Column {} is full'.format(column))

        # Updating the current player.
        winner = game_state.curr_player if game_state.is_winner(row, column) else 0
        game_state.curr_player = OPPONENT_COLOR[game_state.curr_player]
        return game_state, winner

    def draw_board(self):
        print_grid = self.board.astype(str)
        print_grid[print_grid == '-1'] = 'X'
        print_grid[print_grid == '1'] = 'O'
        print_grid[print_grid == '0'] = ' '
        res = str(print_grid).replace("'", "")
        res = res.replace('[[', '[')
        res = res.replace(']]', ']')
        print(' ' + res)
        print('  ' + ' '.join('0123456'))
        print("\n" + PLAYER_NAME[self.curr_player] + " Turn!\n\n")

    def __hash__(self):
        """This object can be inserted into a set or as dict key. NOTICE: Changing the object after it has been inserted
        into a set or dict (as key) may have unpredicted results!!!
        """
        return hash(','.join([self.board[(i, j)]
                              for i in range(BOARD_ROWS)
                              for j in range(BOARD_COLS)] + [self.curr_player]))

    def __eq__(self, other):
        return isinstance(other, GameState) and self.board == other.board and self.curr_player == other.curr_player

    def is_winner(self,row,col):
        return has_won(self.board, self.curr_player, row, col)


def has_won(board, player, row, column):
    """
    Check if player has won with is new piece
    """
    player += 1
    board += 1
    row_str = ''.join(board[row, :].astype(str).tolist())
    col_str = ''.join(board[:, column].astype(str).tolist())
    up_diag_str = ''.join(np.diagonal(board, offset=(column - row)).astype(str).tolist())
    down_diag_str = ''.join(
        np.diagonal(np.rot90(board), offset=- board.shape[1] + (column + row) + 1).astype(str).tolist())

    board -= 1
    victory_pattern = str(player) * 4
    player -= 1
    if victory_pattern in row_str:
        return True
    if victory_pattern in col_str:
        return True
    if victory_pattern in up_diag_str:
        return True
    if victory_pattern in down_diag_str:
        return True

    return False


def get_player_to_play(grid):
    """
    Get player to play given a grid
    """
    player_1 = 0.5 * np.abs(np.sum(grid-1))
    player_2 = 0.5 * np.sum(grid + 1)

    if player_1 > player_2:
        return 1
    else:
        return -1


def can_play(board, column):
    return np.sum(np.abs(board[:, column])) < len(board[:, column])


def play(grid_, column, player=None):
    """
    Play at given column, if no player provided, calculate which player must play, otherwise force player to play
    Return new grid and winner
    """
    grid = grid_.copy()
    if player is None:
        player = get_player_to_play(grid)

    if can_play(grid, column):
        row = grid.shape[0] - 1 - np.sum(np.abs(grid[:, column]), dtype=int)
        grid[row, column] = player
    else:
        raise Exception('Error : Column {} is full'.format(column))
    return grid, player if has_won(grid, player, row, column) else 0