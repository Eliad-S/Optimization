# ===============================================================================
# Imports
# ===============================================================================
import copy
import random
import abstract
from connect_4.board import GameState
from utils import run_with_limited_time, ExceededTimeError
import time
import numpy as np
from connect_4.consts import BOARD_COLS, BOARD_ROWS, OPPONENT_COLOR

# ===============================================================================
# Globals
# ===============================================================================

PAWN_WEIGHT = 1
KING_WEIGHT = 1.5


# ===============================================================================
# Player
# ===============================================================================
def random_play_improved(game_state):
    def get_winning_moves(game_state, moves):
        return [move for move in moves if game_state.perform_move((move, 0))[1]]

    # If can win, win
    curr_turn = True
    while True:
        moves = game_state.get_possible_moves()
        if len(moves) == 0:
            return 0
        if curr_turn:
            player_to_play = game_state.curr_player
            curr_turn = False
        else:
            player_to_play = OPPONENT_COLOR[game_state.curr_player]
            curr_turn = True

        winning_moves = get_winning_moves(game_state, moves)
        loosing_moves = get_winning_moves(game_state, moves)

        if len(winning_moves) > 0:
            selected_move = winning_moves[0]
        elif len(loosing_moves) == 1:
            selected_move = loosing_moves[0]
        else:
            selected_move = random.choice(moves)
        t, winner = game_state.perform_move((selected_move, 0))
        game_state = t
        if np.abs(winner) > 0:
            return player_to_play


def get_player_to_play(grid):
    """
    Get player to play given a grid
    """
    player_1 = 0.5 * np.abs(np.sum(grid - 1))
    player_2 = 0.5 * np.sum(grid + 1)

    if player_1 > player_2:
        return 1
    else:
        return -1


def train_mcts_once(mcts, game_state=None):
    if mcts is None:
        if game_state is None:
            mcts = Node(GameState(), 0, None, None)
        else:
            mcts = Node(game_state, 0, None, None)
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
    moves = node.game_state.get_possible_moves()
    if len(moves) > 0:

        if node.winner == 0:

            states = [(node.game_state.perform_move([move, 0]), move) for move in moves]
            node.set_children(
                [Node(state_winning[0], state_winning[1], move=move, parent=node) for state_winning, move in
                 states])
            # simulation
            winner_nodes = [n for n in node.children if n.winner]
            if len(winner_nodes) > 0:
                node = winner_nodes[0]
                victorious = node.winner
            else:
                node = random.choice(node.children)
                victorious = random_play_improved(node.game_state)
        else:
            victorious = node.winner

        # backpropagation
        parent = node
        while parent is not None:
            parent.games += 1
            if victorious != 0 and get_player_to_play(parent.game_state.board) != victorious:
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
        for i in range(300):
            self.mcts = train_mcts_once(self.mcts, None)

    def train_mcts_during(self, board_state, training_time):
        # mcts = train_mcts_once(self.mcts, board_state)
        start = int(round(time.time() * 1000))
        current = start
        while (current - start) < training_time:
            self.mcts = train_mcts_once(self.mcts, None)
            current = int(round(time.time() * 1000))
        print("after the opp ,before me")
        print(self.mcts.game_state.board)
        return self.mcts

    def get_move(self, board_state, possible_moves):
        for ch in self.mcts.children:
            if np.array_equal(board_state.board, ch.game_state.board):
                self.mcts = ch
        self.clock = time.process_time()
        if len(possible_moves) == 1:
            return possible_moves[0]

        best_move = possible_moves[0]
        node = None
        try:
            node, run_time = run_with_limited_time(
                self.train_mcts_during,
                (copy.deepcopy(board_state), self.time_per_turn - (time.process_time() - self.clock) - 0.05), {},
                self.time_per_turn - (time.process_time() - self.clock) - 0.05)
            if node is not None:
                self.mcts, best_move = node.select_move()
        except (ExceededTimeError, MemoryError):
            print('no more time')
        print("after me:")
        print(self.mcts.game_state.board)
        return best_move

    def no_more_time(self):
        return (time.process_time() - self.clock) >= self.time_per_turn

    def __repr__(self):
        return '{} {}'.format(abstract.AbstractPlayer.__repr__(self), 'mcst_player')


"""
        **************************CLASS NODE****************************
"""


class Node:

    def __init__(self, game_state, winning, move, parent):
        self.parent = parent
        self.move = move
        self.win = 0
        self.games = 0
        self.children = None
        self.game_state = game_state
        self.winner = winning

    def set_children(self, children):
        self.children = children

    def get_uct(self):
        if self.games == 0:
            return None
        return (self.win / self.games) + np.sqrt(2 * np.log(self.parent.games) / self.games)

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

        games = [child.win / child.games if child.games > 0 else 0 for child in self.children]
        best_child = self.children[np.argmax(games)]
        return best_child, best_child.move

    def get_children_with_move(self, move):
        if self.children is None:
            return None
        for child in self.children:
            if child.move == move:
                return child

        raise Exception('Not existing child')
