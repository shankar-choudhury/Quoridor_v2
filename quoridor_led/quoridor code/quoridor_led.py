import pigpio
from time import sleep

pi = pigpio.pi()

_RED_PIN = 19   
_GREEN_PIN = 26   
_BLUE_PIN = 13    

# Constants
_PWM_FREQUENCY = 800  # Hz
_FLASH_DURATION = 0.3  # seconds
_PAUSE_DURATION = 0.3  # seconds


for pin in [_RED_PIN, _GREEN_PIN, _BLUE_PIN]:
    pi.set_PWM_frequency(pin, _PWM_FREQUENCY)

def _turn_off():
    pi.set_PWM_dutycycle(_RED_PIN, 0)
    pi.set_PWM_dutycycle(_GREEN_PIN, 0)
    pi.set_PWM_dutycycle(_BLUE_PIN, 0)

def _set_color(red, green, blue):
    pi.set_PWM_dutycycle(_RED_PIN, red)
    pi.set_PWM_dutycycle(_GREEN_PIN, green)
    pi.set_PWM_dutycycle(_BLUE_PIN, blue)

def _set_red():
    _set_color(255, 0, 0)

def _set_green():
    _set_color(0, 255, 0)

def _flash(color_func, times=1, flash_duration=_FLASH_DURATION, pause_duration=_PAUSE_DURATION):
    """
    Internal flash implementation (private)
    :param color_func: Function to set the color (_set_red or _set_green)
    :param times: Number of flashes
    :param flash_duration: How long each flash lasts
    :param pause_duration: How long between flashes
    """
    for i in range(times):
        color_func()
        sleep(flash_duration)
        _turn_off()
        if i < times - 1: 
            sleep(pause_duration)

def players_turn(is_players_turn):
    """
    Set LED color based on whose turn it is
    :param is_players_turn: True for player's turn (green), False for opponent's turn (red)
    """
    if is_players_turn:
        _set_green()
    else:
        _set_red()

def valid_move(is_valid):
    """
    Provide visual feedback about move validity
    :param is_valid: True for valid move (green flash), False for invalid move (red flash)
    """
    if is_valid:
        _flash(_set_green, times=2)
    else:
        was_green = pi.get_PWM_dutycycle(_GREEN_PIN) > 0
        _flash(_set_red, times=2)
        _set_green() if was_green else _set_red()

def win_lose(did_win):
    """
    Provide win/lose feedback
    :param did_win: True for win (green flash), False for lose (red flash)
    """
    if did_win:
        _set_green()
        _flash(_set_green, times=3)
    else:
        _set_red()
        _flash(_set_red, times=3)

def cleanup():
    _turn_off()
    pi.stop()

# Trial methods
if __name__ == "__main__":
    try:
        print("Player's turn (green)")
        players_turn(True)
        sleep(2)
        
        print("Opponent's turn (red)")
        players_turn(False)
        sleep(2)
        
        print("Valid move (green flash twice)")
        players_turn(True)
        valid_move(True)
        sleep(2)
        
        print("Invalid move (red flash twice then back to green)")
        players_turn(True)
        valid_move(False)
        sleep(2)
        
        print("Win (green flash three times)")
        win_lose(True)
        sleep(2)
        
        print("Lose (red flash three times)")
        win_lose(False)
        sleep(2)
        
    finally:
        cleanup()
