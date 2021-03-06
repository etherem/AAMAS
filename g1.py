import math, random
from math import pi, sqrt, pow
import pygame, settings
from pprint import pprint

# Authors:
# Group 1, AAMAS 2011 spring
# Ben Haanstra, 5964911
# Daniel Peder Dahlsveen, 6425003
# Al Koudous Idrissou

# VERSION 15:00 / 24 feb 2011

###############################################################################

    ## Global Variables
    # - agentKnowledge: dictionary on id that contains dictionaries: contains all relevant information about our agents that can be consulted by any agent at any time
    # - knownPaths: remembers all paths that we've found
    # - wallsKnowledge: hardcoded wallsets as we already know the map
    # - iteration: the time step in the game, incremented for each agent. Modulo 8 gives ingame iterations
    # - alreadyTaken: list of positions of either ammopacks or enemy agents (only enemy atm), to prevent several agents from picking the same object
    # - taskList: dictionary on CP positions: for each task information we remember which agents are assigned to that task as well as other information
    # - taskNames: list: in order to iterate over the taskList

    ## Functions specific for path planning (Creating and using paths)
    #+ Paths
    # - createNewPath: Creates a new path to a goal (CP)
    # - getNextStep; Checks the proposed next step
    # - findNextStep: Checks the corners of the blocking wall, and tries to find a path (close) to a corner which is not blocked
    # - getCorner: When trying a new position in findNextStep a "node" outside of the blocking walls corner is used, generated by this function
    #+ Wall detection
    # - pathBlockedWall: Finds any walls that might block two points in space, defined by formula
    # - checkLineCross: Checks if a line defined by formula is intersected by the wall defined by corners.
    #+ Using found paths
    # - lookUp: Finds the closest start of a path to a goal (CP)
    # - addNewPath: Adds a new path to known paths
        
    ## Functions for moving the agent as well as shooting
    # - moveTo: only used for enemies/objects for which weve already decided beforehand that they're reachable
    # - goTask: uses path planning to get to a specific target
    # - moveRandom: moves the agent randomly
    # - shootTarget: function used to shoot a target or engage a target
    
    ## Functions for objects
    # - getObject: creates a list of objects and the conditions that they should be checked on and returns the found nearest object
    # - getNearestObject: checks the list constructed by getObject and returns the object that is the best (requires least movement and turns)
    # - pathBlockedObj: checks whether the object is reachable for the agent (i.e. not behind a wall) with a very simple algorithm
    # - numSteps: creates a value for an object's position relative to another position based on how many turns and the distance between them.
    
    ## Functions for behaviour (single & multiple)
    #+ Single
    # - actBot: the generic behaviour of the agent for all parts of the game
    #+ Multiple
    # None atm.
    
    ## Auxiliary functions
    # getFormula: used by wall detection to create a formula of the form: y=ax+b
    # get_closest: get the closest (euclidean) element in a list to a position
    # get_closest: same, but return the index in the list
    # angleTurn: used to get the best angle turn for a bot
    # angle_between_points: the angle between points
    # distance_between_points: euclidean distance between points
    
###############################################################################


wallsKnowledge = [
   [((300,100),(303,100),(300,300),(303,300)), ((100,300),(303,300),(100,303),(303,303))],
   [((300,500),(303,500),(300,700),(303,700)), ((100,500),(303,500),(100,503),(303,503))],
   [((600,400),(797,400),(600,403),(797,403)), ((600,200),(603,200),(600,600),(603,600))]
]
knownPaths = {} # Dictionary of paths for specific goals
agentKnowledge = {} # dictionary of agents
iteration = 0
alreadyTaken = [] # use this to say which ammo / enemy is already taken so other agenst choose other targets
taskList = {} # contains tasks
taskNames = [] # contains the names of the tasks so we can easily iterate over the tasks



