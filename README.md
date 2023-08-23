# Contextual Web API

Author: Sharhad Bashar<br>
Language: `Python`<br>
Version: `v3.9.16`<br>

To install all the required libraries, run `pip install -r requirements.txt`<br>
On first run, setup directories and download required files.<br>
To do so run this command from the python directory: `python setup.py`<br>

To Run the API:
1. `uvicorn main:app --reload` 
2. `uvicorn main:app --workers 4`

More information on the API and how to setup and operate can be found in this [document](https://audiovalley.atlassian.net/wiki/spaces/PPIQ/pages/3648651265/Contextual+API+Data+Models)<br>

If you get the error:<br>
`[Errno 48] Address already in use`<br>
Use `ps -fA | grep python`<br>
To find the port in use and kill it using<br>
`kill -9 <PORT_NUMBER>`

For MAC M1 chip:
If you get `ffmpeg` error, use `eval "$(/opt/homebrew/bin/brew shellenv)"` to fix

For any questions, feel free to email or slack Sharhad Bashar or Henry Visotski<br>