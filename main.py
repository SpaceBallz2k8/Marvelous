import cv2
import random
import images
import cv2 as cv
from ppadb.client import Client
import configparser
import time
import colour
import numpy as np
import pixels
from multiprocessing.pool import Pool




# set some defaults
adbHost = ""
adbPort = 0
adbName = ""
# The following values are the X,Y resolution of your original image you took your snips from eg 1920x1080
needleX = int(1920)
needleY = int(1080)

# First load main config
print(colour.bcolors.HEADER + 'Starting Up......')
try:
    theConfig = configparser.ConfigParser()
    theConfig.read('settings.ini')
    adbHost = theConfig.get('adb', 'host')
    adbPort = theConfig.getint('adb', 'port')
    adbName = theConfig.get('adb', 'mumu')  # Change this to your emulator
    whichBlitz = theConfig.getint('user', 'blitz')
    blitzRotations = theConfig.getint('user', 'blitzRotations')
except (RuntimeError, TypeError, NameError):
    quit(colour.bcolors.FAIL + 'Cannot load settings')


if adbHost and adbPort and adbName:
    adb = Client(host=adbHost, port=adbPort)
    device = adb.device(adbName)
    if device:
        print(colour.bcolors.OKGREEN + 'Connected to emulator')
    else:
        quit(colour.bcolors.FAIL + 'Critical Error - Cannot connect to emulator')
else:
    quit(colour.bcolors.FAIL + 'Critical Error - A config item is empty')

res = device.shell(f'wm size')
deviceSize = ''.join([i for i in res if i in '0123456789x']).split('x')
dpi = device.shell(f'wm density')
deviceDpi = ''.join([i for i in dpi if i in '0123456789'])
print(colour.bcolors.OKCYAN + 'Device Resolution - ' + str(deviceSize))
print(colour.bcolors.OKCYAN + 'Device DPI - ' + str(deviceDpi))


def getScreen():
    sGrab = device.screencap()
    with open("./screen.png", "wb") as fp:
        fp.write(sGrab)
    screenshot = cv.imread('./screen.png', cv.IMREAD_COLOR)
    #screenshot = cv2.imdecode(np.asarray(sGrab, dtype=np.uint8), cv2.IMREAD_COLOR)

    return screenshot


