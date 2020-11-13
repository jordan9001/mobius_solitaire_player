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
    print("---------+-" + "--" * len(board))
    while True:
        printed = False
        s = " "
        x,y = " ", "  "
        b = [" "] * len(board)
        if i < len(stack):
            s = stack[i][0]
            x = str(stack[i][3][0])
            y = str(stack[i][3][1]).zfill(2)
            
            printed = True
        for bi in range(len(board)):
            if i < len(board[bi]):
                b[bi] = board[bi][i][0]
                printed = True
        
        print(f"{s} @ {x} {y} | " + " ".join(b))

        if not printed:
            break

        i += 1
    print("---------+-" + "--" * len(board))

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


import ctypes
import PIL.ImageGrab
import PIL.Image
import pytesseract
import string

user32 = ctypes.windll.LoadLibrary("user32.dll")
tmppath = "./tmp.png"

def getprogrec():
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
    return pos

def getcardpos(rect, x, y):
    l, t, r, b = rect
    w = r-l
    h = b-t
    left = int(w*0.439)
    xstep = w * 0.142
    top = int(h*0.1)
    ystep = h * 0.049

    xp = l + left + int(xstep * x)
    yp = t + top + int(ystep * y)

    return (xp, yp)

def getboard_fromscreen():
    pos = getprogrec()
    if pos is None:
        return None
    print(pos)

    # screen cap
    screenshot = PIL.ImageGrab.grab(pos)
    w,h = screenshot.size

    xs = int(w * 0.011)
    ys = int(h * 0.024)

    okay = string.ascii_letters + string.digits
    board = []
    for xi in range(4):
        board.append([])
        for yi in range(13):
            w,h = screenshot.size
            x,y = getcardpos((0, 0, w, h), xi, yi)
            s = screenshot.crop((x-xs, y-ys, x+xs, y+ys))
            
            s = s.getchannel("G")

            s.save(tmppath)
            #input("->")
            #s.show()
            c = pytesseract.image_to_string(tmppath, config='--psm 10')
            c = ''.join([x for x in c if x in okay])
            c = c.lower()

            #print(c)
            board[xi].append(c)
    
    # translate failures and sanity check every card is there
    # try to translate common failures
    # if it has a 0, it is probably 10
    # if it is i, it is probably 7?
    missing = cards * 4
    fixed = []
    for xi in range(len(board)):
        for yi in range(len(board[xi])):
            c = board[xi][yi].upper()
            if len(c) > 1:
                if "10" in c:
                    c = "X"
                elif c.startswith("1") and c[1] in cards:
                    c = c[1]
                    fixed.append((xi,yi))
                else:
                    c = c[0]
                    fixed.append((xi,yi))
            else:
                if c == "1" or c == "i":
                    print(f"{c} @ {xi} {yi} is 7?")
                    c = "7"
                    fixed.append((xi,yi))
                if c == "0":
                    c = "Q"
            
            board[xi][yi] = c

            i = missing.find(c)
            if i == -1:
                # uh oh
                print(f"Too many {c}")
            else:
                missing = missing[:i] + missing[i+1:]

    boarderr = False

    if len(set(missing)) > 1 or len(fixed) < len(missing):
        print(f"Too many missing cards: {missing}. Saw as:")
        boarderr = True
    elif len(fixed) == len(missing):
        for x,y in fixed:
            if board[x][y] != missing[0]:
                print(f"Misguessed {board[x][y]}? Resetting as {missing[0]}")
                board[x][y] = missing[0]
    elif len(missing) > 0:
        print(f"Too many missing cards: {missing}")
        boarderr = True

    if not boarderr:
        missing = cards * 4
        for xi in range(len(board)):
            for yi in range(len(board[xi])):
                c = board[xi][yi].upper()

                i = missing.find(c)
                if i == -1:
                    # uh oh
                    print(f"On check found too many {c}")
                    boarderr = True
                    break
                else:
                    missing = missing[:i] + missing[i+1:]

        if len(missing) > 0:
            print(f"Missing on check {missing}")
            boarderr = True

    if boarderr:
        print("Got error for board seen as:")
        for yi in range(len(board[0])):
            out = ""
            for xi in range(len(board)):
                out += board[xi][yi] + " "
            print(out)
        return None

    realboard = []
    for xi in range(len(board)):
        realboard.append([])
        for yi in range(len(board[xi])):
            realboard[xi].append(getcard(board[xi][yi]))
    return realboard

import subprocess
dumpcardspath = "./dumpcards/bin/Release/netcoreapp3.1/dumpcards.exe"
def getboard_clrmd():
    p = subprocess.run([dumpcardspath], capture_output=True, encoding="ascii")
    if len(p.stdout) == 0:
        print("Error getting cards: \n" + p.stderr)
        return None
    b = []
    for x in range(4):
        b.append([])
        for y in range(13):
            b[x].append(None)

    for l in p.stdout.strip().split('\n'):
        ll = l.split()
        print(ll)
        c = cards[int(ll[0]) - 1]
        card = getcard(c)
        x = int(ll[1])
        y = int(ll[2])
        b[x][y] = card

    for x in range(4):
        for y in range(13):
            if b[x][y] is None:
                print("Didn't get all the cards")
                return None
    return b

import win32api
import win32con
import time
def clickat(xp, yp):
    print(f"Want to click at {xp},{yp}")
    win32api.SetCursorPos((xp, yp))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, xp, yp)
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, xp, yp)
    time.sleep(0.5)

def clicknextstack(rect):
    raise NotImplementedError("Need to find button, it moves")
    w = rect[2] - rect[0]
    h = rect[3] - rect[1]
    clickat(rect[0] + int(w *0.317), rect[1] + int(h * 0.74))

def playstack(positions, rect):
    for x,y in positions:
        xp, yp = getcardpos(rect, x, y)
        clickat(xp, yp)

def playone():
    rect = getprogrec()
    #focus window
    clickat(rect[0] + 6, rect[1] + 6)
    board = getboard_clrmd()
    if board is None:
        print("Failed while getting board")
        return False
    stack = []
    printstate(board, stack)

    while True:
        _, winstack, nextboard = bruteforce(board, stack)
        printstate(nextboard, winstack)
        playstack([x[3] for x in winstack], rect)
        clicknextstack(rect)
        if nextboard == board:
            break
        board = nextboard
        stack = []
    return True

def main():
    playone()

if __name__ == "__main__":
    main()