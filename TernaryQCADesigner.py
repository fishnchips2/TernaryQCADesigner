import sys
import os
import sdl2
import sdl2.ext
import sdl2.sdlttf
import networkx
import math


colours = {
    -1: "grey",
    0: "white",
    1: "red",
    2: "yellow",
    3: "green",
    4: "blue",
    }

height = 30
width = 60
boxSize = 25
heightpx = height*boxSize
widthpx = width*boxSize

horizontalScale = 30
verticalScale = 2

cellRadius = 3E-9
cellSpacing = 10E-9
diagonalDistance = math.sqrt(2)/2
simDistance = 2
temperature = 10
boltzmann = 1.38064852E-23
coulomb = 8.988E9
electronChargeSquared = (1.60217662E-19)**2
iterationsPerClock = 100
clockState = 0

cellNetwork = networkx.MultiDiGraph()
cellSprites = []
changedWhileMouseDown = []
runningWindows = []
uiElements = []

directory = os.getcwd() + '/Resources'

def createSpriteDictionary():
    sprites = (spriteFactory.from_image(directory + '/UNPOLARISED.png'),
               spriteFactory.from_image(directory + '/NS_LOCKED.png'),
               spriteFactory.from_image(directory + '/NESW_LOCKED.png'),
               spriteFactory.from_image(directory + '/EW_LOCKED.png'),
               spriteFactory.from_image(directory + '/NWSE_LOCKED.png'),
               spriteFactory.from_image(directory + '/BLANK.png'),
               spriteFactory.from_color(sdl2.ext.Color(255,0,0),(boxSize,boxSize)),
               spriteFactory.from_color(sdl2.ext.Color(0,255,0),(boxSize,boxSize)),
               spriteFactory.from_color(sdl2.ext.Color(0,0,255),(boxSize,boxSize)),
               spriteFactory.from_color(sdl2.ext.Color(255,0,255),(boxSize,boxSize)),
               spriteFactory.from_color(sdl2.ext.Color(255,255,255),(boxSize,boxSize)),
               spriteFactory.from_image(directory + '/NS.png'),
               spriteFactory.from_image(directory + '/NESW.png'),
               spriteFactory.from_image(directory + '/EW.png'),
               spriteFactory.from_image(directory + '/NWSE.png'))
    return(sprites)

def idle():
    global changedWhileMouseDown
    running = 1
    uiprocessor = sdl2.ext.UIProcessor()
    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_WINDOWEVENT:
                if event.window.event == sdl2.SDL_WINDOWEVENT_CLOSE:
                    for eventWindow in runningWindows:
                        if event.window.windowID == sdl2.SDL_GetWindowID(eventWindow.window):
                            eventWindow.close()
                            runningWindows.remove(eventWindow)
                            if len(runningWindows) == 0:
                                running = 0
                            break
            elif event.type == sdl2.SDL_MOUSEBUTTONUP and event.button.button == sdl2.SDL_BUTTON_LEFT:
                changedWhileMouseDown = []
            elif event.type == sdl2.SDL_MOUSEBUTTONDOWN or event.type == sdl2.SDL_MOUSEMOTION:
                for i in range(width):
                    for j in range(height):
                        uiprocessor.dispatch(cellSprites[i][j], event)
            uiprocessor.dispatch(uiElements, event)

