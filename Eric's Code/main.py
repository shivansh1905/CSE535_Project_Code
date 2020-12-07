# Eric Bell

import math
import random
import time

import numpy as np, pandas as pd
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import pmdarima as pm
from statsmodels.tsa.arima_model import ARIMA
import scipy.stats as stats

df = pd.read_csv('retimedData.csv', names=['time', 'actBolus', 'value'])



# 2 Days of training
trainAmount = 60*24*2
# 75 Minutes for a test
testAmount = 30

fig1, axs1 = plt.subplots(10, 1, figsize=(6, 6 * 10))

axs1[0].set_title("Bolus 1st Difference")
axs1[1].set_title("Bolus 2nd Difference")
axs1[2].set_title("Bolus Prediction")
axs1[3].set_title("Sum Scatter")
axs1[4].set_title("No Bolus 1st Difference")
axs1[5].set_title("No Bolus 2nd Difference")
axs1[6].set_title("No Bolus Prediction")
axs1[7].set_title("No Sum Scatter")
axs1[8].set_title("Bolus Data")
axs1[9].set_title("Prediction")

bolusArray = []
div1Array = []
div2Array = []
forcastAvg = []


for i in range(100):
    print(i)
    # Randomly choose some position in the data
    t0 = time.time()
    randOffset = random.randint(0, 200000)

    train = df.value[randOffset:randOffset + trainAmount]
    bolusTrain = df.actBolus[randOffset:randOffset + trainAmount]
    test = df.value[randOffset + trainAmount:randOffset + trainAmount + testAmount]
    bolusGnd = df.actBolus[randOffset + trainAmount:randOffset + trainAmount + testAmount]

    # Reindex and plot the bolus values
    # Also find the peaks of the bolus
    # If there were no peaks, then that bolus is not applicble to the current time frame
    # Either the food already happened and the bolus started or the food will happen outside of the time frame
    bolusGnd.index = pd.RangeIndex(len(bolusGnd.index))
    axs1[8].plot(bolusGnd, label=str(i))
    peaks, _ = find_peaks(bolusGnd, height=.2)
    axs1[8].plot(peaks, bolusGnd.values[peaks], "x")

    hasBolus = True

    if len(peaks) > 0:
        if 0 in peaks or testAmount - 1 in peaks:
            if len(peaks) == 1:
                hasBolus = False
    else:
        hasBolus = False

    try:
        # Use 4 data points, no differencing, 2nd degree moving average model
        # No sesonality since the data did not look seasonal
        model = ARIMA(train, order=(4,0,2))
        fitted = model.fit(disp=0)
        # print(fitted.summary())
    except Exception:
        print("Failure with model")
        continue

    # Forecast
    fc, se, conf = fitted.forecast(testAmount, alpha=.05)  # 95% conf

    # Make as pandas series
    fc_series = pd.Series(fc, index=test.index)

    # Create first and second order differencing from the forcast
    div1 = fc_series.diff()
    div2 = fc_series.diff().diff()

    # Reindex Values
    div1.index = pd.RangeIndex(len(div1.index))
    div2.index = pd.RangeIndex(len(div2.index))
    fc_series.index = pd.RangeIndex(len(fc_series.index))
    test.index = pd.RangeIndex(len(test.index))

    lastD = div2.values[0]
    crossedZero = []
    div2Sum = 0

    # Find all of the zero crossing points and store the direction
    # -1 is positive to negative
    # 1 is negative to positive
    for d in div2:
        if math.isnan(d):
            continue

        if d > 0 and lastD < 0:
            crossedZero.append(1)
        elif d < 0 and lastD > 0:
            crossedZero.append(-1)

        div2Sum += d
        lastD = d


    lastF = div1.values[0]
    div1CrossedZero = []
    div1Sum = 0

    # Find all of the zero crossing points and store the direction
    # -1 is positive to negative
    # 1 is negative to positive
    for d in div1:
        if math.isnan(d):
            continue

        if d > 0 and lastF < 0:
            div1CrossedZero.append(1)
        elif d < 0 and lastF > 0:
            div1CrossedZero.append(-1)

        div1Sum += d
        lastF = d

    prediction = 0
    forcastAverage = np.average(fc_series.values)
    div1Average = np.average(div1.values[1:])
    div2Average = np.average(div2.values[2:])

    bolusArray.append(int(hasBolus == True))
    div1Array.append(div1Average)
    div2Array.append(div2Average)
    forcastAvg.append(forcastAvg)

    # Create a prediction
    prediction += min(max(((-2 * (div2Average)) + (div1Average)),0),1)

    print("\n\n---------------------")
    print("Prediction Percentage (0-No Bolus, 1-Bolus): {0}".format(prediction))
    print(div1CrossedZero)
    print(crossedZero)
    print(div1.values[-1])
    if hasBolus:
        axs1[0].plot(div1, label=str(i))
        axs1[1].plot(div2, label=str(i))
        axs1[2].plot(fc_series, label="FC" + str(i))
        # axs1[2].plot(test, label="ACT" + str(i))
        print("Has Bolus - Div1 Avg: {0}\tDiv2 Avg: {1}".format(div1Average, div2Average))
        axs1[3].scatter(div1Average, div2Average)
        axs1[9].plot(1, prediction, "x")
    else:
        axs1[4].plot(div1, label=str(i))
        axs1[5].plot(div2, label=str(i))
        axs1[6].plot(fc_series, label=str(i))
        print("No Bolus - Div1 Avg: {0}\tDiv2 Avg: {1}".format(div1Average, div2Average))
        axs1[7].scatter(div1Average, div2Average)
        axs1[9].plot(0, prediction, "x")
    t1 = time.time() - t0
    print("Runtime: {0}".format(t1))
    print("--------------------------")


axs1[2].legend()
plt.show()


# Double check for correlation between the bolus and the 1st and 2nd difference
print(stats.pointbiserialr(bolusArray, div1Array))
print(stats.pointbiserialr(bolusArray, div2Array))

a = []

for i,j in zip(div1Array, div2Array):
    a.append(i - (2*j))

print(stats.pointbiserialr(bolusArray, a))