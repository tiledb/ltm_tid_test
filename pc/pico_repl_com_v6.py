import argparse
import os
import time
from datetime import datetime
import serial
import serial.tools.list_ports
import sys
import select


CTRL_A = b'\x01'  # enter raw REPL
CTRL_B = b'\x02'  # exit raw REPL
CTRL_C = b'\x03'  # interrupt
CTRL_D = b'\x04'  # execute (end of paste)

def wait_for(ser, expected, timeout=5):
    deadline = time.time() + timeout
    buffer = b""
    while time.time() < deadline:
        if ser.in_waiting:
            buffer += ser.read(ser.in_waiting)
            if expected in buffer:
                return buffer
        time.sleep(0.01)
    return buffer

def enter_raw_repl(ser):
    ser.write(b'\r' + CTRL_C*2)  # interrupt any running program
    time.sleep(0.1)
    ser.write(b'\r' + CTRL_A)    # enter raw REPL
    time.sleep(0.1)
    wait_for(ser, b'raw REPL; CTRL-B to exit\r\n>')

def exit_raw_repl(ser):
    ser.write(CTRL_B)
    time.sleep(0.1)

def send_raw_code(ser, code, timeout=10):
    # Clear input buffer first
    while ser.in_waiting:
        ser.read(ser.in_waiting)

    ser.write(code.encode('utf-8'))
    ser.write(CTRL_D)  # Ctrl-D to execute
    out = wait_for(ser, b'OK', timeout=timeout)
    return out

def upload_file(ser, local_path, remote_filename, log_file):
    with open(local_path, 'r', encoding='utf-8') as f:
        content = f.read()

    code = f"f = open('{remote_filename}', 'w')\n"
    for line in content.splitlines():
        line_escaped = line.replace('\\', '\\\\').replace("'", "\\'")
        code += f"f.write('{line_escaped}\\n')\n"
    code += "f.close()\n"

    log_and_print(log_file, f"[INFO] Uploading {local_path} as {remote_filename}\n")
    send_raw_code(ser, code)
    log_and_print(log_file, f"[INFO] Uploaded {local_path}\n")

def log_and_print(log_file, message):
    from datetime import datetime

    # Get current time and calculate elapsed time since program start
    current_time = datetime.now()
    timestamp_raw = current_time.strftime("%Y-%m-%d\t%H-%M-%S")
    
    # Calculate elapsed time (seconds since program start)
    if not hasattr(log_and_print, 'start_time'):
        log_and_print.start_time = time.time()
    elapsed = time.time() - log_and_print.start_time
    elapsed_str = f"{elapsed:.3f}"
    
    # Format the timestamp with elapsed time
    timestamp_with_elapsed = f"{timestamp_raw}\t{elapsed_str}"
    timestamp_colored = f"\033[96m{timestamp_with_elapsed}\033[0m"  # Cyan in terminal

    # Apply timestamps line by line
    lines = message.rstrip('\n').split('\n')

    # Process lines for terminal and file separately
    terminal_lines = []
    file_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        
        # Check if line starts and ends with "--"
        if stripped_line.startswith("--") and stripped_line.endswith("--"):
            # For terminal: remove the leading and trailing "--" (and any surrounding spaces)
            # Remove exactly 2 dashes from start and end
            clean_line = f"\033[96m{stripped_line[2:-2].strip()}\033[0m"
            terminal_lines.append(f"{timestamp_colored}\t{clean_line}")
            # For file: don't write this line at all
        else:
            # Regular line - show in both terminal and file
            terminal_lines.append(f"{timestamp_colored}\t{line}")
            file_lines.append(f"{timestamp_with_elapsed}\t{line}")

    print('\n'.join(terminal_lines), end='\n')
    if file_lines:  # Only write to file if there are lines after filtering
        with open(log_file, 'a') as f:
            f.write('\n'.join(file_lines) + '\n')

