# ===============================================================================
# Imports
# ===============================================================================
import copy
import random
import abstract
from connect_4.board import GameState, can_play
from utils import run_with_limited_time, ExceededTimeError
import time
import numpy as np
from connect_4.board import get_player_to_play, play
from connect_4.consts import BOARD_COLS, BOARD_ROWS, OPPONENT_COLOR

# ===============================================================================
# Globals
# ===============================================================================

PAWN_WEIGHT = 1
KING_WEIGHT = 1.5


# ===============================================================================
# Player
# ===============================================================================

class Node:

    def __init__(self, state, winning, move, parent):
        self.parent = parent
        self.move = move
        self.win = 0
        self.games = 0
        self.children = None
        self.state = state
        self.winner = winning

    def set_children(self, children):
        self.children = children

    def get_uct(self):
        if self.games == 0:
            return None
        return (self.win/self.games) + np.sqrt(2*np.log(self.parent.games)/self.games)

    def select_move(self):
        """
        Select best move and advance
        :return:
        """
        if self.children is None:
            return None, None

        winners = [child for child in self.children if child.winner]
        if len(winners) > 0:
            return winners[0], winners[0].move

        games = [child.win/child.games if child.games > 0 else 0 for child in self.children]
        best_child = self.children[np.argmax(games)]
        return best_child, best_child.move

    def get_children_with_move(self, move):
        if self.children is None:
            return None
        for child in self.children:
            if child.move == move:
                return child

        raise Exception('Not existing child')


def create_grid(sizeX=6, sizeY=7):
    return np.zeros((sizeX, sizeY), dtype=int)


def reset(grid):
    return np.zeros(grid.shape, dtype=int)


def to_state(grid):
    grid += 1
    res = ''.join(grid.astype(str).flatten().tolist())
    grid -=1
    return res


def valid_move(grid):
    return [i for i in range(grid.shape[1]) if can_play(grid, i)]


def random_play_improved(grid):

    def get_winning_moves(grid, moves, player):
        return [move for move in moves if play(grid, move, player=player)[1]]

    # If can win, win
    while True:
        moves = valid_move(grid)
        if len(moves) == 0:
            return 0
        player_to_play = get_player_to_play(grid)

        winning_moves = get_winning_moves(grid, moves, player_to_play)
        loosing_moves = get_winning_moves(grid, moves, -player_to_play)

        if len(winning_moves) > 0:
            selected_move = winning_moves[0]
        elif len(loosing_moves) == 1:
            selected_move = loosing_moves[0]
        else:
            selected_move = random.choice(moves)
        grid, winner = play(grid, selected_move)
        if np.abs(winner) > 0:
            return player_to_play


def train_mcts_during(mcts, training_time):
    clock = time.process_time()
    while (time.process_time() - clock - 0.05) < training_time:
        mcts = train_mcts_once(mcts)
    return mcts


def train_mcts_once(mcts=None):

    if mcts is None:
        mcts = Node(create_grid(), 0, None,  None)

    node = mcts

    # selection
    while node.children is not None:
        # Select highest uct
        ucts = [child.get_uct() for child in node.children]
        if None in ucts:
            node = random.choice(node.children)
        else:
            node = node.children[np.argmax(ucts)]

    # expansion, no expansion if terminal node
    moves = valid_move(node.state)
    if len(moves) > 0:

        if node.winner == 0:

            states = [(play(node.state, move), move) for move in moves]
            # if childrens equal to None then extend all the childrens
            node.set_children([Node(state_winning[0], state_winning[1], move=move, parent=node) for state_winning, move in states])
            # simulation
            winner_nodes = [n for n in node.children if n.winner]
            if len(winner_nodes) > 0:
                node = winner_nodes[0]
                victorious = node.winner
            else:
                node = random.choice(node.children)
                victorious = random_play_improved(node.state)
        else:
            victorious = node.winner

        # backpropagation
        parent = node
        while parent is not None:
            parent.games += 1
            if victorious != 0 and get_player_to_play(parent.state) != victorious:
                parent.win += 1
            parent = parent.parent


    else:
        print('no valid moves, expended all')

    return mcts


class Player(abstract.AbstractPlayer):
    def __init__(self, setup_time, player_color, time_per_turn):
        abstract.AbstractPlayer.__init__(self, setup_time, player_color, time_per_turn)
        self.clock = time.process_time()
        self.time_per_turn = time_per_turn
        self.mcts = None
        for i in range(200):
            self.mcts = train_mcts_once(self.mcts)

    def get_move(self, board_state, possible_moves):
        board_state.mcts = self.mcts
        self.clock = time.process_time()

        # opponent move
        if board_state.move is not None:
            # train mcts to extend all his childrens
            try:
                node, run_time = run_with_limited_time(
                    train_mcts_during,
                    (board_state.mcts, (self.time_per_turn - (time.process_time() - self.clock) - 0.05)/2), {},
                    self.time_per_turn - (time.process_time() - self.clock) - 0.05)
                if node is not None:
                    board_state.mcts = board_state.mcts.get_children_with_move(board_state.move)
            except (ExceededTimeError, MemoryError):
                print('no more time')
        best_move = possible_moves[0]
        try:
            node, run_time = run_with_limited_time(
                train_mcts_during,
                (board_state.mcts, self.time_per_turn - (time.process_time() - self.clock) - 0.5), {},
                self.time_per_turn - (time.process_time() - self.clock) - 0.05)
            if node is not None:
                board_state.mcts, best_move = node.select_move()
        except (ExceededTimeError, MemoryError):
            print('no more time')
        self.mcts = board_state.mcts
        return best_move

    def no_more_time(self):
        return (time.process_time() - self.clock) >= self.time_per_turn

    def __repr__(self):
        return 'mcst'


"""
        **************************CLASS NODE****************************
"""
