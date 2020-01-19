import numpy as np
import pygame
import math
import sys
import random
import serial
import tensorflow.keras
from PIL import Image, ImageOps
import cv2
import struct
import time

startMarker = '<'
endMarker = '>'
dataStarted = False
dataBuf = ""
messageComplete = False


BLUE =(0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)


ROW_COUNT = 6
COLUMN_COUNT = 7

PLAYER = 0
AI = 1

EMPTY = 0
PLAYER_PIECE = 1
AI_PIECE = 2

WINDOW_LENGTH = 4

# Disable scientific notation for clarity
np.set_printoptions(suppress=True)

# Loading the Keras model
model = tensorflow.keras.models.load_model('keras_playingcards.h5')
video = cv2.VideoCapture(0)


def setupSerial(baudRate, serialPortName):
    global serialPort

    serialPort = serial.Serial(port=serialPortName, baudrate=baudRate, timeout=0, rtscts=True)

    print("Serial port " + serialPortName + " opened  Baudrate " + str(baudRate))

    waitForArduino()

def sendToArduino(stringToSend):
    # this adds the start- and end-markers before sending
    global startMarker, endMarker, serialPort

    stringWithMarkers = (startMarker)
    stringWithMarkers += stringToSend
    stringWithMarkers += (endMarker)

    serialPort.write(stringWithMarkers.encode('utf-8'))  # encode needed for Python3

def recvLikeArduino():
    global startMarker, endMarker, serialPort, dataStarted, dataBuf, messageComplete

    if serialPort.inWaiting() > 0 and messageComplete == False:
        x = serialPort.read().decode("utf-8")  # decode needed for Python3

        if dataStarted == True:
            if x != endMarker:
                dataBuf = dataBuf + x
            else:
                dataStarted = False
                messageComplete = True
        elif x == startMarker:
            dataBuf = ''
            dataStarted = True

    if (messageComplete == True):
        messageComplete = False
        return dataBuf
    else:
        return "XXX"


def waitForArduino():
    # wait until the Arduino sends 'Arduino is ready' - allows time for Arduino reset
    # it also ensures that any bytes left over from a previous message are discarded

    print("Waiting for Arduino to reset")

    msg = ""
    while msg.find("Arduino is ready") == -1:
        msg = recvLikeArduino()
        if not (msg == 'XXX'):
            print(msg)


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


def minimax(board, depth, alpha, beta, maximizingPlayer):
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)
    if depth == 0 or is_terminal:
        if winning_move(board, AI_PIECE):
            if is_terminal:
                return None, 100000
            elif winning_move(board, PLAYER_PIECE):
                return None, -100000
            else: #Game is over, no more valid moves
                return None, 0
        else: #Depth is 0
            return None, score_position(board, AI_PIECE)

    if maximizingPlayer:
        value = -math.inf
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            insert_piece(b_copy, row, col, AI_PIECE)
            new_score = minimax(b_copy, depth-1, alpha, beta, False)[1]
            if new_score > value:
                value = new_score
                column = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return column, value

    else: #Minimizing player
        value = math.inf
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            insert_piece(b_copy, row, col, PLAYER_PIECE)
            new_score = minimax(b_copy, depth - 1, alpha, beta, True)[1]
            if new_score < value:
                value = new_score
                column = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return column, value


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

def flatten_board(board):
    flatboard = board.flatten()
    intboard = flatboard.astype(int)
    boardlist = str(intboard)
    boardlist = boardlist.replace(" ", "")
    boardlist = boardlist.replace("[", "")
    boardlist = boardlist.replace("]", "")
    return boardlist


def draw_board(board):
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            pygame.draw.rect(screen, BLUE, (c*SQUARESIZE, r*SQUARESIZE+SQUARESIZE, SQUARESIZE, SQUARESIZE))
            pygame.draw.circle(screen, BLACK, (int(c*SQUARESIZE+SQUARESIZE/2), int(r*SQUARESIZE+SQUARESIZE+SQUARESIZE/2)), RADIUS)

    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            if board[r][c] == 1:
                pygame.draw.circle(screen, RED, (int(c * SQUARESIZE + SQUARESIZE / 2), height-int(r * SQUARESIZE + SQUARESIZE / 2)), RADIUS)
            elif board[r][c] == 2:
                pygame.draw.circle(screen, YELLOW, (int(c * SQUARESIZE + SQUARESIZE / 2), height-int(r * SQUARESIZE + SQUARESIZE / 2)), RADIUS)
    pygame.display.update()

board = create_board()
print_board(board)
game_over = False

turn = random.randint(PLAYER, AI)

pygame.init()

SQUARESIZE = 100

width = COLUMN_COUNT * SQUARESIZE
height = (ROW_COUNT+1 )* SQUARESIZE

size = (width, height)

RADIUS = int(SQUARESIZE/2 - 5)

screen = pygame.display.set_mode(size)
draw_board(board)
pygame.display.update()

setupSerial(115200, "COM4")
count = 0
prevTime = time.time()

while not game_over:
    _, frame = video.read()

    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

    image = Image.fromarray(frame, 'RGB')

    size = (224, 224)
    image = ImageOps.fit(image, size, Image.ANTIALIAS)

    image_array = np.asarray(image)

    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1

    data[0] = normalized_image_array

    prediction = model.predict(data)


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

    #if event.type == pygame.MOUSEBUTTONDOWN:
    pygame.draw.rect(screen, BLACK, (0, 0, width, SQUARESIZE)) # Clear PyGame upper black bar

        # Ask for Player 1 Input
    if turn == PLAYER and not game_over:

        posx = 350

        if prediction.flat[0] > 0.9:
            posx = 50
        elif prediction.flat[1] > 0.9:
            posx = 150
        elif prediction.flat[2] > 0.9:
            posx = 250
        elif prediction.flat[3] > 0.9:
            posx = 350
        elif prediction.flat[4] > 0.9:
            posx = 450
        elif prediction.flat[5] > 0.9:
            posx = 550

        pygame.draw.circle(screen, RED, (posx, int(SQUARESIZE / 2)), RADIUS)
        pygame.display.update()

        if event.type == pygame.MOUSEBUTTONDOWN:

            col = int(math.floor(posx/SQUARESIZE))

            if is_move_valid(board, col):
                row = get_next_open_row(board, col)
                insert_piece(board, row, col, PLAYER_PIECE)

                if winning_move(board, PLAYER_PIECE):

                    print("Player 1 wins!")

                    game_over = True

                turn += 1
                turn = turn % 2

            print_board(board)
            draw_board(board)
            sendToArduino(str(flatten_board(board)))


        # Ask for Player 2 Input
    elif turn == AI and not game_over:


        col, minimax_score = minimax(board, 5, -math.inf, math.inf, True)

        if is_move_valid(board, col):
            row = get_next_open_row(board, col)
            insert_piece(board, row, col, AI_PIECE)

            if winning_move(board, AI_PIECE):
                print("Player 2 wins!")

                game_over = True

            turn += 1
            turn = turn % 2

        print_board(board)
        draw_board(board)
        sendToArduino(str(flatten_board(board)))


    # check for a reply
    #arduinoReply = recvLikeArduino()
    #if not (arduinoReply == 'XXX'):
        # print("Time %s  Reply %s" % (time.time(), arduinoReply))

    # send a message at intervals
    #if time.time() - prevTime > 1:

       # prevTime = time.time()
       #count += 1

