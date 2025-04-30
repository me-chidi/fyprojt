FYPROJT
-------

My final year project. 
A webapp that pulls data from an Arduino via serial json and also writes to it with the same method.

Overview
--------

FYPROJT is a zApp (Zigbee app) that facilitates the control and monitoring of Zigbee-controlled street lights (nodes). Connected to an arduino that serves as the interface between the `flask` webserver and the nodes, real time data pertaining to the status of the nodes are pulled from the Arduino and displayed through the browser. The nodes can also be turned on/off individually or all at once with the click of a button. 

Usage Instructions
------------------

This app is intended for use on a local machine with at most 100 nodes connected. It is a light app for light usage.

## Installation:

After making a pull request, use pipenv to install dependencies

```bash
pipenv install
```
also install the --dev dependency `pyngrok` for "external" use
```bash
pipenv install --dev pyngrok
```

Then call
```bash
flask run
```

By default it should be served on `https://localhost:5000` or `https://127.0.0.1:5000`. You will be required to set a username and password before logging in.

If you desire to access the server from another machine other that the machine it is hosted on change the `START_NGROK` variable to `True` and access it from the "Ngrok Tunnel" link provided in the terminal. You may familiarize yourself with the use of ngrok [here](https://ngrok.com/docs/getting-started/). The pyngrok module was used here so you would only need to set a few environmental variables for authentication.

### Nominal use:
Plug in an Arduino that outputs a nested json an example can be seen in the [test_pyduino.py](https://github.com/me-chidi/fyprojt/blob/main/tests/test_pyduino.py) module in the form of a variable called `json_data` used for tests. The server displays realtime changes without reloading the page.

### Not-Nominal use:
Although ideally made to control street lights, the app could be used to control and monitor other devices with a little tweak. Provided they are interfaced with an arduino and accept serial commands.     
