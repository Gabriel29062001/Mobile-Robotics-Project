# MARKOV THIS IS THE NEWer VERSION !!!

# Imports
import numpy as np
import math

import matplotlib.pyplot as plt
import seaborn as sn 

import tdmclient.notebook

# Constants

# Probability that the robot moved to the correct position (or "pixel")
P_HIT = 0.8
# Probability that the robot moved to a neighbouring "pixel"
P_MISS = 0.2/8 #8 neighboring pixels



# displays the heatmap of data_to_display
def display_heatmap(data_to_display):
    displayed_map = sn.heatmap(data = data_to_display, annot=False, linewidth=.5, vmin=0, vmax=1.0) 
    displayed_map.invert_yaxis()
    
# Function to update the probabilities of the neighboring pixels
def neighbouring_pixels(x,y,prob,any_map):
    global map_estimate_robot
    
    length,height = np.shape(any_map)

    # the if-statements make sure that we stay within any_map of dimensions length x height

    if (x-1 >= 0):    
        # Left row of neighbors
        if (y-1 >= 0):
            any_map[x-1][y-1] = prob
        any_map[x-1][y] = prob
        if (y+1 <= (height-1)):
            any_map[x-1][y+1] = prob

        # Middle row of neighbors
        if (y-1 >= 0):
            any_map[x][y-1] = prob

        any_map[x][y+1] = prob

    if (x+1 <= (length-1)):
        # Right row of neighbors
        if (y-1 >= 0):
            any_map[x+1][y-1] = prob
        any_map[x+1][y] = prob
        if (y+1 <= (height-1)):
            any_map[x+1][y+1] = prob

 

# map: each square has the prob = 1/(height * length)
# map_estimate_robot: empty map with size height x length
# map_estimate_CV: empty map with size height x length
def initialize_maps(height,length):
    global map, map_estimate_robot, map_estimate_CV
    
    # initialize map
    initial_prob = 1/(length*height)
    map = np.empty((height,length), float)
    map.fill(initial_prob)

    # create empty map_estimate_robot
    map_estimate_robot = np.empty((height,length), float)
    map_estimate_robot.fill(0.0)

    # create empty map_estimate_CV
    map_estimate_CV = np.empty((height,length), float)
    map_estimate_CV.fill(0.0)


def estimate_robot(x,y):
    global map_estimate_robot   
    
    # reset map to 0.0
    map_estimate_robot.fill(0.0)

    # the robot has a probability of P_HIT to be on the "pixel" is should be on
    map_estimate_robot[x][y] = P_HIT
    # the robot has a probability of P_MISS to be on a neighbouring "pixel"
    neighbouring_pixels(x,y,P_MISS,map_estimate_robot)



def estimate_CV(x,y,confidence_CV):
    # reset map to 0
    map_estimate_CV.fill(0)

    # add prob
    MEAS_P_HIT = confidence_CV
    MEAS_P_MISS = (1-confidence_CV)/8

    # confidence that the CV gave the correct position
    map_estimate_CV[x][y] = MEAS_P_HIT
    # probability that the CV thinks that the robot is on a neighbouring "pixel"
    neighbouring_pixels(x,y,MEAS_P_MISS,map_estimate_CV)
    

# Function to multiply probability maps and update the global map variable
def multiply_maps():
    global map, map_estimate_CV, map_estimate_robot

    # Multiply the probability maps of computer vision (CV) and robot belief position
    temp = np.multiply(map_estimate_CV,map_estimate_robot)
    
    # if the estimated position of the robot and by CV are too far apart, or the last position of the robot and its position now, the whole map after multiplication is = 0
    # in this case, set map = map_estimate_robot as it is less likely that the position measured by the robot is off by a lot than the CV
    
    if (not np.any(temp)):
        # If the multiplication results in all zeros, retain the current map value
        map = map
    else:
         # Update map by multiplying it with the temporary result
        map = np.multiply(map,temp)
    if (not np.any(map)):
         # If the resulting map is all zeros, update map to map_estimate_CV
        map = map_estimate_CV # IS THIS NECESSARY ????????




# Function to normalize the values in map such that the sum of all elements is 1
def normalize_map():
    global map
  
    # Calculate the sum of all values in the map array
    sum = np.sum(map)
     # Divide each element in the map array by the sum to normalize the values
    map = np.divide(map,sum)
    


# if multiple "pixels" have the same probability, we choose the one that is closest to the position of the robot
def multiple_highest_prob_with_same_value(pos_robot,indices):

    # save estimated position of robot as an array
    pos_robot_x = pos_robot[0].item()
    pos_robot_y = pos_robot[1].item()
    point = np.array([pos_robot_x, pos_robot_y])

    # put values of pos with the same highest prob in a table, table[0] -> x, table[1] -> 1
    table = np.array(indices).tolist()

    # Transpose the table array
    table_array = np.array(table).T

    # Calculate Euclidean distances
    distances = np.linalg.norm(table_array - point, axis=1)

    # Find the index of the minimum distance
    closest_index = np.argmin(distances)
    X_ROBOT = table[0][closest_index] 
    Y_ROBOT = table[1][closest_index]

    return X_ROBOT,Y_ROBOT


def filtered_pos_robot():
    # Find indices where the maximum value occurs in map
    indices = np.where(map == map.max())
    # Find indices where the maximum value occurs in map_estimate_robot
    pos_robot = np.where(map_estimate_robot == map_estimate_robot.max())
    
    # Check if there is a single pair of coordinates in indices
    if (np.size(indices)==2): 
        # If there is only one maximum, assign X_ROBOT and Y_ROBOT directly
        X_ROBOT = indices[0].item()
        Y_ROBOT = indices[1].item()
    else:
        # If there are multiple maxima, use a function to resolve the conflict
        X_ROBOT, Y_ROBOT = multiple_highest_prob_with_same_value(pos_robot,indices)
    
    # Return the X and Y coordinates of the robot
    return X_ROBOT,Y_ROBOT


def markov(x_robot,y_robot,x_CV,y_CV,confindence_CV,first_step):
    global map

    # Initialize local variables
    x_filtered_pos_robot = 0
    y_filtered_pos_robot = 0

    # take integer value (rounded down)
    x_robot = np.int64(x_robot)
    y_robot = np.int64(y_robot)
    x_CV = np.int64(x_CV)
    y_CV = np.int64(y_CV)
    
    
    estimate_robot(x_robot,y_robot)
    estimate_CV(x_CV,y_CV,confindence_CV)
    multiply_maps()
    normalize_map()
    x_filtered_pos_robot, y_filtered_pos_robot = filtered_pos_robot()

    # if the distance between the x and y position given by the robot and 
    # the CV are different by more than 3 "pixels",
    # which means that none of the "pixels" of the map_estimate_robot and 
    # #map_estimate_CV overlap (the resulting multiplied map is empty),
    # we take the position given by CV as the filtered position value.
    # Also, if it is the first iteration of the Markov filter, we take the position given by CV as the filtered position value.
    if ((abs(x_CV-x_robot) >= 3) or (abs(x_CV-x_robot) >= 3) or first_step):
        x_filtered_pos_robot = x_CV
        y_filtered_pos_robot = y_CV
        #update map
        map[x_filtered_pos_robot][y_filtered_pos_robot] = P_HIT
        neighbouring_pixels(x_filtered_pos_robot,y_filtered_pos_robot,P_MISS,map)

    
    return x_filtered_pos_robot, y_filtered_pos_robot