def list_files_on_pico(ser, log_file, path="/"):
    log_and_print(log_file, f"\n[INFO] Listing files on Pico in '{path}':\n")
    # Use a special marker to find start and end of output
    marker_start = "<<<START>>>"
    marker_end = "<<<END>>>"
    code = (
        f"print('{marker_start}')\n"
        f"import os\n"
        f"files = os.listdir('{path}')\n"
        f"for f in files:\n"
        f"    print(f)\n"
        f"print('{marker_end}')\n"
    )
    send_raw_code(ser, code)

    output = b""
    deadline = time.time() + 5
    while time.time() < deadline:
        if ser.in_waiting:
            output += ser.read(ser.in_waiting)
            if marker_end.encode() in output:
                break
        else:
            time.sleep(0.1)

    try:
        text = output.decode(errors='ignore')
        start = text.find(marker_start) + len(marker_start)
        end = text.find(marker_end)
        file_list = text[start:end].strip().replace('\r', '')
        log_and_print(log_file, file_list + '\n')
    except Exception as e:
        log_and_print(log_file, f"[ERROR] Failed to parse file list output: {e}\n")

def run_script(ser, script_name, log_file, script_args=""):
    """
    Run a script on the Pico and monitor output.
    
    Key forwarding: Only 't' and 'f' keys are forwarded to the Pico.
    This allows limited interaction while preventing accidental key presses
    from interfering with the running script.
    
    Args:
        ser: Serial connection to Pico
        script_name: Name of script file to run
        log_file: Path to log file for output
        script_args: Arguments to pass to the script
    """
    log_and_print(log_file, f"[INFO] Running script '{script_name}'... (Press Ctrl+C to stop)\n")
    if script_args:
        log_and_print(log_file, f"[INFO] Script arguments: {script_args}\n")
    log_and_print(log_file, "[INFO] Key forwarding enabled: 't' and 'f' keys will be sent to Pico\n")
    
    # Create a global variable for script arguments (MicroPython compatible)
    setup_code = "import sys\n"
    if script_args:
        # Simple argument parsing - split by spaces
        args_list = script_args.split()
        escaped_args = []
        for arg in args_list:
            # Escape single quotes in arguments
            escaped_arg = arg.replace("'", "\\'")
            escaped_args.append(f"'{escaped_arg}'")
        setup_code += f"script_args = [{', '.join(escaped_args)}]\n"
    else:
        setup_code += "script_args = []\n"
    
    # Execute the script with the arguments
    code = setup_code + f"exec(open('{script_name}').read())\n"
    
    # Debug: print the code being sent
    log_and_print(log_file, f"[DEBUG] Executing code: {repr(code)}\n")
    
    # Send code without waiting for OK (for continuous scripts)
    while ser.in_waiting:
        ser.read(ser.in_waiting)
    
    ser.write(code.encode('utf-8'))
    ser.write(CTRL_D)  # Ctrl-D to execute
    
    # Wait a moment for any initial response
    time.sleep(0.5)

    try:
        while True:
            time.sleep(0.05)
            while ser.in_waiting:
                out = ser.read(ser.in_waiting).decode(errors='ignore')
                log_and_print(log_file, out)
                time.sleep(0.01)
            # ---- forward keyboard to Pico ----
            # Only forward 't' and 'f' keys to prevent accidental interference
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                if key in ('t', 'f'):
                    ser.write(key.encode())
    except KeyboardInterrupt:
        log_and_print(log_file, "\n[INFO] Ctrl+C detected.\n")
        answer = input("Stop execution on Pico and soft reset? (y/n): ").strip().lower()
        if answer == 'y':
            ser.write(b'\x03')  # Ctrl-C interrupt on Pico
            time.sleep(0.5)
            ser.write(b'\x04')  # Ctrl-D soft reset on Pico
            time.sleep(1)
            log_and_print(log_file, "[INFO] Pico soft reset done.\n")
        else:
            log_and_print(log_file, "[INFO] Script execution continues on Pico (no reset).\n")

def auto_detect_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "Pico" in p.description or "USB Serial" in p.description:
            return p.device
    return None

