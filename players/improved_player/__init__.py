from players import simple_player

from utils import MiniMaxWithAlphaBetaPruning, INFINITY, run_with_limited_time, ExceededTimeError
import time


class Player(simple_player.Player):
    def __init__(self, setup_time, player_color, time_per_k_turns, k):
        super().__init__(setup_time, player_color, time_per_k_turns, k)
        self.__k_times = 0

    def __repr__(self):
        return '{} {}'.format(simple_player.Player.__repr__(self), 'improved_player')

    def get_move(self, game_state, possible_moves):
        self.clock = time.process_time()

        self.time_for_current_move = (self.time_remaining_in_round / self.turns_remaining_in_round) - 0.05

        if len(possible_moves) == 1:
            if self.turns_remaining_in_round == 1:
                self.turns_remaining_in_round = self.k
                self.time_remaining_in_round = self.time_per_k_turns
            else:
                self.turns_remaining_in_round -= 1
                self.time_remaining_in_round -= (time.process_time() - self.clock)
            return possible_moves[0]
        time_per_depth = {1: 0.001, 2: 0.001, 3: 0.01, 4: 0.01, 5: 0.04, 6: 0.1, 7: 0.25, 8: 0.588}
        current_depth = 1
        prev_alpha = -INFINITY

        # Choosing an arbitrary move in case Minimax does not return an answer:
        best_move = possible_moves[0]

        # Initialize Minimax algorithm, still not running anything
        minimax = MiniMaxWithAlphaBetaPruning(self.utility, self.color, self.no_more_time,
                                              self.selective_deepening_criterion)

        # Iterative deepening until the time runs out.
        while True:
            print('going to depth: {}, remaining time: {}, prev_alpha: {}, best_move: {}'.format(
                current_depth,
                self.time_for_current_move - (time.process_time() - self.clock),
                prev_alpha,
                best_move))

            try:
                if current_depth < 8:
                    remaining = self.time_for_current_move - (time.process_time() - self.clock) * time_per_depth[
                        current_depth]
                else:
                    remaining = self.time_for_current_move - (time.process_time() - self.clock)
                (alpha, move), run_time = run_with_limited_time(
                    minimax.search, (game_state, current_depth, -INFINITY, INFINITY, True), {},
                    remaining)
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

        if self.turns_remaining_in_round == 1:
            self.turns_remaining_in_round = self.k
            self.time_remaining_in_round = self.time_per_k_turns
        else:
            self.turns_remaining_in_round -= 1
            self.time_remaining_in_round -= (time.process_time() - self.clock)
        return best_move