import paramiko
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
import schedule
import time
import threading
from datetime import datetime
from PIL import Image, ImageTk
import json

# Define a JSON file to store the last input values
CONFIG_FILE_SEND = 'send_inputs.json'
CONFIG_FILE_GET = 'get_inputs.json'


def save_send_form_inputs(data):
    with open(CONFIG_FILE_SEND, 'w') as file:
        json.dump(data, file)

def load_send_form_inputs():
    if os.path.exists(CONFIG_FILE_SEND):
        with open(CONFIG_FILE_SEND, 'r') as file:
            return json.load(file)
    return {}

def save_get_form_inputs(data):
    with open(CONFIG_FILE_GET, 'w') as file:
        json.dump(data, file)

def load_get_form_inputs():
    if os.path.exists(CONFIG_FILE_GET):
        with open(CONFIG_FILE_GET, 'r') as file:
            return json.load(file)
    return {}

def transfer_files(source_path, destination_path, host, username, password, transfer_method, file_type):
    # print(f"Transferring files from {source_path} to {destination_path} on host {host} with username {username}")
    # Connect to the destination machine using SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=username, password=password)

    # Create an SFTP client
    sftp = ssh.open_sftp()
    
    # Create or append to the trace file
    trace_file_path = os.path.join(destination_path, "trace.txt")
    with sftp.file(trace_file_path, "a") as trace_file:
        transfer_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trace_file.write(f"\r\n{transfer_date}: File transfer initiated\r\n")
    
    # Transfer files from source to destination path
    for file_name in os.listdir(source_path):
        if file_name.endswith(file_type):
            local_source_path = os.path.join(source_path, file_name)
            remote_destination_path = os.path.join(destination_path, file_name)
            
            # Transfer files according to the specified method
            if transfer_method == "copy":
                sftp.put(local_source_path, remote_destination_path)
            elif transfer_method == "cut":
                sftp.put(local_source_path, remote_destination_path)
                os.remove(local_source_path)
            
            # Append transfer details to the trace file
            with sftp.file(trace_file_path, "a") as trace_file:
                trace_file.write(f"{transfer_date}: Transferred {file_name} from {source_path} to {destination_path}\r\n")
    
    # Close SFTP and SSH connections
    sftp.close()
    ssh.close()
    print("File transfer completed")

def get_files(machine2_source_path, machine1_destination_path, host, username, password, transfer_method, file_type):
    print(f"Getting files from {machine2_source_path} on host {host} with username {username}")

    # Connect to the source machine using SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=username, password=password)

    # Create an SFTP client
    sftp = ssh.open_sftp()

    # Ensure the destination directory exists
    if not os.path.exists(machine1_destination_path):
        os.makedirs(machine1_destination_path)

    # Create or append to the trace file
    trace_file_path = os.path.join(machine1_destination_path, "trace.txt")
    with open(trace_file_path, "a") as trace_file:
        transfer_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trace_file.write(f"\n{transfer_date}: File retrieval initiated\n")

    # Transfer files from source to destination path
    for file_name in sftp.listdir(machine2_source_path):
        if file_name.endswith(file_type):
            remote_source_path = os.path.join(machine2_source_path, file_name)
            local_destination_path = os.path.join(machine1_destination_path, file_name)

            # Transfer files according to the specified method
            if transfer_method == "copy":
                sftp.get(remote_source_path, local_destination_path)
            elif transfer_method == "cut":
                sftp.get(remote_source_path, local_destination_path)
                os.remove(remote_source_path)
        
            # Log transfer information
            with open(trace_file_path, "a") as trace_file:
                transfer_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                trace_file.write(f"{transfer_date}: Transferred {file_name} from {machine2_source_path} to {machine1_destination_path}\n")

        print(f"Transferred {file_name} from {machine2_source_path} to {machine1_destination_path}")

    # Close SFTP and SSH connections
    sftp.close()
    ssh.close()

    print("File retrieval completed")

