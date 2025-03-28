import speech_recognition as sr
import psutil
import subprocess
import platform
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from multiprocessing import Process, Pipe

# GUI Setup
root = tk.Tk()
root.title("VoiceOS Manager")
root.geometry("900x700")
root.configure(bg="#2E2E2E")

# Styling
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background="#3C3C3C", foreground="white", fieldbackground="#3C3C3C", rowheight=25)
style.configure("Treeview.Heading", background="#4A4A4A", foreground="white", font=("Arial", 10, "bold"))
style.configure("TButton", font=("Arial", 10), padding=5)

# Header Label
header = tk.Label(root, text="VoiceOS Manager", font=("Arial", 18, "bold"), bg="#2E2E2E", fg="#00D4FF")
header.pack(pady=10)

# Frame for Process List
process_frame = tk.Frame(root, bg="#2E2E2E")
process_frame.pack(fill="both", expand=True, padx=10, pady=5)

# Process List Table
tree = ttk.Treeview(process_frame, columns=("PID", "Name", "CPU", "Memory"), show="headings", height=15)
tree.heading("PID", text="PID")
tree.heading("Name", text="Process Name")
tree.heading("CPU", text="CPU %")
tree.heading("Memory", text="Memory %")
tree.column("PID", width=80, anchor="center")
tree.column("Name", width=250)
tree.column("CPU", width=100, anchor="center")
tree.column("Memory", width=100, anchor="center")
tree.pack(side="left", fill="both", expand=True)

# Scrollbar for Process List
scrollbar = ttk.Scrollbar(process_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# Control Panel Frame
control_frame = tk.Frame(root, bg="#2E2E2E")
control_frame.pack(fill="x", padx=10, pady=5)

# Buttons and Entries
refresh_btn = ttk.Button(control_frame, text="Refresh", command=lambda: update_process_list())
refresh_btn.grid(row=0, column=0, padx=5)

start_entry = tk.Entry(control_frame, width=20, bg="#3C3C3C", fg="white", insertbackground="white")
start_entry.grid(row=0, column=1, padx=5)
start_btn = ttk.Button(control_frame, text="Start Process", command=lambda: start_process(start_entry.get()))
start_btn.grid(row=0, column=2, padx=5)

kill_entry = tk.Entry(control_frame, width=10, bg="#3C3C3C", fg="white", insertbackground="white")
kill_entry.grid(row=0, column=3, padx=5)
kill_btn = ttk.Button(control_frame, text="Kill Process", command=lambda: kill_process(kill_entry.get()))
kill_btn.grid(row=0, column=4, padx=5)

# Search Feature
search_entry = tk.Entry(control_frame, width=20, bg="#3C3C3C", fg="white", insertbackground="white")
search_entry.grid(row=0, column=5, padx=5)
search_btn = ttk.Button(control_frame, text="Search Process", command=lambda: search_process(search_entry.get()))
search_btn.grid(row=0, column=6, padx=5)

# Status Label
status_label = tk.Label(root, text="Status: Listening...", font=("Arial", 12), bg="#2E2E2E", fg="#FFD700")
status_label.pack(pady=5)

# Log Area
log_frame = tk.Frame(root, bg="#2E2E2E")
log_frame.pack(fill="x", padx=10, pady=5)
log = tk.Text(log_frame, height=8, bg="#3C3C3C", fg="white", font=("Arial", 10), wrap="word")
log.pack(side="left", fill="x", expand=True)
log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=log.yview)
log.configure(yscrollcommand=log_scroll.set)
log_scroll.pack(side="right", fill="y")

# Voice Recognizer & OS Detection
recognizer = sr.Recognizer()
OS = platform.system()

# Update Process List
def update_process_list():
    for i in tree.get_children():
        tree.delete(i)
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        cpu = proc.info['cpu_percent']
        mem = proc.info['memory_percent']
        cpu_str = f"{cpu:.1f}" if cpu is not None else "N/A"
        mem_str = f"{mem:.1f}" if mem is not None else "N/A"
        tree.insert("", "end", values=(proc.info['pid'], proc.info['name'], cpu_str, mem_str))
    root.after(5000, update_process_list)

