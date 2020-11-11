import random

cards = "A23456789XJQK"
vals = list(range(1,11)) + [10,10,10]
order = list(range(len(cards)))

def getcard(c):
    i = cards.find(c)
    if i == -1:
        raise ValueError(f"Invalid Card: {c}")

    return((cards[i], vals[i], order[i]))

def stackstr(s):
    stack = []
    for c in s:
        stack.append(getcard(c))
    return stack

def deal():
    deck = list(zip(list(cards), vals, order)) * 4
    random.shuffle(deck)
    board = [deck[i:i+13] for i in range(0,52,13)]
    return board

def isrun(group):
    srun = sorted([x[2] for x in group])
    for i in range(1,len(srun)):
        if (srun[i-1] + 1) != srun[i]:
            return False
    return True

def score(stack):
    score = 0
    if len(stack) == 0:
        return score
    
    if stack[0][0] == "J":
        score += 2
    
    # get stack total and any sets
    total = 0
    lastcard = " "
    setlen = 0
    for c in stack:
        if lastcard == c[0]:
            setlen += 1
            score += (setlen * 2)
        else:
            setlen = 0
        lastcard = c[0]

        total += c[1]
        if total == 15:
            score += 2
        elif total == 31:
            score += 2

    # get any runs
    for l in range(7,2,-1):
        if l > len(stack):
            continue
        i = 0
        while i <= (len(stack) - l):
            if i+l > len(stack):
                break
            if isrun(stack[i:i+l]):
                score += l
                stack = stack[:i] + stack[i+l:]
            else:
                i += 1

    return score

def bruteforce(board, stack=[]):
    # just brute force for 1 stack maximum score
    total = sum([c[1] for c in stack])

    pulled = 0
    wins = -1
    winstack = []
    winboard = None
    for i in range(4):
        if len(board[i]) > 0 and (board[i][-1][1] + total) <= 31:
            newboard = []
            for ii in range(4):
                if ii == i:
                    newboard.append(board[ii][:-1])
                else:
                    newboard.append(board[ii][:])
            newstack = stack[:]
            card = board[i][-1]
            card = (card[0], card[1], card[2], (i,len(board[i])-1))
            newstack.append(card)
            s, trystack, tryboard = bruteforce(newboard, newstack)
            if s > wins or (s == wins and len(board[pulled]) < len(board[i])):
                winstack = trystack
                wins = s
                pulled = i
                winboard = tryboard
    if wins == -1:
        return (score(stack), stack, board)        
    else:
        return (wins, winstack, winboard)

def printstate(board, stack):
    i = 0
    print("---+-" + "--" * len(board))
    while True:
        printed = False
        s = " "
        x,y = " ", "  "
        b = [" "] * len(board)
        if i < len(stack):
            s = stack[i][0]
            x = str(stack[i][3][0])
            x = str(stack[i][3][1]).zfill(2)
            
            printed = True
        for bi in range(len(board)):
            if i < len(board[bi]):
                b[bi] = board[bi][i][0]
                printed = True
        
        print(f" {s} {x},{y} | " + " ".join(b))

        if not printed:
            break

        i += 1
    print("---+-" + "--" * len(board))

def playbrute(board, stack):
    printstate(board, stack)

    while True:
        score, winstack, nextboard = bruteforce(board, stack)
        printstate(nextboard, winstack)
        print(f"@{score}\n")
        if nextboard == board:
            break
        board = nextboard
        stack = []


#TODO
# to set cursor:
#   mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, x, y)
#   OR SetCursorPos((x,y)) # not the same x,y as above
# to click
#   mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y)
#   mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y)
# to get board
#   PIL.ImageGrab.grab
#   pytesseract.image_to_string(path, config='--psm 10')
import ctypes
import PIL.ImageGrab
import pytesseract

user32 = ctypes.windll.LoadLibrary("user32.dll")
tmppath = "./tmp.png"

def getBoard():
    callback = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_ulonglong, ctypes.c_ulonglong)
    buf = (ctypes.c_byte * 0x400)()

    pos = None
    def enumfunc(hwnd, param):
        user32.GetWindowTextW(hwnd, buf, len(buf)//2)
        bbuf = bytes(buf)
        end = bbuf.find(b"\0\0")
        if (end & 1) == 1:
            end += 1
        title = bbuf[:end]
        stitle = str(title, "UTF_16_LE")
        if "Möbius Front '83" != stitle:
            return True

        rect = (ctypes.c_long * 4)()
        user32.GetWindowRect(hwnd, rect)
        nonlocal pos
        pos = list(rect)
        return True
    user32.EnumWindows(callback(enumfunc), 0)

    if pos is None:
        print("Error, unable to find game coordinates")
        return None
    if min(pos) < 0:
        print("Target is offscreen")
        return None
    print(pos)

    # screen cap
    screenshot = PIL.ImageGrab.grab(pos)
    w,h = screenshot.size

    xs = int(w * 0.015)
    ys = int(h * 0.024)

    left = int(w*0.432)
    xstep = w * 0.144
    top = int(h*0.1)
    ystep = h * 0.049

    for xi in range(4):
        for yi in range(13):
            w,h = screenshot.size
            x = left + int(xstep * xi)
            y = top + int(ystep * yi)
            s = screenshot.crop((x-xs, y-ys, x+xs, y+ys))
            s.save(tmppath)
            s.show()
            input("->")
            print(pytesseract.image_to_string(tmppath, config='--psm 10'))

    #TODO here the OCR is choking on the card edges. I want to try extracting the red channel
    # and adjust the sizes, see if we can get it closer on target without edges showing up
    
    return None


#TODO use sendInput as admin to actually play the game