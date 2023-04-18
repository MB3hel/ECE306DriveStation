# ECE306 Drive Station

## Data format

*Note: Not all axes and buttons are sent. Only the indicated ones.*

```py
# Data format:
# ^[KEY]C[LX][LY][RX][RY][A][B][X][Y]
#   Each axis's (LX, LY, RX, RY) value is sent as a single character
#   Value is from 32 to 95 (64 values) where 32 = -100% and 95 = 100%
#   0% = 64 = ASCII @
#   
#   Each button's value is sent as a single character
#   T = True = Pressed. F = False = Not Pressed
```

- Each message above is sent in its own TCP packet or UDP datagram (depending on drive station mode).
- Note that the axis value may include a '^' symbol (ASCII 96). Make sure your parser can handle this. Use the fact that you know the size of the packet / datagram to avoid searching for '^' during parsing. Just use '^[KEY]` to validate the message is yours.

## Building and Running

First, make sure python3 is installed. On windows, the executable name may be `python` not `python3`.


**Create a Virtual Environment**
```sh
python3 -m venv env
```

**Activate the environment**

- On Windows (powershell)
    ```sh
    .\env\Scripts\Activate.Ps1
    ```

- On Windows (cmd)
    ```sh
    env\Scripts\activate.bat
    ```

- On Linux or macOS (or Git Bash in Windows)
    ```sh
    source env/bin/activate
    ```

**Install Required Libraries**
```sh
python -m pip install -r requirements.txt
```

**Compiling UI and Resource Files**

```sh
python compile.py
```

**Running**

```sh
python src/main.py
```


## Packaging

```sh
rm -r build/
rm -r dist/
pyinstaller windows.spec
```

Exe will be in `dist/`