def main():
    parser = argparse.ArgumentParser(description="Upload libraries and run a script on Raspberry Pi Pico via REPL.")
    parser.add_argument('--port', help="COM port (e.g., COM3 or /dev/ttyACM0). Auto-detects if not specified.")
    parser.add_argument('--lib-folder', default="lib", help="Folder containing library files (default: 'lib').")
    parser.add_argument('--script', required=False, help="Main script to run (e.g., 'main.py').")
    parser.add_argument('--filename', required=False, help="Suffix for log file (e.g., 'batch_01').")
    parser.add_argument('--data-folder', default="../data", help="Folder where data would be stored (default: '../data').")
    parser.add_argument('--script-args', default="", help="Arguments to pass to the script (e.g., '--arg1 value1 --arg2 value2')")
    parser.add_argument('-m', '--monitor', action='store_true', help="Monitor the raw REPL without running or resetting the Pico.")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename_suffix = args.filename or "noname"
    
    # Create data folder if it doesn't exist
    import os
    os.makedirs(args.data_folder, exist_ok=True)
    
    log_file = os.path.join(args.data_folder, f"log_{timestamp}_{filename_suffix}.csv")

    port = args.port or auto_detect_port()
    if not port:
        print("[ERROR] Could not auto-detect Pico. Use --port.")
        return

    try:
        with serial.Serial(port, 115200, timeout=1) as ser:
            time.sleep(2)  # wait for device
            
            # Enter raw REPL for both modes
            
            if args.monitor:
                log_and_print(log_file, "[INFO] Monitoring raw REPL (no upload or run)... Press Ctrl+C to exit.\n")
                try:
                    while True:
                        if ser.in_waiting:
                            out = ser.read(ser.in_waiting).decode(errors='ignore')
                            log_and_print(log_file, out)
                        else:
                            time.sleep(0.1)
                except KeyboardInterrupt:
                    log_and_print(log_file, "\n[INFO] Monitor stopped by user.\n")
                    answer = input("Stop execution on Pico and soft reset? (y/n): ").strip().lower()
                    if answer == 'y':
                        ser.write(b'\x03')  # Ctrl-C interrupt on Pico
                        time.sleep(0.5)
                        ser.write(b'\x04')  # Ctrl-D soft reset on Pico
                        time.sleep(1)
                        log_and_print(log_file, "[INFO] Pico soft reset done.\n")
                    else:
                        log_and_print(log_file, "[INFO] Script execution continues on Pico (no reset).\n")
                finally:
                    # exit raw REPL gracefully
                    exit_raw_repl(ser)
            else:
                # Enter raw REPL for both modes
                ser.write(b'\r' + CTRL_C*2)  # interrupt any running program
                time.sleep(0.1)
                ser.write(b'\r' + CTRL_A)    # enter raw REPL
                time.sleep(0.1)
                wait_for(ser, b'raw REPL; CTRL-B to exit\r\n>')
                if not args.script:
                    print("[ERROR] --script is required unless --monitor is used.")
                    return

                list_files_on_pico(ser, log_file, "/")

                # Upload all .py files in lib-folder root (no recursion)
                if args.lib_folder is not None and os.path.exists(args.lib_folder):
                    if os.path.isdir(args.lib_folder):
                        for file in os.listdir(args.lib_folder):
                            if not file.endswith('.py'):
                                continue
                            local_path = os.path.join(args.lib_folder, file)
                            if os.path.isfile(local_path):
                                upload_file(ser, local_path, file, log_file)

                # Upload main script with its original filename (no rename)
                upload_file(ser, args.script, os.path.basename(args.script), log_file)

                # Run the uploaded main script by its filename
                run_script(ser, os.path.basename(args.script), log_file, args.script_args)

                exit_raw_repl(ser)

    except Exception as e:
        error_msg = f"[ERROR] {e}\n"
        print(error_msg)
        with open(log_file, 'a') as f:
            f.write(error_msg)

if __name__ == "__main__":
    main()