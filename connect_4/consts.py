# ==============================================================================
# Game pieces
# - RP\BP are pawn pieces
# - RK\BK are king pieces
# - EM is an empty location on the board.
# ==============================================================================

RED_PLAYER = 1
BLACK_PLAYER = -1
TIE = 'tie'

# ===============================================================================
# Board Shape
# ===============================================================================
BOARD_ROWS = 7
BOARD_COLS = 6

# IS_BLACK_TILE = lambda loc: (loc[0] + loc[1]) % 2 == 0

# The ID of the "back" row for each player.
PLAYER_NAME = {
    1: 'RED_PLAYER',
    -1: 'BLACK_PLAYER'
}

# The Opponent of each Player
OPPONENT_COLOR = {
    RED_PLAYER: BLACK_PLAYER,
    BLACK_PLAYER: RED_PLAYER
}
