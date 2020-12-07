from pandas import read_csv
from pandas import DataFrame
from pandas import concat
import numpy
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM

def series_to_supervised(data, n_in=1, n_out=1):
	n_vars = 1 if type(data) is list else data.shape[1]
	df = DataFrame(data)
	cols, names = list(), list()
	for i in range(n_in, 0, -1):
		cols.append(df.shift(i))
		names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
	for i in range(0, n_out):
		cols.append(df.shift(-i))
		if i == 0:
			names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
		else:
			names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
	agg = concat(cols, axis=1)
	agg.dropna(inplace=True)
	agg.columns = names
	return agg

window = 6
dataframe = read_csv('data.csv', header=None, names=['Bolus', 'CGM'])
dataframe.loc[dataframe['Bolus'] < 1, 'Bolus'] = 0
dataframe.loc[dataframe['Bolus'] >= 1, 'Bolus'] = 1
dataset = dataframe.values
dataset = dataset.astype('float32')
dataset = series_to_supervised(dataset, window, 1)
dataset.drop(dataset.columns[-1], axis=1, inplace=True)

values = dataset.values
train_size = int(len(values) * 0.8)
train, test = values[0:train_size,:], values[train_size:len(values),:]
train_X, train_y = train[:, :-1], train[:, -1]
test_X, test_y = test[:, :-1], test[:, -1]
train_X = train_X.reshape((train_X.shape[0], window, 2))
test_X = test_X.reshape((test_X.shape[0], window, 2))
print(train_X.shape, train_y.shape, test_X.shape, test_y.shape)

model = Sequential()
model.add(LSTM(16))
model.add(Dense(1, activation='sigmoid'))
model.compile(loss='mae', optimizer='adam', metrics=['accuracy'])
history = model.fit(train_X, train_y, epochs=10, batch_size=1, validation_data=(test_X, test_y), verbose=2, shuffle=False)
yhat = model.predict(train_X).flatten()
print(yhat)