
from collections import defaultdict

from checkers.consts import OPPONENT_COLOR, MAX_TURNS_NO_JUMP, MY_COLORS, OPPONENT_COLORS
from players import simple_player
from utils import INFINITY


class Player(simple_player.Player):
    def _init_(self, setup_time, player_color, time_per_k_turns, k):
        super()._init_(setup_time, player_color, time_per_k_turns, k)

    def _repr_(self):
        return '{} {}'.format(simple_player.Player._repr_(self), 'better_h')

    def numDefendingNeighbors(self, state, i, j, player):
        n = 0
        if player == 1:
            p, k = MY_COLORS[self.color][0], MY_COLORS[self.color][1]
        else:
            p, k = OPPONENT_COLORS[self.color][0], OPPONENT_COLORS[self.color][1]
        if i + 1 < 8 and j + 1 < 8:
            if state.board[(i + 1, j + 1)] == p or state.board[(i + 1, j + 1)] == k:
                n += 1
        if i + 1 < 8 and j - 1 >= 0:
            if state.board[(i + 1, j - 1)] == p or state.board[(i + 1, j - 1)] == k:
                n += 1
        if i - 1 >= 0 and j + 1 < 8:
            if state.board[(i - 1, j + 1)] == p or state.board[(i - 1, j + 1)] == k:
                n += 1
        if i - 1 >= 0 and j - 1 >= 0:
            if state.board[(i - 1, j - 1)] == p or state.board[(i - 1, j - 1)] == k:
                n += 1
        return n

    def utility(self, state):
        if len(state.get_possible_moves()) == 0:
            return INFINITY if state.curr_player != self.color else -INFINITY
        if state.turns_since_last_jump >= MAX_TURNS_NO_JUMP:
            return 0

        board_Val = 0
        for key, loc_val in state.board.items():
            i, j = key[0], key[1]
            if loc_val == OPPONENT_COLORS[self.color][0]:
                board_Val -= (3 + ((7 - i) * 0.5) + self.numDefendingNeighbors(state, key[0], key[1], 0))
                if j == 0 or j == 7:
                    board_Val -= 1
                if i == 7:
                    board_Val -= 2
            elif loc_val == OPPONENT_COLORS[self.color][1]:
                board_Val -= (5 + self.numDefendingNeighbors(state, key[0], key[1], 0))
                if j == 0 or j == 7:
                    board_Val -= 1
                if i == 7:
                    board_Val -= 2
            elif loc_val == MY_COLORS[self.color][0]:
                board_Val += (3 + (i * 0.5) + self.numDefendingNeighbors(state, key[0], key[1], 1))
                if j == 0 or j == 7:
                    board_Val += 1
                if i == 0:
                    board_Val += 2
            elif loc_val == MY_COLORS[self.color][1]:
                board_Val += 5 + self.numDefendingNeighbors(state, key[0], key[1], 1)
                if j == 0 or j == 7:
                    board_Val += 1
                if i == 0:
                    board_Val += 2
        return board_Val