def onClick(button, event):
    if button in cellNetwork:
        state = cellNetwork.nodes[button]['state']
        phase = cellNetwork.nodes[button]['phase']
        graphData = cellNetwork.nodes[button]['graphdata']
        if event.button.button == sdl2.SDL_BUTTON_RIGHT:
            if phase != -1:
                detailWindow(graphData)
        elif sdl2.SDL_GetKeyboardState(None)[sdl2.SDL_SCANCODE_LCTRL]:
            button.texture = spriteDict[10].texture
            spriteRenderer.render(button)
            if 0 in state:
                index = state.index(max(state))
                state[index] = 0
                state[(index+1)%4] = 4
            else:
                state = [4,0,0,0]
            phase = -1
            button.texture = spriteDict[state.index(max(state))+1].texture
            cellNetwork.nodes[button]['state'] = state
            cellNetwork.nodes[button]['phase'] = phase
        elif sdl2.SDL_GetKeyboardState(None)[sdl2.SDL_SCANCODE_DELETE]:
            cellNetwork.remove_node(button)
            button.texture = spriteDict[5].texture
        else:
            state = [1,1,1,1]
            if(phase == -1):
                phase = clockState
            else:
                phase = (phase+1)%4
            button.texture = spriteDict[phase+6].texture
            spriteRenderer.render(button)
            button.texture = spriteDict[0].texture
            cellNetwork.nodes[button]['state'] = state
            cellNetwork.nodes[button]['phase'] = phase
    elif not (sdl2.SDL_GetKeyboardState(None)[sdl2.SDL_SCANCODE_DELETE] or sdl2.SDL_GetKeyboardState(None)[sdl2.SDL_SCANCODE_LCTRL] or event.button.button == sdl2.SDL_BUTTON_RIGHT):
        cellNetwork.add_node(button, state=[1,1,1,1], graphdata=[], phase = clockState, newState = [1,1,1,1])
        button.texture = spriteDict[clockState+6].texture
        spriteRenderer.render(button)
        button.texture = spriteDict[0].texture
    elif sdl2.SDL_GetKeyboardState(None)[sdl2.SDL_SCANCODE_LCTRL]:
        cellNetwork.add_node(button, state=[4,0,0,0], graphdata=[], phase = -1)
        button.texture = spriteDict[10].texture
        spriteRenderer.render(button)
        button.texture = spriteDict[1].texture
    spriteRenderer.render(button)
    changedWhileMouseDown.append(button)

def onMove(button, event):
    if button not in changedWhileMouseDown and sdl2.SDL_GetMouseState(None,None)==sdl2.SDL_BUTTON(sdl2.SDL_BUTTON_LEFT):
        onClick(button, event)

def nextPhase(a,b):
    global clockState
    global clockIndicator
    clockState = (clockState+1)%4
    clockIndicator.texture = spriteDict[clockState+6].texture
    spriteRenderer.render(clockIndicator)

def UI():
    global changedWhileMouseDown
    renderer.present()
    renderBuffer = []
    for i in range(width):
        cellSpritesColumn = []
        cellSprites.append(cellSpritesColumn)
        for j in range(height):
            button = UIFactory.create_button(size=(boxSize,boxSize))
            button.position = (i*boxSize, (j+1)*boxSize)
            button.texture = spriteDict[5].texture
            renderBuffer.append(button)
            button.pressed += onClick
            button.motion += onMove
            cellSpritesColumn.append(button)
    simulateButton = UIFactory.create_button(size=(boxSize*6,boxSize))
    simulateButton.position = ((i-5)*boxSize,0)
    simulateText = spriteFactory.from_image(directory + '/SIMULATE.png')
    simulateButton.texture = simulateText.texture
    simulateButton.click += simulate
    renderBuffer.append(simulateButton)
    settingsButton = UIFactory.create_button(size=(boxSize,boxSize))
    settingsButton.position = (0,0)
    settingsIcon = spriteFactory.from_image(directory + '/SETTINGS.png')
    settingsButton.texture = settingsIcon.texture
    settingsButton.click += settingsWindow
    renderBuffer.append(settingsButton)
    global clockIndicator
    clockIndicator = UIFactory.create_button(size=(boxSize,boxSize))
    clockIndicator.position = ((i-6)*boxSize, 0)
    clockIndicator.texture = spriteDict[6].texture
    clockIndicator.pressed += nextPhase
    renderBuffer.append(clockIndicator)
    spriteRenderer.render(renderBuffer)
    uiElements.append(simulateButton)
    uiElements.append(settingsButton)
    uiElements.append(clockIndicator)

