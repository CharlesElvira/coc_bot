import subprocess
import random
import os
import re
import time
import pyautogui
import pygetwindow as gw


class ADBError(Exception):
    """Custom exception for ADB-related errors"""
    pass

def check_adb_connection():
    """Check if ADB is working and devices are connected"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
        output = result.stdout.strip()

        # Parse device list
        lines = output.split('\n')[1:]  # Skip header line
        connected_devices = [line.strip() for line in lines if line.strip() and not line.strip().endswith('offline')]

        return len(connected_devices) > 0, output
    except Exception as e:
        return False, str(e)

def recover_adb_connection():
    """Attempt to recover ADB connection by restarting the server"""
    print("ADB connection issue detected. Attempting recovery...")

    try:
        # Kill ADB server
        print("Killing ADB server...")
        subprocess.run(['adb', 'kill-server'], capture_output=True, timeout=10)
        time.sleep(2)

        # Start ADB server
        print("Starting ADB server...")
        subprocess.run(['adb', 'start-server'], capture_output=True, timeout=10)
        time.sleep(3)

        # Check devices again
        is_connected, output = check_adb_connection()
        print(f"ADB devices output: {output}")

        if is_connected:
            print("ADB connection recovered successfully!")
            return True
        else:
            raise ADBError("BlueStacks is not running or ADB debug bridge is not working on BlueStacks. "
                          "Please ensure BlueStacks is running and ADB debugging is enabled.")

    except subprocess.TimeoutExpired:
        raise ADBError("ADB commands timed out. Please check your ADB installation.")
    except Exception as e:
        raise ADBError(f"Failed to recover ADB connection: {str(e)}")

def ensure_adb_connection():
    """Ensure ADB connection is working, attempt recovery if needed"""
    is_connected, output = check_adb_connection()

    if not is_connected:
        recover_adb_connection()
        # Double-check after recovery
        is_connected, output = check_adb_connection()
        if not is_connected:
            raise ADBError("ADB connection could not be established after recovery attempt.")

def adb_tap(x, y, jitter=1):
    """
    Sends a tap command via ADB at (x, y) with an added random jitter.
    """
    jitter_x = random.randint(-jitter, jitter)
    jitter_y = random.randint(-jitter, jitter)
    new_x, new_y = x + jitter_x, y + jitter_y
    print(f"adb tap: {new_x}, {new_y} (jitter: {jitter_x}, {jitter_y})")
    cmd = f"adb shell input tap {new_x} {new_y}"

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"ADB command failed: {e}")
        print("Attempting ADB recovery...")
        recover_adb_connection()
        # Retry the command after recovery
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise ADBError(f"ADB tap failed even after recovery: {result.stderr}")

def capture_screen(filename="screen.png"):
    """Capture a screenshot from the device using ADB."""
    try:
        with open(filename, "wb") as f:
            result = subprocess.run("adb exec-out screencap -p", shell=True, stdout=f, stderr=subprocess.PIPE, timeout=15)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, "adb exec-out screencap -p", result.stderr)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Screen capture failed: {e}")
        print("Attempting ADB recovery...")
        recover_adb_connection()
        # Retry the command after recovery
        with open(filename, "wb") as f:
            result = subprocess.run("adb exec-out screencap -p", shell=True, stdout=f, stderr=subprocess.PIPE, timeout=15)
            if result.returncode != 0:
                raise ADBError(f"Screen capture failed even after recovery: {result.stderr}")

def get_screen_size():
    """Get actual device screen size"""
    try:
        result = subprocess.run(['adb', 'shell', 'wm', 'size'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, 'adb shell wm size', result.stderr)

        match = re.search(r'(\d+)x(\d+)', result.stdout)
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            return width, height
        else:
            print("Could not parse screen size from ADB output, using default")
            return 1080, 2400  # Default fallback

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Get screen size failed: {e}")
        print("Attempting ADB recovery...")
        recover_adb_connection()
        # Retry the command after recovery
        try:
            result = subprocess.run(['adb', 'shell', 'wm', 'size'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise ADBError(f"Get screen size failed even after recovery: {result.stderr}")

            match = re.search(r'(\d+)x(\d+)', result.stdout)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
                return width, height
            else:
                print("Could not parse screen size after recovery, using default")
                return 1080, 2400  # Default fallback
        except Exception:
            print("Screen size detection failed completely, using default")
            return 1080, 2400  # Default fallback

def zoom_out():
    """
    Zoom out using BlueStacks keyboard shortcut (Ctrl+-) sent directly to window
    """
    try:
        if pyautogui and gw:
            # Find and activate BlueStacks window
            bluestacks_windows = gw.getWindowsWithTitle("BlueStacks App Player")
            if not bluestacks_windows:
                bluestacks_windows = gw.getWindowsWithTitle("Clash of Clans")

            if bluestacks_windows:
                bluestacks_windows[0].activate()
                time.sleep(0.1)  # Brief delay to ensure window is focused

            # Send Ctrl+- keyboard shortcut directly
            pyautogui.hotkey('ctrl', 'minus')
            print("Zoomed out using Ctrl+-")
        else:
            print("pyautogui not available, falling back to ADB method")
            # Fallback to ADB keyevent approach
            subprocess.run(['adb', 'shell', 'input', 'keyevent', '113', '69'],
                          capture_output=True, text=True, timeout=10)
            print("Zoomed out using ADB fallback")
    except Exception as e:
        print(f"Zoom out failed: {e}")
        raise ADBError(f"Zoom out failed: {e}")

def zoom_in():
    """
    Zoom in using BlueStacks keyboard shortcut (Ctrl++) sent directly to window
    """
    try:
        if pyautogui and gw:
            # Find and activate BlueStacks window
            bluestacks_windows = gw.getWindowsWithTitle("BlueStacks App Player")
            if not bluestacks_windows:
                bluestacks_windows = gw.getWindowsWithTitle("Clash of Clans")

            if bluestacks_windows:
                bluestacks_windows[0].activate()
                time.sleep(0.1)  # Brief delay to ensure window is focused

            # Send Ctrl++ keyboard shortcut directly (Ctrl + Plus)
            pyautogui.hotkey('ctrl', 'plus')
            print("Zoomed in using Ctrl++")
        else:
            print("pyautogui not available, falling back to ADB method")
            # Fallback to ADB keyevent approach
            subprocess.run(['adb', 'shell', 'input', 'keyevent', '113', '59', '70'],
                          capture_output=True, text=True, timeout=10)
            print("Zoomed in using ADB fallback")
    except Exception as e:
        print(f"Zoom in failed: {e}")
        raise ADBError(f"Zoom in failed: {e}")
