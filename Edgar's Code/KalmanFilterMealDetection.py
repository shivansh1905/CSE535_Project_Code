"""
This program attempts to use provided CGM data to run a Kalman filter based meal detection 
algorithm as discussed in this article: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4713125/#FD4
"""

import scipy.io 
import math 
import csv

mat = scipy.io.loadmat('InsulinGlucoseData2.mat')
numCGM = mat['numCGM']

# Equation 8 - Calculating basal plasma glucose concentration G_b based on input paramater k
# representing the time i.e each sample of CGM data 
def G_b(k):
    h = 5 # Sampling time = 5 minutes
    l = 30 # Length of window used to calculate G_b

    range = (2 * l) / h
    result = 0
    if k < range:
        result = 100
    else:
        start = int(k - range + 1)
        end = k - l / h
        while start <= end:
            result += numCGM[0][start]
            start += 1
        result *= h / l
    
    return result

# Unscented Kalman Filter Equations

# Equation 9 - A non-linear state space model using equation 8
def nonLinearStateSpaceModelX(k):
    return G_b(k - 1)

def nonLinearStateSpaceModelY(k):
    return G_b(k)

# Equation 10
L = 2 # Demension of x vector
alpha = 1
beta = 2
kappa = 0

mu = math.pow(alpha, 2)* (L + kappa)

# Scalar weights
scalarWeightW0x = mu / (L + mu)
scalarWeightW0y = mu / (L + mu) + (1 - math.pow(alpha, 2) + beta)

# Equation 11 - Calculating Sigma-point vectors
def sigmaPointVectors(k, index):
    if k < 0: return 0

    estimatedX = nonLinearStateSpaceModelX(k)
    gamma = math.sqrt(L + mu)
    if index == 0:
        return estimatedX 
    elif index < index + L:
        return estimatedX + gamma * numCGM[0][k]
    else:
        return estimatedX - gamma * numCGM[0][k]


# Equation 12 - Calculating prior sigma-points estimations
def priorSigmaPointEstimations(k, index):
    if k == 0:
        return
    
    x_difference = sigmaPointVectors(k - 1, index)
    return min(math.pow(x_difference, 1), x_difference)

# Equation 13 - Calculating prior state estimations
def priorStateEstimation(k):
    priorState = 0
    scalarWeightWix = 1 / (2 * (L + mu))
    for i in range(2*L):
        if i == 0:  
            priorState += scalarWeightW0x * priorSigmaPointEstimations(k, i)
        else:
            priorState += scalarWeightWix * priorSigmaPointEstimations(k, i)
    return priorState

# Equation 14 - Calculating covariance matrix
def covarianceMatrix(k):
    covariance = 0
    scalarWeightWiy = 1 / (2 * (L + mu))
    for i in range(2*L):
        if i == 0:  
            covariance += scalarWeightW0y * (priorSigmaPointEstimations(k, i) - priorStateEstimation(k)) * math.pow(priorSigmaPointEstimations(k, i) - priorStateEstimation(k), 1)
        else:
            covariance += scalarWeightWiy * (priorSigmaPointEstimations(k, i) - priorStateEstimation(k)) * math.pow(priorSigmaPointEstimations(k, i) - priorStateEstimation(k), 1) 
        return covariance

# Equation 15 - Calculating prior output sigma points
def priorOutputSigmaPoints(k, index):
    return priorSigmaPointEstimations(k, index)

# Equation 16 - Calculating output sigma points
def outputSigmaPoints(k):
    priorOutputs = 0
    scalarWeightWix = 1 / (2 * (L + mu))
    for i in range(2*L):
        if i == 0:  
            priorOutputs += scalarWeightW0x * priorOutputSigmaPoints(k, i)
        else:
            priorOutputs += scalarWeightWix * priorOutputSigmaPoints(k, i)
    return priorOutputs

# Equation 17 - Calulating innovation covariance
def innovationCovariance(k):
    innovationCovariance = 0
    scalarWeightWiy = 1 / (2 * (L + mu))
    for i in range(2*L):
        if i == 0:  
            innovationCovariance += scalarWeightW0y * (priorOutputSigmaPoints(k, i) - outputSigmaPoints(k)) * math.pow(priorOutputSigmaPoints(k, i) - outputSigmaPoints(k), 1)
        else:
            innovationCovariance += scalarWeightWiy * (priorOutputSigmaPoints(k, i) - outputSigmaPoints(k)) * math.pow(priorOutputSigmaPoints(k, i) - outputSigmaPoints(k), 1) 
    
    return innovationCovariance   

# Equation 18 - Calculating cross-covariance matrices
def crossCovariance(k):
    crossCovariance = 0
    scalarWeightWiy = 1 / (2 * (L + mu))
    for i in range(2*L):
        if i == 0:  
            crossCovariance += scalarWeightW0y * (priorOutputSigmaPoints(k, i) - outputSigmaPoints(k)) * math.pow(priorOutputSigmaPoints(k, i) - outputSigmaPoints(k), 1)
        else:
            crossCovariance += scalarWeightWiy * (priorSigmaPointEstimations(k, i) - outputSigmaPoints(k)) * math.pow(priorOutputSigmaPoints(k, i) - outputSigmaPoints(k), 1) 
    
    return crossCovariance

# Equation 19 - Calculating Kalman filter gain
def kalmanFilterGain(k):
    return crossCovariance(k) * (1 / innovationCovariance(k))

# Equation 20 - Calculating updated state vector estimation 
def stateVectorEstimation(k):
    return priorStateEstimation(k) + kalmanFilterGain(k) * (nonLinearStateSpaceModelY(k) - outputSigmaPoints(k))

# Equation 21 - Calculating updated covariance matrix
def covariance(k):
    return covarianceMatrix(k) - (kalmanFilterGain(k) * innovationCovariance(k) * math.pow(kalmanFilterGain(k), 1))
    

if __name__ == "__main__":
    # Run Kalmin filter algorithm on each element of the given CGM data and write results into a file
    filename = "resultKalmanFilter/result.csv"
    csvfile = open(filename, 'w')

    columns = ['Index', 'Computed Value']
    # creating a csv writer object  
    writer = csv.writer(csvfile)
    writer.writerow(columns)   
    for i in range(len(numCGM[0])):
        data = covariance(i + 1)
        row = [str(i), str(data)]
        # writing the results into csv file 
        writer.writerow(row)
    csvfile.close()  
                