class AgentBrain():
    agent_no = 1
    def __init__(self):
        self.no = AgentBrain.agent_no
        AgentBrain.agent_no += 1
    
    def action(self, observation):
        action = {
            'turn': 0,
            'speed': 0,
            'shoot': False
        }

        # INITALISATION of global variables:
        if len(knownPaths) == 0 : # initialize checkpoints as goals
            for item in observation['controlpoints'] :
                knownPaths[item['location']] = [] # no known paths for the goal (we remember a goal as a position)
                taskList[item['location']] = {'agents':[], 'priority':0, 'pressure':0, 'area':item['location'], 'enemyAgents':0, 'type':'cp', 'ammopacks':[], 'needAssistance':False, 'owned':item['team']}
                taskNames.append(item['location'])
                # numAgents how many agents at task, priority is its priority, pressure: how many enemies come to this position, area refers to the area of this task (could be a position or an area)
            # bottom
            self.addNewPath([[[653, 650], [((600, 400), (797, 400), (600, 403), (797, 403)), ((600, 200), (603, 200), (600, 600), (603, 600))]], [[550, 650], [((600, 400), (797, 400), (600, 403), (797, 403)), ((600, 200), (603, 200), (600, 600), (603, 600))]], [[353, 50], [((300, 100), (303, 100), (300, 300), (303, 300)), ((100, 300), (303, 300), (100, 303), (303, 303))]], [[250, 50], [((300, 100), (303, 100), (300, 300), (303, 300)), ((100, 300), (303, 300), (100, 303), (303, 303))]], [(220, 220), []]], (220,220))
            self.addNewPath([[[653, 650], [((600, 400), (797, 400), (600, 403), (797, 403)), ((600, 200), (603, 200), (600, 600), (603, 600))]], [[550, 650], [((600, 400), (797, 400), (600, 403), (797, 403)), ((600, 200), (603, 200), (600, 600), (603, 600))]], [(500, 400), []]], (500,400))
            self.addNewPath([[[653, 650], [((600, 400), (797, 400), (600, 403), (797, 403)), ((600, 200), (603, 200), (600, 600), (603, 600))]], [[250, 750], [((300, 500), (303, 500), (300, 700), (303, 700)), ((100, 500), (303, 500), (100, 503), (303, 503))]], [(220, 580), []]], (220,580))
            # top
            self.addNewPath([[[653, 150], [((600, 400), (797, 400), (600, 403), (797, 403)), ((600, 200), (603, 200), (600, 600), (603, 600))]], [[250, 50], [((300, 100), (303, 100), (300, 300), (303, 300)), ((100, 300), (303, 300), (100, 303), (303, 303))]], [(220, 220), []]], (220,220))
            self.addNewPath([[[653, 150], [((600, 400), (797, 400), (600, 403), (797, 403)), ((600, 200), (603, 200), (600, 600), (603, 600))]], [[550, 150], [((600, 400), (797, 400), (600, 403), (797, 403)), ((600, 200), (603, 200), (600, 600), (603, 600))]], [(500, 400), []]], (500,400))
            self.addNewPath([[[653, 150], [((600, 400), (797, 400), (600, 403), (797, 403)), ((600, 200), (603, 200), (600, 600), (603, 600))]], [[550, 150], [((600, 400), (797, 400), (600, 403), (797, 403)), ((600, 200), (603, 200), (600, 600), (603, 600))]], [(353, 753), [((300, 500), (303, 500), (300, 700), (303, 700)), ((100, 500), (303, 500), (100, 503), (303, 503))]], [(250, 753), [((300, 500), (303, 500), (300, 700), (303, 700)), ((100, 500), (303, 500), (100, 503), (303, 503))]], [(220, 580), []]], (220,580))
            global iteration
