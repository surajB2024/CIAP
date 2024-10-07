import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, simpledialog
from tkinter import Text, END
import serial
import serial.tools.list_ports
import threading
import time
import re
import ansi2html

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

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New Connection", command=self.new_connection, accelerator="Alt+N")
        file_menu.add_command(label="Duplicate Session", command=self.duplicate_session, accelerator="Alt+D")
        file_menu.add_command(label="Cygwin Connection", command=self.cygwin_connection, accelerator="Alt+G")
        file_menu.add_separator()
        file_menu.add_command(label="Log", command=self.start_logging, accelerator="Ctrl+L")
        file_menu.add_command(label="Comment to Log", command=self.comment_to_log, accelerator="Ctrl+M")
        file_menu.add_command(label="View Log", command=self.view_log, accelerator="Ctrl+V")
        file_menu.add_command(label="Show Log Dialog", command=self.show_log_dialog, accelerator="Ctrl+Shift+L")
        file_menu.add_command(label="Send File", command=self.send_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Transfer", command=self.transfer, accelerator="Ctrl+T")
        file_menu.add_command(label="SSH SCP", command=self.ssh_scp, accelerator="Ctrl+Shift+S")
        file_menu.add_command(label="Change Directory", command=self.change_directory, accelerator="Ctrl+D")
        file_menu.add_command(label="Replay Log", command=self.replay_log, accelerator="Ctrl+R")
        file_menu.add_command(label="TTY Record", command=self.tty_record, accelerator="Ctrl+Shift+R")
        file_menu.add_command(label="TTY Replay", command=self.tty_replay, accelerator="Ctrl+Shift+E")
        file_menu.add_command(label="Print", command=self.print_log, accelerator="Alt+P")
        file_menu.add_separator()
        file_menu.add_command(label="Disconnect", command=self.disconnect, accelerator="Alt+1")
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Alt+Q")
        file_menu.add_command(label="Exit All", command=self.exit_all)
        menu_bar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Copy", command=self.copy, accelerator="Alt+C")
        edit_menu.add_command(label="Paste", command=self.paste, accelerator="Alt+V")
        edit_menu.add_command(label="Clear Screen", command=self.clear_screen, accelerator="Alt+R")
        edit_menu.add_command(label="Clear Buffer", command=self.clear_buffer)
        edit_menu.add_command(label="Cancel Selection", command=self.cancel_selection)
        edit_menu.add_command(label="Select Screen", command=self.select_screen)
        edit_menu.add_command(label="Select All", command=self.select_all)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        setup_menu = tk.Menu(menu_bar, tearoff=0)
        setup_menu.add_command(label="Port Settings", command=self.port_settings)
        menu_bar.add_cascade(label="Setup", menu=setup_menu)

        control_menu = tk.Menu(menu_bar, tearoff=0)
        control_menu.add_command(label="Start", command=self.start_logging, accelerator="Ctrl+Shift+S")
        control_menu.add_command(label="Stop", command=self.stop_logging, accelerator="Ctrl+Shift+Q")
        menu_bar.add_cascade(label="Control", menu=control_menu)

        windows_menu = tk.Menu(menu_bar, tearoff=0)
        windows_menu.add_command(label="Minimize", command=self.root.iconify, accelerator="Ctrl+M")
        windows_menu.add_command(label="Maximize", command=self.maximize_window, accelerator="Ctrl+Shift+M")
        menu_bar.add_cascade(label="Windows", menu=windows_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menu_bar)

        # Bind keyboard shortcuts
        self.root.bind_all("<Alt-n>", lambda e: self.new_connection())
        self.root.bind_all("<Alt-d>", lambda e: self.duplicate_session())
        self.root.bind_all("<Alt-g>", lambda e: self.cygwin_connection())
        self.root.bind_all("<Control-l>", lambda e: self.start_logging())
        self.root.bind_all("<Control-m>", lambda e: self.comment_to_log())
        self.root.bind_all("<Control-v>", lambda e: self.view_log())
        self.root.bind_all("<Control-Shift-L>", lambda e: self.show_log_dialog())
        self.root.bind_all("<Control-s>", lambda e: self.send_file())
        self.root.bind_all("<Control-t>", lambda e: self.transfer())
        self.root.bind_all("<Control-Shift-S>", lambda e: self.ssh_scp())
        self.root.bind_all("<Control-d>", lambda e: self.change_directory())
        self.root.bind_all("<Control-r>", lambda e: self.replay_log())
        self.root.bind_all("<Control-Shift-R>", lambda e: self.tty_record())
        self.root.bind_all("<Control-Shift-E>", lambda e: self.tty_replay())
        self.root.bind_all("<Alt-p>", lambda e: self.print_log())
        self.root.bind_all("<Alt-1>", lambda e: self.disconnect())
        self.root.bind_all("<Alt-q>", lambda e: self.root.quit())
        self.root.bind_all("<Control-Shift-Q>", lambda e: self.exit_all())
        self.root.bind_all("<Alt-c>", lambda e: self.copy())
        self.root.bind_all("<Alt-v>", lambda e: self.paste())
        self.root.bind_all("<Alt-r>", lambda e: self.clear_screen())
        self.root.bind_all("<Control-x>", lambda e: self.clear_buffer())
        self.root.bind_all("<Control-z>", lambda e: self.cancel_selection())
        self.root.bind_all("<Control-a>", lambda e: self.select_screen())
        self.root.bind_all("<Control-s>", lambda e: self.select_all())
        pass

    def create_widgets(self):
        # Log console (80% of the screen) with black background to mimic a terminal
        # self.log_console = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, bg="black", fg="white", font=("Consolas", 10))
        self.log_console = scrolledtext.ScrolledText(self.root, wrap=tk.NONE, bg="black", fg="white", font=("Consolas", 10))
        self.log_console.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)  # Removed padding


    def check_ports(self):
        previous_ports = []
        while True:
            try:
                ports = serial.tools.list_ports.comports()
                current_ports = [port.device for port in ports]

                # Check if a new port has been connected
                if len(current_ports) > len(previous_ports):
                    self.serial_port = serial.Serial(current_ports[-1], baudrate=115200, timeout=1)
                    self.root.title("AEPL Logger (Connected)")
                    self.start_logging()  # Only start logging when a connection is made

                # Check if the port was disconnected
                elif len(current_ports) < len(previous_ports) or not self.serial_port.is_open:
                    self.root.title("AEPL Logger (Disconnected)")
                    self.stop_logging()  # Stop logging when the connection is lost

                previous_ports = current_ports
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                print(f"Error checking ports: {e}")
                break  # Optionally break on error to avoid infinite loop


    def start_logging(self):
        if not self.serial_port or not self.serial_port.is_open:
            messagebox.showerror("Error", "No serial port available or it is not open.")
            return
        
        # Only open a new log file if one is not already open
        if not self.log_file:
            self.log_file = open(f"serial_log_{time.strftime('%Y%m%d_%H%M%S')}.log", 'a')

        if not self.logging_active:
            self.logging_active = True
            self.log_console.insert(tk.END, "Logging started...\n")
            self.thread = threading.Thread(target=self.read_serial)
            self.thread.daemon = True  # Ensure thread exits when main program exits
            self.thread.start()

    def stop_logging(self):
        if self.logging_active:
            self.logging_active = False
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()  # Close the serial port
            if self.log_file:
                self.log_file.close()
                self.log_file = None  # Reset the log file handler

            self.log_console.insert(tk.END, "Logging stopped.\n")

    def read_serial(self):
        ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
        
        while self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:  # Only read if there is data
                    line = self.serial_port.readline()
                    
                    # Attempt to decode the line, handle decoding errors
                    try:
                        line = line.decode('utf-8').rstrip()
                        line = ansi_escape.sub('', line)  # Remove ANSI codes
                    except UnicodeDecodeError:
                        line = "<Decoding Error>"
                    
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    log_entry = f"{timestamp} - {line}"
                    
                    # Insert cleaned log entry into the console
                    self.log_console.insert(tk.END, log_entry + '\n')
                    self.log_console.yview(END)  # Auto-scroll to the end

                    # Log to file if needed
                    if self.log_file:
                        self.log_file.write(log_entry + '\n')

                time.sleep(0.1)  # Small delay to avoid CPU overuse
                
            except serial.SerialException as e:
                print(f"Serial exception: {e}")
                self.stop_logging()  # Stop logging if there's a serial exception
                break

            except Exception as e:
                print(f"Error reading from serial: {e}")
                self.stop_logging()
                break  # Break the loop in case of an error


    def insert_ansi_text(self, widget, text):
        # This function interprets ANSI escape sequences and inserts colored text
        converter = ansi2html.Ansi2HTMLConverter()
        html = converter.convert(text, full=False)  # Convert ANSI to HTML for color

        # Extract the text between <span> tags and apply corresponding color tags in the widget
        # Add parsing logic here based on your preference and desired colors
        widget.insert(END, text)
        widget.yview(END)  # Scroll to the end

    def browse_file(self):
        if self.log_file:
            self.log_file.close()
        file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.log_file = open(file_path, 'a')

    def create_new_file(self):
        if self.log_file:
            self.log_file.close()
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.log_file = open(file_path, 'a')

    def save_log(self):
        if self.log_file:
            self.log_file.flush()
            messagebox.showinfo("Success", "Log saved successfully!")
        else:
            messagebox.showerror("Error", "No log file is open.")

    def port_settings(self):
        # Here you could create a configuration dialog to change baud rate, etc.
        messagebox.showinfo("Port Settings", "Port settings would go here.")

    def show_about(self):
        messagebox.showinfo("About", "AEPL Logger\nVersion 1.0")

    def new_connection(self):
        # Create a new Toplevel window
        connection_window = tk.Toplevel(self.root)
        connection_window.title("New Connection")
        
        # Set up TCP/IP and Serial radio buttons
        connection_type = tk.StringVar(value="TCP/IP")
        tcp_radio = tk.Radiobutton(connection_window, text="TCP/IP", variable=connection_type, value="TCP/IP")
        tcp_radio.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        serial_radio = tk.Radiobutton(connection_window, text="Serial", variable=connection_type, value="Serial")
        serial_radio.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        # TCP/IP frame (default visible)
        tcp_frame = tk.Frame(connection_window)
        tcp_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5)

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

        # Serial frame (hidden initially)
        serial_frame = tk.Frame(connection_window)

        tk.Label(serial_frame, text="Port:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        port_entry = tk.Entry(serial_frame)
        port_entry.grid(row=0, column=1, padx=5, pady=5)

        # Toggle frames between TCP/IP and Serial based on selection
        def toggle_frames():
            if connection_type.get() == "TCP/IP":
                tcp_frame.grid()
                serial_frame.grid_forget()
            else:
                tcp_frame.grid_forget()
                serial_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5)

        tcp_radio.config(command=toggle_frames)
        serial_radio.config(command=toggle_frames)

        # Buttons at the bottom
        button_frame = tk.Frame(connection_window)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        def connect_action():
            if connection_type.get() == "TCP/IP":
                host = host_entry.get()
                port = tcp_port_entry.get()
                if not host or not port:
                    messagebox.showerror("Input Error", "Host and Port must be provided for TCP/IP.")
                else:
                    # Here, you would connect using the TCP/IP details
                    print(f"Connecting to {host}:{port} via {service_var.get()}")
            else:
                port = port_entry.get()
                if not port:
                    messagebox.showerror("Input Error", "Port must be provided for Serial connection.")
                else:
                    # Here, you would connect using the Serial details
                    print(f"Connecting via Serial on port {port}")

            connection_window.destroy()  # Close the dialog after connection

        ok_button = tk.Button(button_frame, text="OK", command=connect_action)
        ok_button.grid(row=0, column=0, padx=5)

        cancel_button = tk.Button(button_frame, text="Cancel", command=connection_window.destroy)
        cancel_button.grid(row=0, column=1, padx=5)

        help_button = tk.Button(button_frame, text="Help", command=lambda: messagebox.showinfo("Help", "Provide connection details and press OK to connect."))
        help_button.grid(row=0, column=2, padx=5)


    def duplicate_session(self):
        if not self.current_connection:
            messagebox.showerror("Error", "No active session to duplicate.")
            return

        connection_params = self.current_connection.get_params()  # Get active session parameters

        duplicate_window = tk.Toplevel(self.root)
        duplicate_window.title("Duplicate Session")

        connection_type = tk.StringVar(value=connection_params["type"])
        tcp_radio = tk.Radiobutton(duplicate_window, text="TCP/IP", variable=connection_type, value="TCP/IP")
        tcp_radio.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        serial_radio = tk.Radiobutton(duplicate_window, text="Serial", variable=connection_type, value="Serial")
        serial_radio.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        tcp_frame = tk.Frame(duplicate_window)
        tcp_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5)

        # Host and Port input for TCP/IP
        tk.Label(tcp_frame, text="Host:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        host_entry = tk.Entry(tcp_frame)
        host_entry.insert(0, connection_params["host"])
        host_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(tcp_frame, text="TCP port#:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        tcp_port_entry = tk.Entry(tcp_frame)
        tcp_port_entry.insert(0, connection_params["port"])
        tcp_port_entry.grid(row=1, column=1, padx=5, pady=5)

        # Service type selection (SSH, Telnet, etc.)
        service_var = tk.StringVar(value=connection_params["service"])
        ssh_radio = tk.Radiobutton(tcp_frame, text="SSH", variable=service_var, value="SSH")
        ssh_radio.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        telnet_radio = tk.Radiobutton(tcp_frame, text="Telnet", variable=service_var, value="Telnet")
        telnet_radio.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        # Serial Port Input
        serial_frame = tk.Frame(duplicate_window)
        tk.Label(serial_frame, text="Port:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        port_entry = tk.Entry(serial_frame)
        port_entry.insert(0, connection_params["port"])
        port_entry.grid(row=0, column=1, padx=5, pady=5)

        # Toggle visibility of TCP or Serial input based on selection
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

        # Action for Connect Button
        def connect_action():
            if connection_type.get() == "TCP/IP":
                host = host_entry.get()
                port = tcp_port_entry.get()
                if not host or not port:
                    messagebox.showerror("Input Error", "Host and Port must be provided for TCP/IP.")
                else:
                    print(f"Connecting to {host}:{port} via {service_var.get()}")
                    self.start_connection(host, port, service_var.get())  # Replace with actual connect logic
            else:
                port = port_entry.get()
                if not port:
                    messagebox.showerror("Input Error", "Port must be provided for Serial connection.")
                else:
                    print(f"Connecting via Serial on port {port}")
                    self.start_serial_connection(port)  # Replace with actual serial connect logic

            duplicate_window.destroy()

        ok_button = tk.Button(button_frame, text="OK", command=connect_action)
        ok_button.grid(row=0, column=0, padx=5)

        cancel_button = tk.Button(button_frame, text="Cancel", command=duplicate_window.destroy)
        cancel_button.grid(row=0, column=1, padx=5)

        help_button = tk.Button(button_frame, text="Help", command=lambda: messagebox.showinfo("Help", "Duplicate current session with these settings."))
        help_button.grid(row=0, column=2, padx=5)


    def cygwin_connection(self):
        # Placeholder for Cygwin connection
        messagebox.showinfo("Cygwin Connection", "Cygwin connection setup dialog would go here.")

    def comment_to_log(self):
        comment = simpledialog.askstring("Comment to Log", "Enter comment:")
        if comment:
            self.log_console.insert(tk.END, f"# {comment}\n")
            if self.log_file:
                self.log_file.write(f"# {comment}\n")

    def view_log(self):
        # Do not close the log file here; just open it for reading
        file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, 'r') as file:
                log_content = file.read()
            log_window = tk.Toplevel(self.root)
            log_window.title("View Log")
            log_text = tk.Text(log_window, bg="white", fg="black", font=("Consolas", 10))
            log_text.pack(expand=True, fill=tk.BOTH)
            log_text.insert(tk.END, log_content)
            log_text.config(state=tk.DISABLED)


    def show_log_dialog(self):
        # Do not close the log file here; just open it for reading
        file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, 'r') as file:
                log_content = file.read()
            log_window = tk.Toplevel(self.root)
            log_window.title("Log Dialog")
            log_text = tk.Text(log_window, bg="white", fg="black", font=("Consolas", 10))
            log_text.pack(expand=True, fill=tk.BOTH)
            log_text.insert(tk.END, log_content)
            log_text.config(state=tk.DISABLED)


    def send_file(self):
        # Placeholder for sending a file
        file_path = filedialog.askopenfilename(filetypes=[("All Files", "*.*")])
        if file_path:
            # Implement file sending functionality
            messagebox.showinfo("Send File", f"File {file_path} selected for sending.")

    def transfer(self):
        # Placeholder for transfer functionality
        messagebox.showinfo("Transfer", "Transfer functionality would go here.")

    def ssh_scp(self):
        # Placeholder for SSH SCP functionality
        messagebox.showinfo("SSH SCP", "SSH SCP functionality would go here.")

    def change_directory(self):
        # Placeholder for changing directory
        directory_path = filedialog.askdirectory()
        if directory_path:
            messagebox.showinfo("Change Directory", f"Directory changed to {directory_path}.")

    def replay_log(self):
        # Placeholder for replaying a log
        messagebox.showinfo("Replay Log", "Replay Log functionality would go here.")

    def tty_record(self):
        # Placeholder for TTY record functionality
        messagebox.showinfo("TTY Record", "TTY Record functionality would go here.")

    def tty_replay(self):
        # Placeholder for TTY replay functionality
        messagebox.showinfo("TTY Replay", "TTY Replay functionality would go here.")

    def print_log(self):
        # Placeholder for print functionality
        messagebox.showinfo("Print", "Print functionality would go here.")

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
        # Implement copy functionality
        selected_text = self.log_console.get("sel.first", "sel.last")
        self.clipboard_clear()
        self.clipboard_append(selected_text)

    def paste(self):
        # Implement paste functionality
        try:
            clipboard_text = self.clipboard_get()
            self.log_console.insert(tk.INSERT, clipboard_text)
        except tk.TclError:
            messagebox.showwarning("Paste", "Clipboard is empty or cannot be accessed.")

    def clear_screen(self):
        self.log_console.delete(1.0, tk.END)

    def clear_buffer(self):
        # Implement buffer clearing if needed
        messagebox.showinfo("Clear Buffer", "Buffer cleared.")

    def cancel_selection(self):
        self.log_console.tag_add('sel', '1.0', '1.0')

    def select_screen(self):
        self.log_console.tag_add('sel', '1.0', tk.END)

    def select_all(self):
        self.log_console.tag_add('sel', '1.0', tk.END)

    def maximize_window(self):
        self.root.state('zoomed')

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialUtility(root)
    root.mainloop()
