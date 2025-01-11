# ESP32 Tournament: Rock Paper Scissors

A two-player Rock Paper Scissors tournament system using two ESP32 microcontrollers and a computer-based GUI for game display and scoring.

## Features
- Two-player real-time gameplay using ESP32 microcontrollers
- Computer-based GUI for game display and tournament tracking
- LED indicators for game status and player moves
- Real-time score tracking and game history
- Flask server for handling game logic and communication
- No OLED displays needed - all game information shown on computer GUI

## Hardware Requirements
- 2x ESP32 development boards (one for each player)
- 1x Breadboards
- 2x LEDs
- 2x 220Ω resistors (for LEDs)
- Jumper wires
- USB cables for ESP32 programming and power

## Software Requirements
### Computer
- Python 3.8 or higher
- Flask web server
- Tkinter GUI library (included with Python)
- See requirements.txt for complete Python dependencies

### ESP32
- Arduino IDE or PlatformIO
- ESP32 board support package
- Required Arduino Libraries:
  - WiFi
  - ArduinoJson

## Installation

1. Clone this repository:
```sh
git clone https://github.com/PaoloStillittano/esp32-rps-tournament.git
cd esp32-rps-tournament
```

2. Install Python dependencies:
```sh
pip install -r requirements.txt
```

3. Configure ESP32 devices:
   - Open `player1/` and `player2/` in Arduino IDE or PlatformIO
   - Update WiFi credentials in the respective config files
   - Upload code to each ESP32 device
   - Note the IP addresses assigned to each device

4. Hardware Setup:
   - Connect LEDs and buttons according to the provided schematic
   - Each ESP32 should have:
     - 1 LEDs for move indication (Rock, Paper, Scissors)
     - Common ground connection

## Usage

1. Start the Flask server:
```sh
python server.py
```

2. The GUI will automatically launch and display the game interface

3. On each ESP32:
   - LED indicators will show the current selection
   - Final move is locked in after a short delay

4. The GUI will:
   - Display current game state
   - Show player moves
   - Track tournament score
   - Record game history

## Project Structure
```
esp32-rps-tournament/
├── main.py            # Flask server, game logic and Tkinter GUI implementation
├── requirements.txt   # Python dependencies
├── player1/           # Code for first ESP32
├── player2/           # Code for second ESP32
└── README.md
```

## Troubleshooting
- Ensure both ESP32s are connected to the same WiFi network as the computer
- Check LED connections if move indicators aren't working
- Verify server IP address configuration in ESP32 code
- Ensure all required Python packages are installed

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements
- The ESP32 community for their excellent libraries and resources
- Flask and Tkinter communities for their documentation
- Original rock-paper-scissors game concept