#            pickel.load('savedPaths')
            
        # Initialization of agentKnowledge
        if iteration == 0 : # we know there are 8 agents for this map, if there are more, increase the number
            for agent in observation['agents'] :
                if agent['team'] == observation['team'] :
                    agentKnowledge[agent['id']] = {'id': agent['id'], 'goal': (1,1), 'task': 0, 'path': [], 'previousNode':[], 'idle':0, 'lastPosition':agent['location'], 'direction':agent['direction'], 'ammo':0}
                    for item in taskNames :
                        if len(taskList[item]['agents']) < 3 and agentKnowledge[agent['id']]['task'] == 0 :
                            taskList[item]['agents'].append(agent['id'])
                            agentKnowledge[agent['id']]['task'] = item[:]
                            agentKnowledge[agent['id']]['goal'] = item[:]
            agentKnowledge[observation['id']] = {'id': observation['id'], 'goal': (1,1), 'task': 0, 'path': [], 'previousNode':[], 'idle':0, 'lastPosition':observation['location'], 'direction':observation['direction'], 'ammo':0}
            for item in taskNames :
                if len(taskList[item]['agents']) < 3 and agentKnowledge[observation['id']]['task'] == 0 :
                    taskList[item]['agents'].append(observation['id'])
                    agentKnowledge[observation['id']]['task'] = item[:]
                    agentKnowledge[observation['id']]['goal'] = item[:]
        
        
        # UPDATE KNOWLEDGE
        # Update whether we own a task.
        for item in observation['controlpoints']:
            if item['team'] == observation['team'] :
                taskList[item['location']]['owned'] = observation['team']                        
            else :
                taskList[item['location']]['owned'] = item['team']

        # Update information for the agents
        if iteration % 8 == 0 : # the 8 iterations here should correspond to 1 iteration ingame
            alreadyTaken = []
            
            # all observation agents (not the current agent himself)
            for agent in observation['agents'] :
                if agent['team'] == observation['team'] :
                    if agentKnowledge[agent['id']]['lastPosition'] == agent['location'] :
                        agentKnowledge[agent['id']]['idle'] = agentKnowledge[agent['id']]['idle']+1
                    else :
                        agentKnowledge[agent['id']]['idle'] = 0
                        agentKnowledge[agent['id']]['lastPosition'] = agent['location']
                    agentKnowledge[agent['id']]['direction'] = agent['direction']

            # agent himself
            if agentKnowledge[observation['id']]['lastPosition'] == observation['location'] :
                agentKnowledge[observation['id']]['idle'] = agentKnowledge[observation['id']]['idle']+1
            else :
                agentKnowledge[observation['id']]['idle'] = 0
                agentKnowledge[observation['id']]['lastPosition'] = observation['location']
            agentKnowledge[observation['id']]['direction'] = observation['direction']

            
        iteration = iteration + 1
        
        agentKnowledge[observation['id']]['ammo'] = observation['ammo']
        
        # Observation relating to tasks
        for item in taskNames :
            # How many enemies there are etc.
            if taskList[item]['pressure'] > 0 :
                taskList[item]['pressure'] = taskList[item]['pressure'] - 1
        
        
        # TASK DIVISION
