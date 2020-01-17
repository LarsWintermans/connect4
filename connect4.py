import numpy as np
import pygame
import math
import sys
import random

ROW_COUNT = 6
COLUMN_COUNT = 7

PLAYER = 0
AI = 1

EMPTY = 0
PLAYER_PIECE = 1
AI_PIECE = 2

WINDOW_LENGTH = 4

def create_board():
    board = np.zeros((ROW_COUNT, COLUMN_COUNT))
    arduinoBoard = [board]
    return board


def insert_piece(board, row, col, piece):
    board[row][col] = piece


def is_move_valid(board, col):  # checks if move is valid, so if the last row (5) of the column is 0
    return board[ROW_COUNT - 1][col] == 0


def get_next_open_row(board, col):  # checks what the next open row is
    for r in range(ROW_COUNT):
        if board[r][col] == 0:
            return r


def print_board(board):
    print(np.flip(board, 0))  # changes the array so the bottom row is actually at the bottom


def winning_move(board, piece):
    # Check horizontal locations
    for c in range(COLUMN_COUNT - 3):  # we subtract 3 because the last 3 columns cant be starting the winning move
        for r in range(ROW_COUNT):
            if board[r][c] == piece and board[r][c + 1] == piece and board[r][c + 2] == piece and board[r][c + 3] == piece:
                return True

    # Check vertical locations
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - 3):
            if board[r][c] == piece and board[r + 1][c] == piece and board[r + 2][c] == piece and board[r + 3][c] == piece:
                return True

    # Check for positively sloped diags
    for c in range(COLUMN_COUNT - 3):
        for r in range(ROW_COUNT - 3):
            if board[r][c] == piece and board[r + 1][c+1] == piece and board[r + 2][c+2] == piece and board[r + 3][c+3] == piece:
                return True

    # Check for negatively sloped diags
    for c in range(COLUMN_COUNT - 3):
        for r in range(3, ROW_COUNT):
            if board[r][c] == piece and board[r - 1][c+1] == piece and board[r - 2][c+2] == piece and board[r - 3][c+3] == piece:
                return True

def evaluate_window(window, piece):
    score = 0
    opp_piece = PLAYER_PIECE
    if piece == PLAYER_PIECE:
        opp_piece = AI_PIECE

    if window.count(piece) >= 4:
        score += 100
    elif window.count(piece) == 3 and window.count(EMPTY) ==1:
        score += 10
    elif window.count(piece) == 2 and window.count(EMPTY) == 2:
        score += 5

    if window.count(opp_piece) ==3 and window.count(EMPTY) == 1:
        score -= 80

    return score

def score_position(board, piece):
    score = 0

    # Score center column
    center_array = [int(i) for i in list(board[:, COLUMN_COUNT//2])] #floor devision gets the middle column
    center_count = center_array.count(piece)
    score += center_count * 6

    # Score Horizontal
    for r in range(ROW_COUNT):
        row_array = [int(i) for i in list(board[r,:])]
        for c in range(COLUMN_COUNT-3):
            window = row_array[c:c+WINDOW_LENGTH] # Window refers to the window in which can be won
            score += evaluate_window(window, piece)

    # Score vertical
    for c in range(COLUMN_COUNT):
        col_array = [int(i) for i in list(board[:, c])]
        for r in range(ROW_COUNT-3):
            window = col_array[r:r+WINDOW_LENGTH]
            score += evaluate_window(window, piece)

    # Score positive diag
    for r in range(ROW_COUNT-3):
        for c in range(COLUMN_COUNT-3):
            window = [board[r+i][c+i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    # Score negative diag
    for r in range(ROW_COUNT-3):
        for c in range(COLUMN_COUNT-3):
            window = [board[r+3-1][c+i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    return score

def is_terminal_node(board):
    return winning_move(board, PLAYER_PIECE) or winning_move(board, AI_PIECE) or len(get_valid_locations(board)) == 0


def minimax(board, depth, maximizingPlayer):
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)
    if depth == 0 or is_terminal:
        if winning_move(board, AI_PIECE):
            if is_terminal:
                return 100000
            elif winning_move(board, PLAYER_PIECE):
                return -100000
            else: #Game is over, no more valid moves
                return 0
        else: #Depth is 0
            return score_position(board, AI_PIECE)

    if maximizingPlayer:
        value = -math.inf
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            insert_piece(b_copy, row, col, AI_PIECE)
            new_score = max(value, minimax(b_copy, depth-1, False))
            return new_score

    else: #Minimizing player
        value = math.inf
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            insert_piece(b_copy, row, col, PLAYER_PIECE)
            new_score = min(value, minimax(b_copy, depth - 1, True))
        pass

def get_valid_locations(board): # gives a list of where we can drop
    valid_locations = []
    for col in range(COLUMN_COUNT):
        if is_move_valid(board, col):
            valid_locations.append(col)

    return valid_locations

def pick_best_move(board, piece):
    valid_locations = get_valid_locations(board)
    best_score = 0
    best_col = random.choice(valid_locations)
    for col in valid_locations:
        row = get_next_open_row(board, col)
        temp_board = board.copy() # copy because otherwise it points to the same location
        insert_piece(temp_board, row, col, piece)
        score = score_position(temp_board, piece)
        if score > best_score: #if the score found is higher than current best score, update best score and mark this column as best column
            best_score = score
            best_col = col

    return best_col



board = create_board()
print_board(board)
game_over = False

turn = random.randint(PLAYER, AI)


while not game_over:

    # Ask for Player 1 Input
    if turn == PLAYER and not game_over:
        col = int(input("Player 1 Make your Selection (0-6):"))


        if is_move_valid(board, col):
            row = get_next_open_row(board, col)
            insert_piece(board, row, col, PLAYER_PIECE)

            if winning_move(board, PLAYER_PIECE):
                print("Player 1 wins!")
                game_over = True

            turn += 1
            turn = turn % 2


    # Ask for Player 2 Input
    elif turn == AI and not game_over:

        col = pick_best_move(board, AI_PIECE)

        if is_move_valid(board, col):
            pygame.time.wait(500) # Delay for better UX - MAYBE REMOVE IF BETTER ALGORITHM IS IMPLEMENTED
            row = get_next_open_row(board, col)
            insert_piece(board, row, col, AI_PIECE)

            if winning_move(board, AI_PIECE):
                print("Player 2 wins!")
                game_over = True

            turn += 1
            turn = turn % 2

    print_board(board)