def simulate(a,b):
    global clockIndicator
    global clockState
    for runningWindow in range(len(runningWindows)):
        if runningWindow >= 1:
            runningWindows[runningWindow].close()
        
    if cellRadius*2 >= cellSpacing:
        errorWindow("Radius too large")
        return
    renderBuffer = []
    for button in cellNetwork:
        calcEdges(button)
        neighbours = cellNetwork.neighbors(button)
        phase = cellNetwork.nodes[button]['phase']
        if phase == (clockState)%4 or phase == (clockState+1)%4 or phase == (clockState+2)%4:
            cellNetwork.nodes[button]['graphdata'] = []
            cellNetwork.nodes[button]['state'] = [1,1,1,1]
            button.texture = spriteDict[0].texture
            renderBuffer.append(button)
        stability = [0,0,0,0]
        state = cellNetwork.nodes[button]['state']
        if state != [1,1,1,1]:
            stability[state.index(max(state))] = 4
            cellNetwork.nodes[button]['state'] = stability
    spriteRenderer.render(renderBuffer)
    renderer.fill((boxSize*5,0,boxSize*(width-16),boxSize),color=sdl2.ext.Color(255,0,0))
    for iteration in range(iterationsPerClock):
        if iteration%math.ceil(iterationsPerClock/20)==0:
            renderer.fill((boxSize*5,0,round(iteration*boxSize*(width-16)/iterationsPerClock),boxSize),color=sdl2.ext.Color(0,255,0))
            renderer.present()
        for button in cellNetwork:
            state = cellNetwork.nodes[button]['state']
            phase = cellNetwork.nodes[button]['phase']
            graphData = cellNetwork.nodes[button]['graphdata']
            if phase == clockState:
                stability = calcPolar(button)
                graphData.append(stability)
                cellNetwork.nodes[button]['graphdata'] = graphData
                cellNetwork.nodes[button]['newState'] = stability
        for button in cellNetwork:
            if cellNetwork.nodes[button]['phase'] != -1:
                cellNetwork.nodes[button]['state'] = cellNetwork.nodes[button]['newState']
    renderer.fill((boxSize*5,0,boxSize*(width-15),boxSize),color=sdl2.ext.Color(0,0,0))
    renderBuffer = []
    for button in cellNetwork:
        if cellNetwork.nodes[button]['phase'] == clockState:
            button.texture = spriteDict[clockState+6].texture
            renderBuffer.append(button)
    clockState = (clockState+1)%4
    clockIndicator.texture = spriteDict[clockState+6].texture
    renderBuffer.append(clockIndicator)
    spriteRenderer.render(renderBuffer)
    renderBuffer = []
    for button in cellNetwork:
        if cellNetwork.nodes[button]['phase'] != -1:
            polarisation = cellNetwork.nodes[button]['state'].copy()
            if polarisation != [1,1,1,1]:
                maximum = polarisation.index(max(polarisation))
                button.texture = spriteDict[maximum+11].texture
                
            else:
                button.texture = spriteDict[0].texture
            renderBuffer.append(button)
    spriteRenderer.render(renderBuffer)
            
def calcPolar(button):
    neighbours = cellNetwork.neighbors(button)
    offsets = ((0,-1),(diagonalDistance,-diagonalDistance),(1,0),(diagonalDistance,diagonalDistance))
    stabilityList = [0,0,0,0]
    for i in neighbours:
        weight = cellNetwork[button][i][0]['weight']
        neighbourState = cellNetwork.nodes[i]['state']
        for k in range(4):
            distance = [0,0,0,0]
            distance[0] = weight[0]+cellRadius*offsets[k][0]
            distance[1] = weight[1]+cellRadius*offsets[k][1]
            distance[2] = weight[0]-cellRadius*offsets[k][0]
            distance[3] = weight[1]-cellRadius*offsets[k][1]
            for j in range(4):
                tempDistance = distance.copy()
                tempDistance[0] -= cellRadius*offsets[j][0]
                tempDistance[1] -= cellRadius*offsets[j][1]
                tempDistance[2] -= cellRadius*offsets[j][0]
                tempDistance[3] -= cellRadius*offsets[j][1]
                stabilityList[j] += (neighbourState[k]-1)*electronChargeSquared*coulomb/(4*math.sqrt(tempDistance[0]**2+tempDistance[1]**2))
                stabilityList[j] += (neighbourState[k]-1)*electronChargeSquared*coulomb/(4*math.sqrt(tempDistance[2]**2+tempDistance[3]**2))

                
                tempDistance = distance.copy()
                tempDistance[0] += cellRadius*offsets[j][0]
                tempDistance[1] += cellRadius*offsets[j][1]
                tempDistance[2] += cellRadius*offsets[j][0]
                tempDistance[3] += cellRadius*offsets[j][1]
                stabilityList[j] += (neighbourState[k]-1)*electronChargeSquared*coulomb/(4*math.sqrt(tempDistance[0]**2+tempDistance[1]**2))
                stabilityList[j] += (neighbourState[k]-1)*electronChargeSquared*coulomb/(4*math.sqrt(tempDistance[2]**2+tempDistance[3]**2))
    probabilityList = [math.exp((stabilityList[0]-i)/(boltzmann*temperature)) for i in stabilityList]
    divisor = sum(abs(i) for i in probabilityList)
    probabilityList = [4*i/divisor for i in probabilityList]
    return probabilityList