#        for item in taskNames :
#            if len(taskList[item]['agents']) < 3 and agentKnowledge[observation['id']]['task'] == 0 :
#                taskList[item]['agents'].append(observation['id'])
#                agentKnowledge[observation['id']]['task'] = item[:]
#                agentKnowledge[observation['id']]['goal'] = item[:]
#                print agentKnowledge[observation['id']]['goal']
#        print agentKnowledge
        action = self.actBot(observation, action)

        return action
          
    def distance_between_points(self,x,y):
        return sqrt( pow(abs(x[0]-y[0]),2) + pow(abs(x[1]-y[1]),2) )
        
    def angle_between_points(self,x,y):
        return math.atan2(y[1] - x[1], y[0] - x[0] )
    
    def getFormula(self,x,y):
        # From two positions, create a formula (i.e. straight line/function), return the y position of a given position using that formula
        if y[0]-x[0] == 0:
            a = 1.0
            b = x[1]-(x[0]*a)
        else :
            a = (float(y[1])-float(x[1]))/(float(y[0])-float(x[0]))
            b = x[1]-(x[0]*a)
            
        return {'a':a,'b':b,'start':x,'end':y}
        
    def get_closest(self,list,location):
        if list == []:
            return "None"
        closest = list[0]
        shortest_dist = self.distance_between_points(closest, location)
        list.pop(0)
        for element in list:
            dist = self.distance_between_points(element,location)
            if dist < shortest_dist:
                closest = element
                shortest_dist = dist
        return closest
    
    def get_closest_nr(self,list,location):
        # This is used for a list of paths, where we don't care about its position, but only its index in the list
        if list == []:
            return "None"
        shortest_dist = 9999999
        currentnr = 0
        for element in list:
            dist = self.distance_between_points(element,location)
            if dist < shortest_dist:
                number = currentnr 
                shortest_dist = dist
            currentnr = currentnr+1
        return number
    
    def angleTurn(self, targetPosition, observation):
        # Allowing the agent to turn around both ways:
        a = self.angle_between_points(observation['location'],targetPosition) - observation['direction']
        if a < -1*pi :
            a = a+2*pi
        elif a > pi :
            a = a-2*pi
        return a   
     
    def getCorner(self, corner, nrcorner):
        # This is used to construct 'guidance nodes' that can be used to find a path.
        # Guidance nodes, because the agents themselves still decide whether to go to that node or not.
        # That means, they don't move strictly to that node
        p = 50
        return {
                0 : [corner[0]-p, corner[1]-p], # topleft
                1 : [corner[0]+p, corner[1]-p], # topright
                2 : [corner[0]-p, corner[1]+p], # bottomleft
                3 : [corner[0]+p, corner[1]+p], # bottomright
                }[nrcorner]
      
    def pathBlocked(self, targetPosition, position, observation):
        # In this part we have a target (that the bot wants to go to) and its position. We iterate over all other agents to see whether there is something in its way, if this is the case we return yes, otherwise no.
        formula = self.getFormula(position, targetPosition)
        blockingAgents = []
        for agent in agents:
            posy = (agent['location'][0]*formula['a'])+formula['b']
            # Now, if the difference between the agent and the path to the target is less than 7 (estimation) they will hit
            # if their distance is less or equal to the max speed. And if the position of the agent is actually within the path (x < agent.loc < end)
            hit = (abs((agent['location'][1]-posy)) < 7) & (self.distance_between_points(position, agent['location']) < 50) & agent['location'][0] > formula['start'] & agent['location'][0] < formula['end']
            if hit==True:
                blockingAgents.append(agent['location']) # add the agent to the list

        return self.get_closest(blockingAgent, position) # return the closest one
    
    def pathBlockedWall(self, formula):
        # Check all known walls
        closestWallset = []
        bdist = 99999999
        for wallset in wallsKnowledge :
            for wall in wallset :
                # Create useful corners to check collision
                if self.checkLineCross(formula, wall) :
                    avgx = (wall[0][0]+wall[1][0]) / 2
                    avgy = (wall[1][1]+wall[2][1]) / 2
                    if self.distance_between_points(formula['start'], [avgx,avgy]) < bdist :
                        closestWallset = wallset
        return closestWallset
    
    def pathBlockedObj(self, object, observation):        
        # Acquire the positions, in order to make a relative classification about the object
        minx = min(observation['location'][0],object[0])
        miny = min(observation['location'][1],object[1])
        maxx = max(observation['location'][0],object[0])
        maxy = max(observation['location'][1],object[1])
        
        for wall in observation['walls'] :
            if minx < wall['left'] and wall['left'] < maxx :
                if miny < wall['top'] and wall['top'] < maxy :
                    return True
                elif miny > wall['top'] and wall['bottom'] > maxy :
                    return True
                elif miny < wall['bottom'] and wall['bottom'] < maxy :
                    return True
            if minx < wall['right'] and wall['right'] < maxx :
                if miny < wall['top'] and wall['top'] < maxy :
                    return True
                elif miny > wall['top'] and wall['bottom'] > maxy :
                    return True
                elif miny < wall['bottom'] and wall['bottom'] < maxy :
                    return True
            if minx > wall['left'] and wall['right'] > maxx :
                if miny < wall['top'] and wall['top'] < maxy :
                    return True
                elif miny > wall['top'] and wall['bottom'] > maxy :
                    return True
                elif miny < wall['bottom'] and wall['bottom'] < maxy :
                    return True
                
        return False
    
    def checkLineCross(self, formula, corners):
        # Idea: get all corners of the walls, check for each corner whether it is above/below/left/right of the formula. If one of them is left(or above) while another is right(or below) then the wall blocks the path
        relPos = [[1],[1],[1],[1]]
        cornernr = 0
        miny = min(formula['start'][1],formula['end'][1])
        maxy = max(formula['start'][1],formula['end'][1])
        minx = min(formula['start'][0],formula['end'][0])
        maxx = max(formula['start'][0],formula['end'][0])
        collision = 11
        for corner in corners :
            if (formula['a']*corner[0]+formula['b']) < corner[1] :
                relPos[cornernr] = 2
            else :
                relPos[cornernr] = 0
            if abs((formula['a']*corner[0]+formula['b']) - corner[1]) < collision and minx-collision < corner[0] and corner[0] < maxx+collision and miny-collision < corner[1] and corner[1] < maxy+collision  : # or if we hit a corner. *** this works OK
                return True
            cornernr = cornernr+1

        if relPos[0] != relPos[1] : # topleft to bottomleft i.e. horizontal line
            if miny-5 < corners[0][1] & corners[0][1] < maxy+5 : # the topleft corner is within the domain of start to end
                return True
        if relPos[0] != relPos[2] : # topleft to bottomleft i.e. vertical line
            if minx-5 < corners[0][0] & corners[0][0] < maxx+5 : # the topleft corner is within the domain of start to end
                return True
        return False

    def createNewPath(self, observation, goal):
        # a path contains an array with nodes and their walls 
        # Create a formula, then check on observation whether there are walls
        agent = observation['location']
        formula = self.getFormula(agent, goal)
        blockWall = self.pathBlockedWall(formula)
        
        # initialization:
        path = [[goal,[]]] # goal, wall
        alreadyPassed = [observation['location']]
        # If there is a wall, we will formulate a more appropriate path planning
        if blockWall != [] :
            pathCheck = self.findNextStep(blockWall, agent, goal, observation, 0, alreadyPassed)
            path = pathCheck['path']

        return path
    # get multiple paths? create multiple and save them at the end + a distance..?

    def findNextStep(self, currentWalls, position, goal, observation, depth, alreadyPassed):
        # This recursively checks all possible corners whether it is reachable and if so try to find the next step
        currentStep = {'score' : 999999, 'path':[[position, currentWalls]]}
         # For simplicity, so we don't have to use a dictionary nor do any complex math.
        for wall in currentWalls :
            nrcorner = 0
            for corner in wall :
                # get an appropriate reachable position that we can try
                tryPosition = self.getCorner(corner, nrcorner)
                if not(tryPosition in alreadyPassed) and 0 < tryPosition[0] and tryPosition[0] < 800 and 0 < tryPosition[1] and tryPosition[1] < 800 :
                    # To prevent cycles we remember what path we have already followed
                    newPassed = alreadyPassed[:]
                    newPassed.append(tryPosition)
                    
                    formula = self.getFormula(position, tryPosition)
                    blockWall = self.pathBlockedWall(formula)
                    if blockWall == [] : # If we can access the tryPosition (not obstructed by a wall):
                        traject=self.getNextStep(tryPosition, goal, observation, depth, newPassed) # find the next step
                        traject['score'] = traject['score']+self.distance_between_points(position, tryPosition)
                        traject['path'].insert(0, [tryPosition, currentWalls]) # add the current tryPosition and the currentWall to the path
                        if currentStep['score'] > traject['score'] :
                            currentStep['score'] = traject['score'] # better path found
                            currentStep['path'] = traject['path']
                nrcorner = nrcorner+1
        return currentStep
    
    def getNextStep(self, position, goal, observation, depth, alreadyPassed):
        currentNode = {'score' : self.distance_between_points(position,goal), 'path' : [[goal,[]]]}
        if depth == 5: # the depth of the search space becomes too big (we want speed)
            return {'score' : 1000, 'path' : [[alreadyPassed[-1],[]]]} #this score choice allows for partial paths to be constructed, but not preferred over a complete one
        
        # Check for walls between our position and the goal
        formula = self.getFormula(position, goal)
        blockWall = self.pathBlockedWall(formula)
        depth=depth+1
        if blockWall != []: # if there is a wall, we take a next step
            currentNode = self.findNextStep(blockWall, position, goal, observation, depth, alreadyPassed)
        # The only remaining case is that we found a path to the goal that isnt blocked
        return currentNode
      
    def lookUp(self, observation, goal):
        # In: observation, goal
        # Global: knownPaths
        # Out: path that is suitable for the current agent
        
        listPaths = knownPaths[goal]
        best = 99999999
        bestpath = []
        if listPaths != [] :
            for path in listPaths :
                dist = self.distance_between_points(observation['location'], path[0][0])
                if dist < best : 
                    formula = self.getFormula(observation['location'], path[0][0])
                    if self.pathBlockedWall(formula) == [] :
                        bestpath = path[:]
                        best = dist
        return bestpath
        
    def addNewPath(self, newPath, goal):
        # In: newPath, goal
        # Global: knownPaths(adds to)
        
        if not(newPath in knownPaths[goal]) : # prevent duplications
            while len(newPath)>1 : # when there is only one remaining, that is the goal
                onePath = newPath[:]
                knownPaths[goal].append(onePath)
                del newPath[0]
                      
    def getObject(self, observation, type):
        # In: observation, type
        # Out: best suitable object based on the type
        
        objectList = []
        if type == 'enemy' :
            distcond = settings.MAX_SHOT_DISTANCE
            for object in observation['agents'] :
                if observation['team'] != object['team'] :
                    objectList.append(object)
        else :
            distcond = settings.MAX_SPEED
            objectList = observation[type]

        return self.getNearestObject(observation, objectList, distcond)
                
    def getNearestObject(self, observation, objectList, distcond):
        # In: observation, list objects, distance condition (used by numStep)
        # Global: alreadyTaken
        # Out: target that has the lowest numStep value
        
        target={'location':[], 'angle':0, 'distance':999999,'inRange':-1, 'best':8}
        for object in objectList :
            if not(object in alreadyTaken) :
                if self.pathBlockedObj(object['location'], observation) == False and object['location'][0] > 0 and object['location'][0] < 800 and object['location'][1] < 800 and object['location'][1] > 0:
                    dist = self.distance_between_points(observation['location'], object['location'])
                    a = self.angle_between_points(observation['location'], object['location']) - observation['direction']
                    if a < -1*pi :
                        a = a+2*pi
                    elif a > pi :
                        a = a-2*pi
                    num = self.numSteps(a, dist, distcond)
                    if num < target['best'] :
                        if dist < target['distance'] :
                            target['best'] = num
                            target['distance'] = dist
                            target['angle'] = a
                            target['location'] = object['location']
                            if dist <= distcond :
                                target['inRange'] = 1
        
        return target
    
    def numSteps(self, a, dist, distcond):
        # In: angle, distance and distance condition
        # Imported: settings
        # Out: value for the angle/distance
        
        num = 0
        if abs(a) <= pi/3 :
            num = num + 0
        elif abs(a) <= pi*2/3 :
            num = num + 1
        else : # abs(a) >= pi*2/3 :
            num = num + 2
        if dist <= distcond :
            num = num + 0
        elif dist > distcond and dist <= settings.MAX_SPEED+distcond : # because it would have to move+shoot then.
            num = num + 1
        else :
            num = num + 2
        return num

    
    def goTask(self, observation, action):
        # In: observation, action
        # Globals: agentKnowledge
        # Out: action dictionary that moves the agent to the target
        
        # When a goal has changed or the agent has been idle for too long
        targetPosition = action
        # Find new path if it doesn't have any
        if agentKnowledge[observation['id']]['path'] == [] : # if goal changed, change path to []
            checkPath = self.lookUp(observation, agentKnowledge[observation['id']]['goal'])
            if checkPath == [] : # if no path is known
                newPath = self.createNewPath(observation, agentKnowledge[observation['id']]['goal']) # create a new path
                if len(newPath) > 1 and newPath[-1][0] == agentKnowledge[observation['id']]['goal'] : # otherwise it is just its goal and isnt a valid path
                    self.addNewPath(newPath, agentKnowledge[observation['id']]['goal']) # add the found path to the dictionary
                agentKnowledge[observation['id']]['path'] = newPath[:]
            else : # update the agents new path
                agentKnowledge[observation['id']]['path'] = checkPath[:]
        
        # countermeasures for when there is a wall that isn't seen before?
        if agentKnowledge[observation['id']]['idle'] > 3 and self.distance_between_points(observation['location'], agentKnowledge[observation['id']]['goal']) > 5 :
            agentKnowledge[observation['id']]['path'] = []
            return self.moveRandom()
            
        else : # agent isnt idle, proceed to goal
            path = agentKnowledge[observation['id']]['path']
            getoutwhile = 0
            notBlocked = True
            while len(path) > 1 and notBlocked == True:
                currentNode = path[0]
                nextNode = path[1]
                formula = self.getFormula(observation['location'], nextNode[0])
                for wall in currentNode[1] :
                    if self.checkLineCross(formula, wall) == True :# 2 = formula, 1 = wall
                        notBlocked = False
                        break
                if notBlocked == True :
                    agentKnowledge[observation['id']]['previousNode'] = path[0]
                    del path[0]
                    
            target = agentKnowledge[observation['id']]['path'][0][0]
        
            targetPosition['turn']=self.angleTurn(target, observation)
            if abs(targetPosition['turn']) > pi/3 : # if it is behind, move slowly
                targetPosition['speed'] = 0
            else :
                targetPosition['speed']=min(self.distance_between_points(observation['location'], target),50)
                
        return targetPosition
    
    def moveRandom(self):
        # In: nothing
        # Out: random behaviour
        targetPosition = {}
        targetPosition['turn'] = random.random()*pi/1.5 - pi/3
        targetPosition['speed'] = 50
        targetPosition['shoot'] = False
        return targetPosition
    
    def moveTo(self, observation, action, targetPosition):
        # In: observation, action and targetPosition
        # Out: action dictionary
        action['turn'] = self.angleTurn(targetPosition, observation)
        if abs(action['turn']) > pi/3 : # if it is behind, move slowly
            action['speed'] = 0
        else :
            action['speed']=min(self.distance_between_points(observation['location'], targetPosition),50)
        if agentKnowledge[observation['id']]['idle'] > 3 and self.distance_between_points(observation['location'], agentKnowledge[observation['id']]['goal']) > 5 :
            return self.moveRandom()
        return action
    
    def shootTarget(self, observation, enemy):
        # input: observation and enemy
        # output: actions that the agent should take
        action = {}
        action['turn'] = enemy['angle']
        action['speed'] = min(enemy['distance']/2, 50)
        if enemy['distance'] < settings.MAX_SHOT_DISTANCE :
            action['speed'] = 0
            if enemy['best'] == 0 :
                action['shoot'] = True
            alreadyTaken.append(enemy['location'])
        return action
        
    def actBot(self, observation, action):
        # In: observation, action
        # Global: agentKnowledge, taskList
        # Out: action dictionary for one agent
        
        # BEHAVIOUR OF ONE AGENT
        # Four kinds of behaviour:
        # 1. guarding a capture point + gathering ammo
        # 2. attacker of a capture point owned by enemy
        # 3. capturing a point that is neutral

        # 1 Capturepoint in possession
        if taskList[agentKnowledge[observation['id']]['goal']]['owned'] == observation['team'] :
            guarding = observation['id']
            second = observation['id']
            ammoagent = observation['id']
            mostammo = -1
            best = 9999
            for agent in taskList[agentKnowledge[observation['id']]['goal']]['agents'] :
                dist = self.distance_between_points(agentKnowledge[agent]['lastPosition'], observation['location'])
                a = self.angle_between_points(agentKnowledge[agent]['lastPosition'], observation['location']) - agentKnowledge[agent]['direction']
                steps = self.numSteps(a, dist, 7) # 7 = estimation radius CP/agent
                if best > steps :
                    best = steps
                    second = guarding
                    guarding = agent
                if mostammo < agentKnowledge[agent]['ammo'] :
                    mostammo = agentKnowledge[agent]['ammo']
                    ammoagent = agent
            
            # Defender       
            if guarding == observation['id'] : # closest
                enemy = self.getObject(observation, 'enemy')
                if enemy['best'] < 8 :
                    if observation['ammo'] == 0 :
                        return self.goTask(observation, action)
                    else :
                        action = self.shootTarget(observation, enemy)
                        action['speed'] = 0
                        return action
                else :
                    if second != guarding and self.distance_between_points(agentKnowledge[observation['id']]['goal'], agentKnowledge[second]['lastPosition']) < 5 and agentKnowledge[second]['ammo'] > observation['ammo'] : # there is someone else with ammo
                        # *** move to position with ammo
                        ammoNearby = self.getObject(observation, 'ammopacks')
                        if ammoNearby['inRange'] == 1 and taskList[agentKnowledge[observation['id']]['goal']]['pressure'] < 30 :
                            return self.moveTo(observation, action, ammoNearby['location'])
                        else :
                            return self.goTask(observation, action)
                    else :
                        return self.goTask(observation, action) # *** if adding expectation do it here
            
            # Scavenger/shooter
            else :
                enemy = self.getObject(observation, 'enemy')
                if enemy['best'] < 8 :
                    if observation['ammo'] == 0 :
                        # *** escape?
                        ammoNearby = self.getObject(observation, 'ammopacks')
                        if ammoNearby['best'] < 8 :
                            return self.moveTo(observation, action, ammoNearby['location'])
                        else :
                            return self.moveRandom()
                    else :
                        return self.shootTarget(observation, enemy)
                else :
                    if observation['id'] == ammoagent or taskList[agentKnowledge[observation['id']]['goal']]['needAssistance'] == True :
                        return self.goTask(observation, action)
                    else :
                        ammoNearby = self.getObject(observation, 'ammopacks')
                        if ammoNearby['best'] < 8 :
                            return self.moveTo(observation, action, ammoNearby['location'])
                        else :
                            return self.moveRandom()

        # 2 Assault at others team capture point
        if taskList[agentKnowledge[observation['id']]['goal']]['owned'] != 'Neutral' and taskList[agentKnowledge[observation['id']]['goal']]['owned'] != observation['team'] :
            # check if there is actually an enemy agent ***
            if observation['ammo'] > 0 :
                enemy = self.getObject(observation, 'enemy')
                if enemy['best'] < 8 :
                    return self.shootTarget(observation, enemy)
                else :
                    return self.goTask(observation, action)
            else :
                ammoNearby = self.getObject(observation, 'ammopacks')
                if ammoNearby['location'] != [] :
                    return self.moveTo(observation, action, ammoNearby['location'])
                else :
                    return self.goTask(observation, action)

        # 3 if point is still neutral
        if taskList[agentKnowledge[observation['id']]['goal']]['owned'] == 'Neutral' :
            if observation['ammo'] > 0 :
                enemy = self.getObject(observation, 'enemy')
                if enemy['best'] < 8 :
                    return self.shootTarget(observation, enemy)
                else :
                    return self.goTask(observation, action)
            else :
                ammoNearby = self.getObject(observation, 'ammopacks')
                if ammoNearby['best'] == 0 : # only go to ammo when you don't have to move around it
                    return self.moveTo(observation, action, ammoNearby['location'])
                else :
                    return self.goTask(observation, action)
        
        return action
    
    
    
    # BUGS:
    # o path planning doesnt fully work yet
    # - agents dont restore their paths
    # o shoots own teammate, feature issue
    # - ammo over capturepoint, even when no enemy nearby -> remember enemies? or scout