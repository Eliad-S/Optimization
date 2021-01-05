# ===============================================================================
# Imports
# ===============================================================================
import copy

import abstract
from utils import MiniMaxWithAlphaBetaPruning, INFINITY, run_with_limited_time, ExceededTimeError, count_sequence
from connect_4.consts import OPPONENT_COLOR
import time
from collections import defaultdict


# ===============================================================================
# Player
# ===============================================================================

class Player(abstract.AbstractPlayer):
    def __init__(self, setup_time, player_color, time_per_turn):
        abstract.AbstractPlayer.__init__(self, setup_time, player_color, time_per_turn)
        self.clock = time.process_time()
        self.time_remaining_in_turn = self.time_per_turn
        self.max_depth = 8
        # We are simply providing (remaining time / remaining turns) for each turn in round.
        # Taking a spare time of 0.05 seconds.

    def get_move(self, game_state, possible_moves):
        game_state = copy.deepcopy(game_state)
        self.time_remaining_in_turn = self.time_per_turn - 0.05
        self.clock = time.process_time()
        if len(possible_moves) == 1:
            return possible_moves[0]

        current_depth = 1
        prev_alpha = -INFINITY

        # Choosing an arbitrary move in case Minimax does not return an answer:
        best_move = possible_moves[0]

        # Initialize Minimax algorithm, still not running anything
        minimax = MiniMaxWithAlphaBetaPruning(self.utility, self.color, self.no_more_time)

        # Iterative deepening until the time runs out.
        while True:
            print('going to depth: {}, remaining time: {}, prev_alpha: {}, best_move: {}'.format(
                current_depth,
                self.time_remaining_in_turn
                - (time.process_time() - self.clock),
                prev_alpha,
                best_move))

            try:
                (alpha, move), run_time = run_with_limited_time(
                    minimax.search, (game_state, current_depth, -INFINITY, INFINITY, True), {},
                    self.time_remaining_in_turn - (time.process_time() - self.clock))
            except (ExceededTimeError, MemoryError):
                print('no more time, achieved depth {}'.format(current_depth))
                break

            if self.no_more_time():
                print('no more time')
                break

            prev_alpha = alpha
            best_move = move

            if alpha == INFINITY:
                print('the move: {} will guarantee victory.'.format(best_move))
                break

            if alpha == -INFINITY:
                print('all is lost')
                break

            current_depth += 1

        return best_move

    def utility(self, game_state):
        """ A utility fucntion to evaluate the state of the board and report it to the calling function,
            utility value is defined as the  score of the player who calles the function - score of opponent player,
            The score of any player is the sum of each sequence found for this player scalled by large factor for
            sequences with higher lengths.
        """
        player = game_state.curr_player
        opponent = OPPONENT_COLOR[player]
        board = game_state.board
        player_fours = count_sequence(board, player, 4)
        player_threes = count_sequence(board, player, 3)
        player_twos = count_sequence(board, player, 2)
        player_score = player_threes * 999 + player_twos * 9

        opponent_fours = count_sequence(board, opponent, 4)
        opponent_threes = count_sequence(board, opponent, 3)
        opponent_twos = count_sequence(board, opponent, 2)
        opponent_score = opponent_threes * 999 + opponent_twos * 9

        if opponent_fours > 0:
            # This means that the current player lost the game
            # So return the biggest negative value => -infinity
            return -INFINITY
        elif player_fours > 0:
            return INFINITY
        else:
            # Return the playerScore minus the opponentScore
            return player_score - opponent_score

    def no_more_time(self):
        return (time.process_time() - self.clock) >= self.time_remaining_in_turn

    def __repr__(self):
        return "MinMax"

# c:\python35\python.exe run_game.py 3 3 3 y simple_player random_player