# Function to run the scheduler in a separate thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# GUI creation
def create_gui():
    root = tk.Tk()
    root.title("File Transfer")

    # Set the window size and make it non-resizable
    root.geometry("620x450")
    root.resizable(False, False)

    # Set background color to #FFFFFF
    root.config(bg="#FFFFFF")

    # Create a custom style to set the background color of frames
    style = ttk.Style()
    style.configure("Custom.TFrame", background="#F1F1F1")

    script_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
     # Specify the relative path to the image file
    logo_path = os.path.join(script_dir, "images/images.png")
    # Load and resize the logo image using Pillow
    image = Image.open(logo_path)
    image = image.resize((300, 63), Image.BOX)  # Resize the image to pixels
    logo = ImageTk.PhotoImage(image)

    # Create a label to display the logo
    logo_label = tk.Label(root, image=logo, bg="#FFFFFF")
    logo_label.image = logo  # Keep a reference to avoid garbage collection
    logo_label.pack(pady=10)  # Add some padding to position the logo nicely# Add some padding to position the logo nicely

    send_form_last_inputs = load_send_form_inputs()
    get_form_last_inputs = load_get_form_inputs()

    # font = ("Palatino Linotype", 12)
    font = ("Courier New",10)


    def create_machine1_form(frame):
        # Create the form elements for Machine 1
        tk.Label(frame, text="Machine 1 Source Path:",font=font).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        machine1_source_entry = tk.Entry(frame, width=60)
        machine1_source_entry.grid(row=0, column=1, padx=5, pady=5)
        machine1_source_entry.insert(0, send_form_last_inputs.get('machine1_source_path', ''))

        tk.Label(frame, text="Machine 2 Destination Path:",font=font).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        machine2_destination_entry = tk.Entry(frame, width=60)
        machine2_destination_entry.grid(row=1, column=1, padx=5, pady=5)
        machine2_destination_entry.insert(0, send_form_last_inputs.get('machine2_destination_path', ''))

        tk.Label(frame, text="Host (IP or hostname):",font=font).grid(row=2, column=0, padx=5, pady=5, sticky="e")
        host_entry = tk.Entry(frame, width=60)
        host_entry.grid(row=2, column=1, padx=5, pady=5)
        host_entry.insert(0, send_form_last_inputs.get('host', ''))

        tk.Label(frame, text="Username:",font=font).grid(row=3, column=0, padx=5, pady=5, sticky="e")
        username_entry = tk.Entry(frame, width=60)
        username_entry.grid(row=3, column=1, padx=5, pady=5)
        username_entry.insert(0, send_form_last_inputs.get('username', ''))

        tk.Label(frame, text="Password:",font=font).grid(row=4, column=0, padx=5, pady=5, sticky="e")
        password_entry = tk.Entry(frame, width=60, show='*')
        password_entry.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(frame, text="Frequency (minutes):",font=font).grid(row=5, column=0, padx=5, pady=5, sticky="e")
        frequency_entry = tk.Entry(frame, width=10)
        frequency_entry.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        frequency_entry.insert(0, send_form_last_inputs.get('frequency', ''))

        tk.Label(frame, text="File Type:",font=font).grid(row=6, column=0, padx=5, pady=5, sticky="e")
        file_type_var = tk.StringVar(value=send_form_last_inputs.get('file_type', 'txt'))
        file_type_spinner = ttk.Combobox(frame, textvariable=file_type_var, values=["txt", "csv"], state="readonly")
        file_type_spinner.grid(row=6, column=1, padx=5, pady=5,sticky="w")

        tk.Label(frame, text="Transfer Method:",font=font).grid(row=7, column=0, padx=5, pady=5, sticky="e")
        transfer_method_var = tk.StringVar(value=send_form_last_inputs.get('transfer_method', 'copy'))
        transfer_spinner = ttk.Combobox(frame, textvariable=transfer_method_var, values=["copy", "cut"], state="readonly")
        transfer_spinner.grid(row=7, column=1, padx=5, pady=5,sticky="w")

        # Transfer button
        def on_transfer_button_click():
            source_path = machine1_source_entry.get()
            destination_path = machine2_destination_entry.get()
            host = host_entry.get()
            username = username_entry.get()
            password = password_entry.get()
            transfer_method = transfer_method_var.get()
            file_type = file_type_var.get()
            frequency = frequency_entry.get()

            try:
                frequency = int(frequency)
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid frequency in minutes.")
                return
            
            # Save the inputs to the JSON file
            save_send_form_inputs({
                'machine1_source_path': source_path,
                'machine2_destination_path': destination_path,
                'host': host,
                'username': username,
                'frequency': frequency,
                'file_type': file_type,
                'transfer_method': transfer_method
            })
     
            # Define the function to be scheduled
            def scheduled_transfer():
                transfer_files(source_path, destination_path, host, username, password, transfer_method, file_type)
           
            try:  
                if not password or len(password) != 9:
                    raise Exception
            except Exception:
                messagebox.showerror("Invalid input","please eneter a valid password")
                return
            
            # Schedule the function at the specified frequency
            schedule.every(frequency).minutes.do(scheduled_transfer)
            print(f"Scheduled transfer every {frequency} minutes.")

                

         # Function to handle immediate file transfer
        def on_force_transfer_button_click():
            source_path = machine1_source_entry.get()
            destination_path = machine2_destination_entry.get()
            host = host_entry.get()
            username = username_entry.get()
            password = password_entry.get()
            transfer_method = transfer_method_var.get()
            file_type = file_type_var.get()

            # Save the inputs to the JSON file
            save_send_form_inputs({
                'machine1_source_path': source_path,
                'machine2_destination_path': destination_path,
                'host': host,
                'username': username,
                'frequency': frequency_entry.get(),
                'file_type': file_type,
                'transfer_method': transfer_method
            })

            # Execute file transfer immediately
            transfer_files(source_path, destination_path, host, username, password, transfer_method, file_type)

        # Create the buttons
        transfer_button = tk.Button(frame, text="Schedule Transfer",font=font, command=on_transfer_button_click,bg="#043052", fg="#FFFFFF")
        transfer_button.grid(row=8, column=1, columnspan=1, pady=10,sticky="e")

        # Button to force transfer
        force_transfer_button = tk.Button(frame, text="Force Transfer",font=font, command=on_force_transfer_button_click,bg="#043052", fg="#FFFFFF")
        force_transfer_button.grid(row=8, column=1, columnspan=1, pady=10,sticky="w") 

        # Create a label for the copyright text
        copyright_label = tk.Label(frame, text="© Groupe CHIALI 2024", font=font)
        copyright_label.grid(row=9, column=0, columnspan=2, pady=10)  # Position at bottom-right corner



    def create_machine2_form(frame):
        # Create the form elements for Machine 2
        tk.Label(frame, text="Machine 2 Source Path:",font=font).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        machine2_source_entry = tk.Entry(frame, width=60)
        machine2_source_entry.grid(row=0, column=1, padx=5, pady=5)
        machine2_source_entry.insert(0, get_form_last_inputs.get('machine2_source_path', ''))
        
        tk.Label(frame, text="Machine 1 destination Path:",font=font).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        machine1_destination_entry = tk.Entry(frame, width=60)
        machine1_destination_entry.grid(row=1, column=1, padx=5, pady=5)
        machine1_destination_entry.insert(0, get_form_last_inputs.get('machine1_destination_path', ''))

        tk.Label(frame, text="Host (IP or hostname):",font=font).grid(row=2, column=0, padx=5, pady=5, sticky="e")
        host_entry = tk.Entry(frame, width=60)
        host_entry.grid(row=2, column=1, padx=5, pady=5)
        host_entry.insert(0, get_form_last_inputs.get('host', ''))

        tk.Label(frame, text="Username:",font=font).grid(row=3, column=0, padx=5, pady=5, sticky="e")
        username_entry = tk.Entry(frame, width=60)
        username_entry.grid(row=3, column=1, padx=5, pady=5)
        username_entry.insert(0, get_form_last_inputs.get('username', ''))

        tk.Label(frame, text="Password:",font=font).grid(row=4, column=0, padx=5, pady=5, sticky="e")
        password_entry = tk.Entry(frame, width=60, show='*')
        password_entry.grid(row=4, column=1, padx=5, pady=5)

        tk.Label(frame, text="Frequency (minutes):",font=font).grid(row=5, column=0, padx=5, pady=5, sticky="e")
        frequency_entry = tk.Entry(frame, width=10)
        frequency_entry.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        frequency_entry.insert(0, get_form_last_inputs.get('frequency', ''))

        tk.Label(frame, text="File Type:",font=font).grid(row=6, column=0, padx=5, pady=5, sticky="e")
        file_type_var = tk.StringVar(value=get_form_last_inputs.get('file_type', 'txt'))
        file_type_spinner = ttk.Combobox(frame, textvariable=file_type_var, values=["txt", "csv"], state="readonly")
        file_type_spinner.grid(row=6, column=1, padx=5, pady=5,sticky="w")

        tk.Label(frame, text="Transfer Method:",font=font).grid(row=7, column=0, padx=5, pady=5, sticky="e")
        transfer_method_var = tk.StringVar(value=get_form_last_inputs.get('transfer_method', 'copy'))
        transfer_spinner = ttk.Combobox(frame, textvariable=transfer_method_var, values=["copy", "cut"], state="readonly")
        transfer_spinner.grid(row=7, column=1, padx=5, pady=5,sticky="w")

        # Button to get files from machine 2
        def on_get_files_button_click():
            machine2_source_path = machine2_source_entry.get()
            machine1_destination_path = machine1_destination_entry.get()
            host = host_entry.get()
            username = username_entry.get()
            password = password_entry.get()
            transfer_method = transfer_method_var.get()
            file_type = file_type_var.get()

            # Save the inputs to the JSON file
            save_get_form_inputs({
                'machine2_source_path': machine2_source_path,
                'machine1_destination_path': machine1_destination_path,
                'host': host,
                'username': username,
                'frequency': frequency_entry.get(),
                'file_type': file_type,
                'transfer_method': transfer_method
            })

            get_files(machine2_source_path, machine1_destination_path, host, username, password, transfer_method, file_type)

        # Transfer button
        def on_transfer_get_button_click():
            machine2_source_path = machine2_source_entry.get()
            machine1_destination_path = machine1_destination_entry.get()
            host = host_entry.get()
            username = username_entry.get()
            password = password_entry.get()
            transfer_method = transfer_method_var.get()
            file_type = file_type_var.get()
            frequency = frequency_entry.get()

            try:
                frequency = int(frequency)
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid frequency in minutes.")
                return

            try:  
                if not password or len(password) != 9:
                    raise Exception    
            except Exception:
                messagebox.showerror("Invalid input","please eneter a valid password")
                return           
            
            # Save the inputs to the JSON file
            save_get_form_inputs({
                'machine2_source_path': machine2_source_path,
                'machine1_destination_path': machine1_destination_path,
                'host': host,
                'username': username,
                'frequency': frequency,
                'file_type': file_type,
                'transfer_method': transfer_method
            })

            # Define the function to be scheduled
            def scheduled_transfer_get():
                get_files(machine2_source_path, machine1_destination_path, host, username, password, transfer_method, file_type)

            # Schedule the function at the specified frequency
            schedule.every(frequency).minutes.do(scheduled_transfer_get)
            print(f"Scheduled transfer every {frequency} minutes.")

        # Button to schedule get transfer
        transfer_get_button = tk.Button(frame, text="Schedule Transfer get", command=on_transfer_get_button_click,bg="#043052", fg="#FFFFFF",font=font)
        transfer_get_button.grid(row=8, column=1, columnspan=1, pady=10,sticky="e")
        
        # Button to force get files
        force_get_files_button = tk.Button(frame, text="get files", command=on_get_files_button_click,bg="#043052", fg="#FFFFFF",font=font)
        force_get_files_button.grid(row=8, column=1, columnspan=1, pady=10,sticky="w")

        # Create a label for the copyright text
        copyright_label = tk.Label(frame, text="© Groupe CHIALI 2024", font=font)
        copyright_label.grid(row=9, column=0, columnspan=2, pady=10)  # Position at bottom-right corner

    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)
    
    
    # Create frames for each tab
    machine1_frame = ttk.Frame(notebook, style="Custom.TFrame")
    machine2_frame = ttk.Frame(notebook, style="Custom.TFrame")

    notebook.add(machine1_frame, text="Machine 1")
    notebook.add(machine2_frame, text="Machine 2")

   

    # Create forms for each tab
    create_machine1_form(machine1_frame)
    create_machine2_form(machine2_frame)
    # Run the scheduler in a separate thread
    threading.Thread(target=run_scheduler, daemon=True).start()

    # Run the main loop
    root.mainloop()

# Call the function to create the GUI
create_gui()