def screenie():
    raw = device.screencap()
    screenshot = cv2.imdecode(np.asarray(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    cv2.imshow('screenie', screenshot)
    cv2.waitKey()




def isNeedleInHaystack(screenshot, theNeedle):
    global needleX, needleY
    the_image = cv.imread(theNeedle, cv.IMREAD_COLOR)
    haystack_resolution = (screenshot.shape[1], screenshot.shape[0])
    scale_x = haystack_resolution[0] / needleX
    scale_y = haystack_resolution[1] / needleY
    scale = min(scale_x, scale_y)
    resized_image = cv.resize(the_image, None, fx=scale, fy=scale)
    matched = cv.matchTemplate(screenshot, resized_image, cv.TM_SQDIFF_NORMED)
    threshold = 0.17
    locations = np.where(matched <= threshold)
    locations = list(zip(*locations[::-1]))
    if locations:
        cogW = resized_image.shape[1]
        cogH = resized_image.shape[0]
        whereX = int(locations[0][0] + (cogW / 2))
        whereY = int(locations[0][1] + (cogH / 2))
        clickLocation = [whereX, whereY]
        return clickLocation  # return coords
    else:
        return False  # cant find it


def errorChecker(screen):
    eImages = [images.dailyStreakPopup, images.convShardsPopup, images.bigOfferClose]

    # Create a list of arguments for isNeedleInHaystack
    args_list = [(screen, needle_image) for needle_image in eImages]

    with Pool() as pool:
        results = pool.map(isNeedleInHaystack, args_list)

    for i, result in enumerate(results):
        print(f'Got result for image {i + 1}: {result}', flush=True)


def tapThis(location):  # tap a screen location - requires a list input [x,y]
    device.shell(f'input tap ' + str(location[0]) + ' ' + str(location[1]))
    time.sleep(1)

def goLeft():  # swipe left
    device.shell(f'input swipe 500 500 700 500 300')
    time.sleep(1)


def goRight():  # swipe right
    device.shell(f'input swipe 700 500 500 500 300')
    time.sleep(1)


def fullRight():  # swipe right fast
    i = 1
    while i < 18:
        device.shell(f'input swipe 700 500 500 500 100')
        i += 1
    time.sleep(1)


def fullLeft():  # swipe right fast
    i = 1
    while i < 18:
        device.shell(f'input swipe 500 500 700 500 100')
        i += 1
    time.sleep(1)


def goUp():  # swipe up - do not alter speeds or y coords - set for orb scrolling
    device.shell(f'input swipe 1165 775 1165 1275 1500')
    time.sleep(1)


def goDown():  # swipe down - do not alter speeds or y coords - set for orb scrolling
    device.shell(f'input swipe 1165 775 1165 275 1500')
    time.sleep(1)

def msfRunning():
    thePID = device.shell(f'pidof com.foxnextgames.m3')
    if thePID:
        print('Game Running')
    else:
        print('Game Not Running!!!!')
        startMSF()


def killMSF():  # force kill the game
    print('Stopping MSF')
    device.shell(f'am force-stop com.foxnextgames.m3')
    time.sleep(1)


def getPixColour(img, location):  # img is screenshot / location is list of x,y - returns list of r,g,b
    b, g, r = img[int(location[1]), int(location[0])]
    return [r, g, b]


def checkPixel(img, data):  #  img is screenshot / data is a list of x, y, r, g, b - returns true/false
    if getPixColour(img, [data[0], data[1]]) == [int(data[2]), int(data[3]), int(data[4])]:
        return True
    else:
        return False


def waitForButton(button):
    while 1:
        img = getScreen()
        if checkPixel(img, button):
            break


def waitForImage(theImage):
    while 1:
        screenie = getScreen()
        checked = isNeedleInHaystack(screenie, theImage)
        if checked:
            return checked


def startMSF():  # Start the game and watch the loading bar wait 10 seconds when we pass 90%
    print('Starting MSF - Please Wait')
    device.shell(f'am start -n com.foxnextgames.m3/com.explodingbarrel.Activity')
    bar = int(0)
    for ten in pixels.loadingbar:
        waitForButton(ten)
        bar += 10
        print(str(bar) + '% Loaded')
    time.sleep(10)


def navToBlitz():
    swipes = int(0)
    while 1:
        screenshot = getScreen()
        theButton = isNeedleInHaystack(screenshot, images.blitzMainMenu)
        if theButton:
            print(colour.bcolors.OKBLUE + 'Starting Blitz Loop')
            tapThis(theButton)
            break
        elif not theButton and swipes < 15:
            goRight()
            swipes += 1
        elif not theButton and swipes >= 15:
            goLeft()
            swipes += 1

def goHome():
    time.sleep(1)  # Wait, we might get a popup
    theScreen = getScreen()
    clickThis = isNeedleInHaystack(theScreen, images.home)
    if not clickThis:  # Were not home
        homeClick = isNeedleInHaystack(theScreen, images.homeButtonRedDot)  # Check for home button
        if homeClick:
            tapThis(homeClick)
            goHome()
        popClose = isNeedleInHaystack(theScreen, images.bigOfferClose)  # Check for an X (Popups)
        if popClose:
            tapThis(popClose)
            goHome()
        shardClaim = isNeedleInHaystack(theScreen, images.convShardsPopup)  # Claim Shards (Store)
        if shardClaim:
            theButton = isNeedleInHaystack(theScreen, images.claimShardsButton)
            if theButton:
                tapThis(theButton)
                goHome()
    else:
        print(colour.bcolors.OKGREEN + 'Were Home')
        return True


def blitzDecide():
    screenshot = getScreen()
    if isNeedleInHaystack(screenshot, images.blitzOne):  # Make sure were on the right page
        myBlitz = whichBlitz
        if checkPixel(screenshot, pixels.blitzGoOne):
            blitzOne = True
            print(colour.bcolors.OKBLUE + 'Blitz One Active')
        else:
            blitzOne = False
        if checkPixel(screenshot, pixels.blitzGoTwo):
            blitzTwo = True
            print(colour.bcolors.OKBLUE + 'Blitz Two Active')
        else:
            blitzTwo = False
        if checkPixel(screenshot, pixels.blitzGoThree):
            blitzThree = True
            print(colour.bcolors.OKBLUE + 'Blitz Three Active')
        else:
            blitzThree = False
        if myBlitz == 1 and blitzOne:
            print(colour.bcolors.OKBLUE + 'Selecting Blitz One')
            tapThis([pixels.blitzGoOne[0], pixels.blitzGoOne[1]])
        elif myBlitz == 2 and blitzTwo:
            print(colour.bcolors.OKBLUE + 'Selecting Blitz Two')
            tapThis([pixels.blitzGoTwo[0], pixels.blitzGoTwo[1]])
        elif myBlitz == 3 and blitzThree:
            print(colour.bcolors.OKBLUE + 'Selecting Blitz Three')
            tapThis([pixels.blitzGoThree[0], pixels.blitzGoThree[1]])
        else:
            print(colour.bcolors.OKBLUE + 'Selecting Blitz One')
            tapThis([pixels.blitzGoOne[0], pixels.blitzGoOne[1]])
        screenshot = getScreen()
        if isNeedleInHaystack(screenshot, images.blitzTwo):  # check we made it to blitz step 2
            print(colour.bcolors.OKBLUE + 'Blitz Decision Complete')
        else:
            blitzDecide()  # We shouldn't need this but just in case try again


def enableBlitzSim():
    time.sleep(1)
    theScreen = getScreen()
    if getPixColour(theScreen, [pixels.blitzSim[0], pixels.blitzSim[1]])[0] > 200:
        print('Blitz Sim Already Enabled')
    else:
        print('Enabling Blitz Sim')
        tapThis([pixels.blitzSim[0], pixels.blitzSim[1]])


def dangerCheck(theScreen):
    if checkPixel(theScreen, pixels.blitzDanger):
        return True
    else:
        return False


def blitzBattleLoop():
    #global blitzLoops, blitzWin, blitzLoss

    turn = int(1)
    print('Trying ' + str(blitzRotations) + ' blitz battles')
    while turn <= blitzRotations:
        screenshot = getScreen()
        if checkPixel(screenshot, pixels.blitzBattleFree):  # Blitz is free
            opponent = int(1)
            while opponent <= 3:
                if not dangerCheck(screenshot):  # non dangerous opponent
                    waitForButton(pixels.blitzBattleFree)
                    tapThis([pixels.blitzBattleFree[0], pixels.blitzBattleFree[1]])
                    turn += 1
                    break
                else:  # dangerous opponent
                    waitForButton(pixels.blitzNewOppo)
                    tapThis([pixels.blitzNewOppo[0], pixels.blitzNewOppo[1]])
                    screenshot = getScreen()
                    opponent += 1
                if opponent == 3:
                    waitForButton(pixels.blitzBattleFree)
                    tapThis([pixels.blitzBattleFree[0], pixels.blitzBattleFree[1]])
                    turn += 1
                    break
            while 1:
                end = getScreen()
                if checkPixel(end, pixels.blitzContinueButton):
                    #if checkPixel(end, pixels.blitzWin):
                        #blitzWin += 1
                        #statsConfig.set('stats', 'blitzWin', str(blitzWin))
                        #with open('stats.ini', 'w') as statsFile:
                            #statsConfig.write(statsFile)
                    #else:
                        #blitzLoss += 1
                        #statsConfig.set('stats', 'blitzLoss', str(blitzLoss))
                        #with open('stats.ini', 'w') as statsFile:
                        #    statsConfig.write(statsFile)
                    tapThis([pixels.blitzContinueButton[0], pixels.blitzContinueButton[1]])
                    break
        else:  # not free - need to cycle squad
            tapThis([pixels.blitzChangeRight[0], pixels.blitzChangeRight[1]])
            time.sleep(1)
            tapThis([pixels.blitzNewOppo[0], pixels.blitzNewOppo[1]])
            turn += 1
    #print('Current Blitz Totals - ' + str(blitzWin) + ' Wins / ' + str(blitzLoss) + ' Losses')
    goHome()


def navToArena():
    swipes = int(0)
    while 1:
        screenshot = getScreen()
        theButton = isNeedleInHaystack(screenshot, images.arenaMainMenu)
        if theButton:
            print(colour.bcolors.OKBLUE + 'Starting Arena Loop')
            tapThis(theButton)
            break
        elif not theButton and swipes < 15:
            goLeft()
            swipes += 1
        elif not theButton and swipes >= 15:
            goRight()
            swipes += 1


def arenaGo():
    goButton = waitForImage(images.arenaGo)
    if goButton:
        tapThis(goButton)
    else:
        arenaGo()


def arenaDecide():
    waitForButton(pixels.arenaPageReady)
    screenshot = getScreen()
    if checkPixel(screenshot, pixels.arenaFree):
        print('Arena Turn Available')
        print('Making random choice (1-3)')
        choice = random.randint(1,3)
        print('Selected ' + str(choice))
        if choice == 1:
            theButton = pixels.arenaOne
        elif choice == 2:
            theButton = pixels.arenaTwo
        elif choice == 3:
            theButton = pixels.arenaThree
        time.sleep(1)
        tapThis([theButton[0], theButton[1]])
        startArena = waitForImage(images.arenaReady)
        tapThis(startArena)
        return True
    else:
        print('Arena Cooldown or No turns Left')
        return False

def arenaBattle():
    waitForButton(pixels.arenaMatchStarted)
    tapThis([pixels.arenaMatchStarted[0], pixels.arenaMatchStarted[1]])
    time.sleep(1)
    tapThis([pixels.arenaMatchStarted[0], pixels.arenaMatchStarted[1]])
    print("Waiting for match end...")
    theButton = waitForImage(images.arenaEnd)
    print("Sleep 3.....")
    time.sleep(3)
    tapThis(theButton)
    print("Tapped button")
    waitForButton(pixels.loadingbar[0])
    time.sleep(5)
    print("Arena Ended - going home")


def buyWarCreds():
    goHome()
    tapThis([pixels.suppliesButton[0], pixels.suppliesButton[1]])


def openSeven():
    click1 = waitForImage(images.openSevenOne)
    tapThis(click1)
    click2 = waitForImage(images.openSevenTwo)
    tapThis(click2)
    click3 = waitForImage(images.openSevenThree)
    tapThis(click3)



def openTen():
    click1 = waitForImage(images.openTen)
    tapThis(click1)
    click2 = waitForImage(images.openTenTwo)
    tapThis(click2)
    click3 = waitForImage(images.openTenThree)
    tapThis(click3)


while 1:
    #goHome()
    #navToArena()
    #arenaGo()
    #if arenaDecide():
    #    arenaBattle()
    goHome()
    navToBlitz()
    blitzDecide()
    enableBlitzSim()
    blitzBattleLoop()
    #openSeven()
    #openTen()
#msfRunning()
#goHome()
#navToArena()
#arenaGo()
#arenaDecide()