# Search Process Function
def search_process(name):
    if not name.strip():
        messagebox.showwarning("Warning", "Please enter a process name to search")
        return
    for item in tree.get_children():
        values = tree.item(item, "values")
        if name.lower() in values[1].lower():  # values[1] is the process name
            tree.selection_set(item)  # Highlight the row
            tree.see(item)  # Scroll to the row
            log.insert(tk.END, f"Found process: {values[1]} (PID: {values[0]})\n")
            log.see(tk.END)
            return
    log.insert(tk.END, f"No process found matching '{name}'\n")
    messagebox.showinfo("Search Result", f"No process found matching '{name}'")

# Process Management Functions
def start_process(app):
    try:
        if OS == "Windows":
            subprocess.Popen(app + ".exe")
        elif OS == "Darwin":  # macOS
            subprocess.Popen(["open", "-a", app])
        log.insert(tk.END, f"Started {app}\n")
    except Exception as e:
        log.insert(tk.END, f"Error starting {app}: {e}\n")
        messagebox.showerror("Error", f"Failed to start {app}")

def kill_process(pid):
    try:
        pid = int(pid)
        p = psutil.Process(pid)
        p.terminate()
        time.sleep(0.5)
        if p.is_running():
            p.kill()
        log.insert(tk.END, f"Killed process {pid}\n")
    except psutil.NoSuchProcess:
        log.insert(tk.END, f"Error: Process {pid} does not exist\n")
        messagebox.showerror("Error", f"Process {pid} not found")
    except psutil.AccessDenied:
        log.insert(tk.END, f"Error: Permission denied to kill {pid}. Try running with sudo.\n")
        messagebox.showerror("Error", f"Permission denied for {pid}. Run with sudo.")
    except ValueError:
        log.insert(tk.END, f"Error: Invalid PID '{pid}' - must be a number\n")
        messagebox.showerror("Error", "Invalid PID - enter a number")
    except Exception as e:
        log.insert(tk.END, f"Error killing {pid}: {e}\n")
        messagebox.showerror("Error", f"Failed to kill {pid}: {e}")

def prioritize_process(app):
    for proc in psutil.process_iter(['name']):
        if app.lower() in proc.info['name'].lower():
            proc.nice(-10 if OS == "Windows" else 10)
            log.insert(tk.END, f"Prioritized {app}\n")
            break

def check_deadlock():
    log.insert(tk.END, "Simulating deadlock check...\n")
    time.sleep(2)
    log.insert(tk.END, "No deadlock detected (simulated).\n")

def ipc_process(conn):
    conn.send("Hello from child!")
    conn.close()

def start_ipc_demo():
    parent_conn, child_conn = Pipe()
    p = Process(target=ipc_process, args=(child_conn,))
    p.start()
    log.insert(tk.END, f"IPC Message: {parent_conn.recv()}\n")
    p.join()

lock = threading.Lock()
shared_counter = 0

def increment_counter():
    global shared_counter
    with lock:
        temp = shared_counter
        time.sleep(0.1)
        shared_counter = temp + 1

def start_sync_demo():
    global shared_counter
    shared_counter = 0
    threads = [threading.Thread(target=increment_counter) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    log.insert(tk.END, f"Synchronized counter: {shared_counter}\n")

# Voice Command Handler
def get_voice_command():
    with sr.Microphone() as source:
        status_label.config(text="Status: Listening...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio).lower()
            log.insert(tk.END, f"You said: {command}\n")
            log.see(tk.END)
            process_command(command)
            status_label.config(text="Status: Command processed")
        except sr.UnknownValueError:
            log.insert(tk.END, "Didn’t understand that.\n")
            status_label.config(text="Status: Unrecognized command")
        except sr.RequestError:
            log.insert(tk.END, "Speech service error.\n")
            status_label.config(text="Status: Speech service error")

def process_command(command):
    if "list processes" in command:
        update_process_list()
    elif "start" in command:
        app = command.replace("start ", "")
        start_process(app)
    elif "kill" in command:
        pid = command.replace("kill ", "")
        kill_process(pid)
    elif "prioritize" in command:
        app = command.replace("prioritize ", "")
        prioritize_process(app)
    elif "check deadlock" in command:
        check_deadlock()
    elif "start ipc" in command:
        start_ipc_demo()
    elif "start sync" in command:
        start_sync_demo()

# Start Voice Listener
def voice_loop():
    while True:
        get_voice_command()

threading.Thread(target=voice_loop, daemon=True).start()
update_process_list()
root.mainloop()
