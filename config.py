import serial

#a = serial.Serial('COM3', 9600)

#parse the data into a json like this
njson = {'nodes': [['1', 'ON', 'MID'],
                 ['2', 'ON', 'LOW'],
                 ['3', 'ON', 'LOW'],
                 ['4', 'OFF', 'HIGH'], 
                 ['5', 'ON', 'HIGH']]
}