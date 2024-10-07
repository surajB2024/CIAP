import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from tkinter import END
import serial
import serial.tools.list_ports
import threading
import time
import re
import threading

class SerialUtility:
    def __init__(self, root):
        self.root = root
        self.root.title("AEPL Logger (Disconnected)")
        self.root.geometry("800x600")
        try:
            self.root.iconbitmap(r"img.ico") 
        except Exception as e:
            print(f"Error setting icon: {e}")


        self.serial_port = None
        self.log_file = None
        self.logging_active = False

        # Create menu bar
        self.create_menu()

        # Create GUI components
        self.create_widgets()

        # Continuously check for available serial ports
        self.check_ports_thread = threading.Thread(target=self.check_ports)
        self.check_ports_thread.daemon = True
        self.check_ports_thread.start()

    def create_menu(self):
        menu_bar = tk.Menu(self.root)

        # File Menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New Connection", command=self.new_connection, accelerator="Alt+N")
        file_menu.add_command(label="Duplicate Session", command=self.duplicate_session, accelerator="Alt+D")
        file_menu.add_separator()
        file_menu.add_command(label="Log", command=self.start_logging, accelerator="Ctrl+L")
        file_menu.add_command(label="View Log", command=self.view_log, accelerator="Ctrl+V")
        file_menu.add_command(label="Change Directory", command=self.change_directory, accelerator="Ctrl+D")
        file_menu.add_separator()
        file_menu.add_command(label="Disconnect", command=self.disconnect, accelerator="Alt+1")
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Alt+Q")
        file_menu.add_command(label="Exit All", command=self.exit_all, accelerator="Ctrl+Shift+X")
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Edit Menu
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Copy", command=self.copy, accelerator="Alt+C")
        edit_menu.add_command(label="Paste", command=self.paste, accelerator="Alt+V")
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        # Setup Menu
        setup_menu = tk.Menu(menu_bar, tearoff=0)
        setup_menu.add_command(label="Port Settings", command=self.port_settings)
        setup_menu.add_command(label="Macros", command=self.macros)
        menu_bar.add_cascade(label="Setup", menu=setup_menu)

        # Control Menu
        control_menu = tk.Menu(menu_bar, tearoff=0)
        control_menu.add_command(label="Start", command=self.start_logging, accelerator="Ctrl+Shift+S")
        control_menu.add_command(label="Stop", command=self.stop_logging, accelerator="Ctrl+Shift+Q")
        menu_bar.add_cascade(label="Control", menu=control_menu)

        # Windows Menu
        windows_menu = tk.Menu(menu_bar, tearoff=0)
        windows_menu.add_command(label="Minimize", command=self.root.iconify, accelerator="Ctrl+M")
        windows_menu.add_command(label="Maximize", command=self.maximize_window, accelerator="Ctrl+Shift+M")
        menu_bar.add_cascade(label="Windows", menu=windows_menu)

        # Help Menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menu_bar)

        # Bind keyboard shortcuts
        self.root.bind_all("<Alt-n>", lambda e: self.new_connection())        # Alt+N -> New Connection
        self.root.bind_all("<Alt-d>", lambda e: self.duplicate_session())     # Alt+D -> Duplicate Session
        self.root.bind_all("<Control-l>", lambda e: self.start_logging())     # Ctrl+L -> Log
        self.root.bind_all("<Control-v>", lambda e: self.view_log())          # Ctrl+V -> View Log
        self.root.bind_all("<Control-d>", lambda e: self.change_directory())  # Ctrl+D -> Change Directory
        self.root.bind_all("<Alt-1>", lambda e: self.disconnect())            # Alt+1 -> Disconnect
        self.root.bind_all("<Alt-q>", lambda e: self.root.quit())             # Alt+Q -> Exit
        self.root.bind_all("<Control-Shift-x>", lambda e: self.exit_all())    # Ctrl+Shift+X -> Exit All
        self.root.bind_all("<Alt-c>", lambda e: self.copy())                  # Alt+C -> Copy
        self.root.bind_all("<Alt-v>", lambda e: self.paste())                 # Alt+V -> Paste
        self.root.bind_all("<Control-Shift-s>", lambda e: self.start_logging()) # Ctrl+Shift+S -> Start
        self.root.bind_all("<Control-Shift-q>", lambda e: self.stop_logging()) # Ctrl+Shift+Q -> Stop
        self.root.bind_all("<Control-m>", lambda e: self.root.iconify())        # Ctrl+M -> Minimize
        self.root.bind_all("<Control-Shift-m>", lambda e: self.maximize_window()) # Ctrl+Shift+M -> Maximize


    def create_widgets(self):
        self.log_console = scrolledtext.ScrolledText(self.root, wrap=tk.NONE, bg="black", fg="white", font=("Consolas", 10))
        self.log_console.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)
        
        # Simran : 04.07.24 -- Colour coded changes
        # Suraj : 10.07.24 -- Colour coded changes
        # Define color tags for specific log flags
        self.log_console.tag_configure('ais', foreground='#0039a6')
        # self.log_console.tag_configure('gps', foreground='green')
        self.log_console.tag_configure('cvp', foreground='blue')      # CVP = Blue
        self.log_console.tag_configure('can', foreground='magenta')   # CAN = Magenta
        self.log_console.tag_configure('net', foreground='green')     # NET = Green
        self.log_console.tag_configure('pla', foreground='yellow')     # PLA = Yellow
        self.log_console.tag_configure('fot', foreground='magenta')     # PLA = Yellow

    def check_ports(self):
        previous_ports = []
        while True:
            try:
                ports = serial.tools.list_ports.comports()
                current_ports = [port.device for port in ports]

                if len(current_ports) > len(previous_ports):
                    self.serial_port = serial.Serial(current_ports[-1], baudrate=115200, timeout=1)
                    self.root.title("AEPL Logger (Connected)")
                    self.start_logging()  

                elif len(current_ports) < len(previous_ports) or not self.serial_port.is_open:
                    self.root.title("AEPL Logger (Disconnected)")
                    self.stop_logging() 

                previous_ports = current_ports
                time.sleep(2)
            except Exception as e:
                print(f"Error checking ports: {e}")
                break 


    def start_logging(self):
        if not self.serial_port or not self.serial_port.is_open:
            messagebox.showerror("Error", "No serial port available or it is not open.")
            return
        if not self.log_file:
            self.log_file = open(f"serial_log_{time.strftime('%Y%m%d_%H%M%S')}.log", 'a')

        if not self.logging_active:
            self.logging_active = True
            self.log_console.insert(tk.END, "Logging started...\n")
            self.thread = threading.Thread(target=self.read_serial)
            self.thread.daemon = True  
            self.thread.start()

    def stop_logging(self):
        if self.logging_active:
            self.logging_active = False
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()  
            if self.log_file:
                self.log_file.close()
                self.log_file = None 

            self.log_console.insert(tk.END, "Logging stopped.\n")

    def read_serial(self):
        ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
        
        while self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline()
            
                    try:
                        line = line.decode('utf-8').rstrip()
                        line = ansi_escape.sub('', line) 
                    except UnicodeDecodeError:
                        line = "<Decoding Error>"
                    
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    log_entry = f"{timestamp} : {line}"

                    self.insert_ansi_colored_text(log_entry) # Simran : 04.07.24 -- call function changes
                    
                    self.log_console.yview(END)
                    if self.log_file:
                        self.log_file.write(log_entry + '\n')

                time.sleep(0.1) 
                
            except serial.SerialException as e:
                print(f"Serial exception: {e}")
                self.stop_logging() 
                break

            except Exception as e:
                print(f"Error reading from serial: {e}")
                self.stop_logging()
                break

    # Simran : 04.07.24 -- insert ansi text changes
    def insert_ansi_colored_text(self, text):
        # ANSI escape sequence regex pattern
        ansi_escape = re.compile(r'\033\[(\d+)(;\d+)*m')

        # Define flags and corresponding tags
        flags = {
            'AIS': 'ais',
            # 'GPS': 'gps',
            'CVP': 'cvp',
            'CAN': 'can',
            'NET': 'net',
            'PLA': 'pla',
            'FOT': 'fot',
        }

        # Initialize current tag
        current_tag = None

        # Split the text based on ANSI escape sequences
        parts = ansi_escape.split(text)

        for part in parts:
            # Check if part is an ANSI code
            if ansi_escape.match(part):
                # Detect the color based on the ANSI code
                codes = part.strip('\033[m').split(';')
                for code in codes:
                    # if code == "32":  # Green
                    #     current_tag = 'gps'
                    if code == "32":  # Green
                        current_tag = 'net'
                    elif code == "34":  # Blue
                        current_tag = 'cvp'
                    elif code == "35":  # Magenta
                        current_tag = 'can'
                    elif code == "33":  # Yellow
                        current_tag = 'pla'
                    elif code == "34":  # Blue
                        current_tag = 'ais'
                    elif code == "35":  # Magenta
                        current_tag = 'fot'
                    elif code == "0":  # Reset
                        current_tag = None

            else:
                # Check for log flags in the part
                for flag, tag in flags.items():
                    if flag in part:
                        current_tag = tag
                        break
                else:
                    current_tag = None  # No recognized flag, reset tag

                # Insert the text part with the current color tag
                if current_tag:
                    self.log_console.insert(tk.END, part, current_tag)
                else:
                    self.log_console.insert(tk.END, part)
 
        self.log_console.insert(tk.END, "\n")  # Insert a newline after the entire log entry
        self.log_console.yview(tk.END)  # Auto-scroll to the end

    def browse_file(self):
        if self.log_file:
            self.log_file.close()
        file_path = filedialog.askopenfilename(defaultextension=".log", filetypes=[("Text Files", "*.log")])
        if file_path:
            self.log_file = open(file_path, 'a')

    def create_new_file(self):
        if self.log_file:
            self.log_file.close()
        file_path = filedialog.asksaveasfilename(defaultextension=".log", filetypes=[("Text Files", "*.log")])
        if file_path:
            self.log_file = open(file_path, 'a')

    def save_log(self):
        if self.log_file:
            self.log_file.flush()
            messagebox.showinfo("Success", "Log saved successfully!")
        else:
            messagebox.showerror("Error", "No log file is open.")

    def port_settings(self):                                                                                                                       
        messagebox.showinfo("Port Settings", "Port settings would go here.")

    # Suraj : 04.07.24 -- Macro function started changes
    def macros(self):
        macro_file_path = filedialog.askopenfilename(
            title="Select Macro File",
            filetypes=[("TTL Files", "*.ttl")]
        )

        if not macro_file_path:
            return

        try:
            with open(macro_file_path, 'r') as macro_file:
                self.commands = [line.strip() for line in macro_file if line.strip() and not line.startswith('#')]

            self.current_command_index = 0
            self.is_paused = False

            # Start a separate thread to execute the macros
            threading.Thread(target=self.execute_macros, daemon=True).start()

        except Exception as e:
            messagebox.showerror("File Error", f"An error occurred while reading the file: {e}")

    # Macro heleper function.
    def execute_macros(self):
        while self.current_command_index < len(self.commands):
            current_line = self.commands[self.current_command_index]

            if current_line.lower().startswith('pause'):
                try:
                    self.pause_duration = float(current_line.split()[1])
                    self.insert_log(f"Pausing for {self.pause_duration} seconds...")
                    self.pause_start_time = time.time()
                    self.is_paused = True
                    self.current_command_index += 1  # Move to the next command after setting up the pause

                    # Continue logging while waiting for the pause to complete
                    while self.is_paused:
                        if time.time() - self.pause_start_time >= self.pause_duration:
                            self.is_paused = False  # Unset the pause
                            self.insert_log("Pause completed.")
                        self.read_and_log_device_data()
                        time.sleep(0.1)  # Small sleep to avoid high CPU usage

                    continue  # Proceed to next command after pause is complete

                except (IndexError, ValueError):
                    self.insert_log("Error: Invalid pause command in macro file.")
                    break

            if current_line.startswith('*'):
                # Handle serial command
                if self.serial_port and self.serial_port.is_open:
                    try:
                        command = current_line.strip()  
                        self.serial_port.write((command + '\n').encode())
                        self.insert_log(f"Executing command: {command}")

                        # Wait for device's response and log the data
                        while True:
                            self.read_and_log_device_data()
                            if self.serial_port.in_waiting > 0:
                                response = self.serial_port.readline().decode('utf-8').strip()
                                self.insert_log(f"Device Response: {response}")

                                # Break on specific response keyword
                                if "command completed" in response.lower() or "done" in response.lower():
                                    break

                        self.current_command_index += 1  # Move to the next command after completion
                        continue

                    except Exception as e:
                        self.insert_log(f"Error executing command: {e}")
                        break

            self.current_command_index += 1  # Proceed to the next command if none of the above conditions are met
            self.root.update_idletasks()  # Update UI

        self.insert_log("Macro file execution completed.")

    def read_and_log_device_data(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    device_data = self.serial_port.readline().decode('utf-8').strip()
                    self.insert_log(f"Device: {device_data}")
                    self.root.update_idletasks()
            except Exception as e:
                self.insert_log(f"Error reading from device: {e}")

    def insert_log(self, message):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.log_console.insert(tk.END, f"{timestamp} - {message}\n")
        self.log_console.yview(tk.END)
        self.root.update_idletasks()

    def show_about(self):
        messagebox.showinfo("About", "AEPL Logger\nVersion 1.0")

    def new_connection(self):
        connection_window = tk.Toplevel(self.root)
        connection_window.title("New Connection")
        connection_window.geometry("350x250") 

        connection_type = tk.StringVar(value="TCP/IP")
        tcp_radio = tk.Radiobutton(connection_window, text="TCP/IP", variable=connection_type, value="TCP/IP")
        tcp_radio.pack(anchor='w', padx=10, pady=5)

        serial_radio = tk.Radiobutton(connection_window, text="Serial", variable=connection_type, value="Serial")
        serial_radio.pack(anchor='w', padx=10, pady=5)

        tcp_frame = tk.Frame(connection_window)
        tcp_frame.pack(padx=10, pady=5, fill='x')

        tk.Label(tcp_frame, text="Host:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        host_entry = tk.Entry(tcp_frame)
        host_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(tcp_frame, text="TCP port#:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        tcp_port_entry = tk.Entry(tcp_frame)
        tcp_port_entry.grid(row=1, column=1, padx=5, pady=5)

        service_var = tk.StringVar(value="SSH")
        ssh_radio = tk.Radiobutton(tcp_frame, text="SSH", variable=service_var, value="SSH")
        ssh_radio.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        telnet_radio = tk.Radiobutton(tcp_frame, text="Telnet", variable=service_var, value="Telnet")
        telnet_radio.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        serial_frame = tk.Frame(connection_window)

        tk.Label(serial_frame, text="Port:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        port_entry = tk.Entry(serial_frame)
        port_entry.grid(row=0, column=1, padx=5, pady=5)

        def toggle_frames():
            if connection_type.get() == "TCP/IP":
                tcp_frame.pack(padx=10, pady=5, fill='x')
                serial_frame.pack_forget()
            else:
                tcp_frame.pack_forget()
                serial_frame.pack(padx=10, pady=5, fill='x')

        tcp_radio.config(command=toggle_frames)
        serial_radio.config(command=toggle_frames)

        button_frame = tk.Frame(connection_window)
        button_frame.pack(pady=15)

        def connect_action():
            if connection_type.get() == "TCP/IP":
                host = host_entry.get()
                port = tcp_port_entry.get()
                if not host or not port:
                    messagebox.showerror("Input Error", "Host and Port must be provided for TCP/IP.")
                    return
                else:
                    print(f"Connecting to {host}:{port} via {service_var.get()}")
            else:
                port = port_entry.get()
                if not port:
                    messagebox.showerror("Input Error", "Port must be provided for Serial connection.")
                    return
                else:
                    print(f"Connecting via Serial on port {port}")

            connection_window.destroy() 

        connection_window.bind('<Return>', lambda event: connect_action())

        ok_button = tk.Button(button_frame, text="OK", command=connect_action)
        ok_button.grid(row=0, column=0, padx=5)

        cancel_button = tk.Button(button_frame, text="Cancel", command=connection_window.destroy)
        cancel_button.grid(row=0, column=1, padx=5)

        help_button = tk.Button(button_frame, text="Help", command=lambda: messagebox.showinfo("Help", "Provide connection details and press OK to connect."))
        help_button.grid(row=0, column=2, padx=5)

        host_entry.focus_set()

    def duplicate_session(self):
        if not self.current_connection:
            messagebox.showerror("Error", "No active session to duplicate.")
            return

        connection_params = self.current_connection.get_params()  

        duplicate_window = tk.Toplevel(self.root)
        duplicate_window.title("Duplicate Session")

        connection_type = tk.StringVar(value=connection_params["type"])
        tcp_radio = tk.Radiobutton(duplicate_window, text="TCP/IP", variable=connection_type, value="TCP/IP")
        tcp_radio.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        serial_radio = tk.Radiobutton(duplicate_window, text="Serial", variable=connection_type, value="Serial")
        serial_radio.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        tcp_frame = tk.Frame(duplicate_window)
        tcp_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5)

        tk.Label(tcp_frame, text="Host:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        host_entry = tk.Entry(tcp_frame)
        host_entry.insert(0, connection_params["host"])
        host_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(tcp_frame, text="TCP port#:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        tcp_port_entry = tk.Entry(tcp_frame)
        tcp_port_entry.insert(0, connection_params["port"])
        tcp_port_entry.grid(row=1, column=1, padx=5, pady=5)

        service_var = tk.StringVar(value=connection_params["service"])
        ssh_radio = tk.Radiobutton(tcp_frame, text="SSH", variable=service_var, value="SSH")
        ssh_radio.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        telnet_radio = tk.Radiobutton(tcp_frame, text="Telnet", variable=service_var, value="Telnet")
        telnet_radio.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        serial_frame = tk.Frame(duplicate_window)
        tk.Label(serial_frame, text="Port:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        port_entry = tk.Entry(serial_frame)
        port_entry.insert(0, connection_params["port"])
        port_entry.grid(row=0, column=1, padx=5, pady=5)

        def toggle_frames():
            if connection_type.get() == "TCP/IP":
                tcp_frame.grid()
                serial_frame.grid_forget()
            else:
                tcp_frame.grid_forget()
                serial_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5)

        tcp_radio.config(command=toggle_frames)
        serial_radio.config(command=toggle_frames)

        if connection_params["type"] == "Serial":
            serial_radio.invoke()
        else:
            tcp_radio.invoke()

        button_frame = tk.Frame(duplicate_window)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        def connect_action():
            if connection_type.get() == "TCP/IP":
                host = host_entry.get()
                port = tcp_port_entry.get()
                if not host or not port:
                    messagebox.showerror("Input Error", "Host and Port must be provided for TCP/IP.")
                else:
                    print(f"Connecting to {host}:{port} via {service_var.get()}")
                    self.start_connection(host, port, service_var.get())  
            else:
                port = port_entry.get()
                if not port:
                    messagebox.showerror("Input Error", "Port must be provided for Serial connection.")
                else:
                    print(f"Connecting via Serial on port {port}")
                    self.start_serial_connection(port) 

            duplicate_window.destroy()

        ok_button = tk.Button(button_frame, text="OK", command=connect_action)
        ok_button.grid(row=0, column=0, padx=5)

        cancel_button = tk.Button(button_frame, text="Cancel", command=duplicate_window.destroy)
        cancel_button.grid(row=0, column=1, padx=5)

        help_button = tk.Button(button_frame, text="Help", command=lambda: messagebox.showinfo("Help", "Duplicate current session with these settings."))
        help_button.grid(row=0, column=2, padx=5)

    def view_log(self):
        file_path = filedialog.askopenfilename(defaultextension=".log", filetypes=[("Text Files", "*.log")])
        if file_path:
            with open(file_path, 'r') as file:
                log_content = file.read()
            log_window = tk.Toplevel(self.root)
            log_window.title("View Log")
            log_text = tk.Text(log_window, bg="white", fg="black", font=("Consolas", 10))
            log_text.pack(expand=True, fill=tk.BOTH)
            log_text.insert(tk.END, log_content)
            log_text.config(state=tk.DISABLED)

    def change_directory(self):
        directory_path = filedialog.askdirectory()
        if directory_path:
            messagebox.showinfo("Change Directory", f"Directory changed to {directory_path}.")

    def disconnect(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.log_console.insert(tk.END, "Disconnected from serial port.\n")
        self.root.title("AEPL Logger (Disconnected)")

    def exit_all(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        if self.log_file:
            self.log_file.close()
        self.root.quit()

    def copy(self):
        try:
            selected_text = self.log_console.get("sel.first", "sel.last")
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(selected_text)
        except tk.TclError:
            messagebox.showwarning("Copy", "No text selected to copy.")
    
    # Suraj : 04.07.24 -- Paste and fire serial commands from console
    def paste(self):
        try:
            clipboard_text = self.root.clipboard_get()  
            self.log_console.insert(tk.END, clipboard_text + '\n')  
            self.log_console.yview(tk.END) 

            if self.serial_port and self.serial_port.is_open:
                for line in clipboard_text.strip().splitlines():
                    command = line.strip()
                    if command.startswith('*'):
                        self.serial_port.write((command + '\n').encode()) 
                        self.insert_log(f"Sent command: {command}") 
                        self.wait_for_device_response()
                    else:
                        self.insert_log(f"Command skipped (not starting with *): {command}")

        except tk.TclError:
            messagebox.showwarning("Paste", "Clipboard is empty or cannot be accessed.")
        except Exception as e:
            self.insert_log(f"Error during paste operation: {e}")

    # Paste Functionality helper function.
    def wait_for_device_response(self):
        """ Waits for a response from the device after sending a command. """
        if self.serial_port and self.serial_port.is_open:
            try:
                # Adjust the waiting mechanism based on your device's response behavior
                while True:
                    if self.serial_port.in_waiting > 0:
                        response = self.serial_port.readline().decode('utf-8').strip()
                        self.insert_log(f"Device Response: {response}")
                        break
                    time.sleep(0.1) 
            except Exception as e:
                self.insert_log(f"Error reading from device: {e}")

    def insert_log(self, message):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.log_console.insert(tk.END, f"{timestamp} - {message}\n")
        self.log_console.yview(tk.END)
        self.root.update_idletasks()


    def maximize_window(self):
        self.root.state('zoomed')

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialUtility(root)
    root.mainloop()