def calcEdges(button):
    position = button.position
    for i in cellNetwork:
        weight = ((i.position[0]-position[0])/boxSize,
                  (i.position[1]-position[1])/boxSize)
        if i != button and abs(weight[0])<=simDistance and abs(weight[1])<=simDistance:
            cellNetwork.add_edge(button, i, weight=[weight[0]*cellSpacing,weight[1]*cellSpacing])

def detailWindow(graphData):
    global horizontalScale
    global verticalScale
    subWindow = sdl2.ext.Window("Detail", size=(boxSize*horizontalScale,boxSize*verticalScale*9))
    runningWindows.append(subWindow)
    subWindow.show()
    subRenderer = sdl2.ext.Renderer(subWindow)
    subSpriteFactory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=subRenderer)
    subSpriteRenderer = subSpriteFactory.create_sprite_render_system(subWindow)
    subUIFactory = sdl2.ext.UIFactory(subSpriteFactory)
    subSpriteDict = (subSpriteFactory.from_image(directory + '/EW_LOCKED.png'),
               subSpriteFactory.from_image(directory + '/NWSE_LOCKED.png'),
               subSpriteFactory.from_image(directory + '/NS_LOCKED.png'),
               subSpriteFactory.from_image(directory + '/NESW_LOCKED.png'))
    subRenderer.present()
    renderBuffer = []
    polarCoords = []
    numberOfPoints = len(graphData)
    if numberOfPoints > 0:
        for i in range(numberOfPoints):
            midPoints = [(graphData[i][0]-graphData[i][2])/4,(graphData[i][1]-graphData[i][3])/4]
            polarCoords.append([math.sqrt(midPoints[0]**2+midPoints[1]**2), (math.atan2(midPoints[1],midPoints[0])/math.pi+1.25)%2])
        previousPointAmplitude = polarCoords[0][0]
        previousPointAngle = polarCoords[0][1]
        for dataPoint in range(numberOfPoints):
            amplitude = polarCoords[dataPoint][0]
            angle = polarCoords[dataPoint][1]
            amplitudeLineCoords = (round(((dataPoint)/numberOfPoints)*boxSize*(horizontalScale-verticalScale)+verticalScale*boxSize),
                                   round((1-previousPointAmplitude)*verticalScale*boxSize*4),
                                   round(((dataPoint+1)/numberOfPoints)*boxSize*(horizontalScale-verticalScale)+verticalScale*boxSize),
                                   round((1-amplitude)*verticalScale*boxSize*4))
            angleLineCoords = (round(((dataPoint)/numberOfPoints)*boxSize*(horizontalScale-verticalScale)+verticalScale*boxSize),
                                   round((2.25+previousPointAngle)*verticalScale*boxSize*2),
                                   round(((dataPoint+1)/numberOfPoints)*boxSize*(horizontalScale-verticalScale)+verticalScale*boxSize),
                                   round((2.25+angle)*verticalScale*boxSize*2))
            subRenderer.draw_line(amplitudeLineCoords,color=sdl2.ext.Color(255,255,0))
            if abs(previousPointAngle - angle)<1.9 and previousPointAmplitude != 0:
                subRenderer.draw_line(angleLineCoords,color=sdl2.ext.Color(255,255,0))
            previousPointAmplitude = amplitude
            previousPointAngle = angle
    subRenderer.draw_line((verticalScale*boxSize-1,0,verticalScale*boxSize-1,4*verticalScale*boxSize),color=sdl2.ext.Color(255,255,255))
    subRenderer.draw_line((horizontalScale*boxSize,4*verticalScale*boxSize+1,verticalScale*boxSize-1,4*verticalScale*boxSize+1),color=sdl2.ext.Color(255,255,255))
    subRenderer.fill((0,round(boxSize*4.5*verticalScale),boxSize*verticalScale,boxSize*4*verticalScale),color=sdl2.ext.Color(255,255,255))
    for i in range(4):
        icon = subSpriteFactory.create_sprite(size=(boxSize*verticalScale, boxSize*verticalScale))
        icon.position = (0, round(verticalScale*(i+4.5)*boxSize))
        icon.texture = subSpriteDict[i].texture
        renderBuffer.append(icon)
    text = subSpriteFactory.from_text("Polarization",fontmanager=fontManager)
    text.angle = -90
    text.position = (round(-0.5*verticalScale*boxSize),2*verticalScale*boxSize)
    renderBuffer.append(text)
    subSpriteRenderer.render(renderBuffer)

