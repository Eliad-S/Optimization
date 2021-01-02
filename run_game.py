""""
A generic turn-based game runner.
"""
import sys

import players.interactive_player
from connect_4.board import GameState
from connect_4.consts import RED_PLAYER, BLACK_PLAYER, TIE, PLAYER_NAME, OPPONENT_COLOR
import utils
import copy


class GameRunner:
    def __init__(self, setup_time, time_per_turn, red_player, black_player):
        """Game runner initialization.

        :param setup_time: Setup time allowed for each player in seconds.
        :param time_per_turn: Time allowed per k moves in seconds.
            The interactive player always gets infinite time to decide, no matter what.
        :param red_player: The name of the module containing the red player. E.g. "myplayer" will invoke an
            equivalent to "import players.myplayer" in the code.
        :param black_player: Same as 'red_player' parameter, but for the black one.
        """

        self.setup_time = float(setup_time)
        self.time_per_turn = float(time_per_turn)
        self.players = {}

        # Dynamically importing the players. This allows maximum flexibility and modularity.
        self.red_player = 'players.{}'.format(red_player)
        self.black_player = 'players.{}'.format(black_player)
        __import__(self.red_player)
        __import__(self.black_player)
        red_is_interactive = sys.modules[self.red_player].Player == players.interactive_player.Player
        black_is_interactive = sys.modules[self.black_player].Player == players.interactive_player.Player

        self.player_move_times = {
            RED_PLAYER: utils.INFINITY if red_is_interactive else self.time_per_turn,
            BLACK_PLAYER: utils.INFINITY if black_is_interactive else self.time_per_turn
        }

    def setup_player(self, player_class, player_color):
        """ An auxiliary function to populate the players list, and measure setup times on the go.

        :param player_class: The player class that should be initialized, measured and put into the list.
        :param player_color: Player color, passed as an argument to the player.
        :return: A boolean. True if the player exceeded the given time. False otherwise.
        """
        try:
            player, measured_time = utils.run_with_limited_time(
                player_class, (self.setup_time, player_color, self.player_move_times[player_color]), {}, self.setup_time * 1.5)
        except MemoryError:
            return True

        self.players[player_color] = player
        return measured_time > self.setup_time

    def run(self):
        """The main loop.
        :return: The winner.
        """
        # Setup each player 
        self.setup_player(sys.modules[self.red_player].Player, RED_PLAYER)
        self.setup_player(sys.modules[self.black_player].Player, BLACK_PLAYER)
        winner = None
        board_state = GameState()

        # Running the actual game loop. The game ends if someone is left out of moves,
        # or exceeds his time.
        counter = 1
        while True:
            board_state.draw_board()

            player = self.players[board_state.curr_player]
            possible_moves = board_state.get_possible_moves()
            # Tie
            if not possible_moves:
                winner = TIE
                break
            # Get move from player
            move = utils.run_with_limited_time(
                player.get_move, (board_state, possible_moves), {}, time_limit=player.time_per_turn * 1.5)

            print(repr(player) + " " + PLAYER_NAME[board_state.curr_player] + ' performed the move: ' + str(move))

            board_state, possible_winner = board_state.perform_move(move)


            if possible_winner != 0:
                board_state.draw_board()
                winner = possible_winner
                break
            print(f'turn number {counter}')
            counter += 1

        self.end_game(winner)
        return winner

    @staticmethod
    def end_game(winner):
        if winner == TIE:
            print('The game ended in a tie!')
        else:
            print('The winner is {}'.format(PLAYER_NAME[winner]))


if __name__ == '__main__':
    try:
        GameRunner(*sys.argv[1:]).run()
    except TypeError:
        print("""Syntax: {0} setup_time time_per_turn verbose red_player black_player
For example: {0} 2 10 interactive random_player
Please read the docs in the code for more info.""".
              format(sys.argv[0]))