def errorWindow(error):
    errWindow = sdl2.ext.Window("Error", size=(500,100))
    runningWindows.append(errWindow)
    errWindow.show()
    errRenderer = sdl2.ext.Renderer(errWindow)
    errSpriteFactory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=errRenderer)
    errSpriteRenderer = errSpriteFactory.create_sprite_render_system(errWindow)
    err = errSpriteFactory.from_text(error,fontmanager=fontManager)
    errRenderer.present()
    errSpriteRenderer.render(err)

def settingsWindow(a,b):
    global height
    global width
    global boxSize
    global horizontalScale
    global verticalScale
    global cellRadius
    global cellSpacing
    global simDistance
    global iterationsPerClock
    setWindow = sdl2.ext.Window("Settings", size=(500,500))
    runningWindows.append(setWindow)
    setWindow.show()
    setRenderer = sdl2.ext.Renderer(setWindow)
    setSpriteFactory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=setRenderer)
    setSpriteRenderer = setSpriteFactory.create_sprite_render_system(setWindow)
    setUIFactory = sdl2.ext.UIFactory(setSpriteFactory)
    settings = (("Window Height (cells)",height),
                ("Window Width (cells)",width),
                ("Cell Draw Size",boxSize),
                ("Detail Window Height",verticalScale),
                ("Detail Window Width",horizontalScale),
                ("Cell Radius",cellRadius),
                ("Cell Spacing",cellSpacing),
                ("Simulation Range (cells)",simDistance),
                ("Simulation Iterations",iterationsPerClock))
    textEntries = []
    renderBuffer = []
    j = 0
    for i in settings:
        text = setSpriteFactory.from_text(i[0],fontmanager=fontManager)
        text.position = (0,20*j)
        value = setSpriteFactory.from_text(str(i[1]),fontmanager=fontManager)
        textInput = setUIFactory.create_text_entry(size=(100,16))
        textInput.position = (200,20*j)
        #textInput.texture = value.texture
        textEntries.append((text,textInput))
        renderBuffer.append(text)
        renderBuffer.append(textInput)
        j = j + 1
    setSpriteRenderer.render(renderBuffer)

#def changeSetting(a,b):


sdl2.ext.init()
sdl2.sdlttf.TTF_Init()
window = sdl2.ext.Window("Ternary QCA", size=(widthpx, heightpx))
runningWindows.append(window)
window.show()
renderer = sdl2.ext.Renderer(window)
spriteFactory = sdl2.ext.SpriteFactory(sdl2.ext.TEXTURE, renderer=renderer)
spriteRenderer = spriteFactory.create_sprite_render_system(window)
UIFactory = sdl2.ext.UIFactory(spriteFactory)
spriteDict = createSpriteDictionary()
fontManager = sdl2.ext.FontManager(directory + '/FONT.ttf',size=16,color=(sdl2.ext.Color(255,255,255)))

UI()
idle()
