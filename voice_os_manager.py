import speech_recognition as sr
import psutil
import subprocess
import platform
import tkinter as tk
from tkinter import ttk
import threading
import time
from multiprocessing import Process, Pipe

# GUI Setup
root = tk.Tk()
root.title("VoiceOS Manager")
root.geometry("800x600")

# Process List
tree = ttk.Treeview(root, columns=("PID", "Name", "CPU"), show="headings")
tree.heading("PID", text="PID")
tree.heading("Name", text="Process Name")
tree.heading("CPU", text="CPU %")
tree.pack(fill="both", expand=True)

# Status Log
log = tk.Text(root, height=5)
log.pack(fill="x")

# Voice Recognizer
recognizer = sr.Recognizer()

# OS Detection
OS = platform.system()

# Update Process List
def update_process_list():
    for i in tree.get_children():
        tree.delete(i)
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        tree.insert("", "end", values=(proc.info['pid'], proc.info['name'], proc.info['cpu_percent']))
    root.after(5000, update_process_list)  # Refresh every 5s

# Voice Command Handler
def get_voice_command():
    with sr.Microphone() as source:
        log.insert(tk.END, "Listening...\n")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio).lower()
            log.insert(tk.END, f"You said: {command}\n")
            process_command(command)
        except sr.UnknownValueError:
            log.insert(tk.END, "Didn’t understand that.\n")
        except sr.RequestError:
            log.insert(tk.END, "Speech service error.\n")

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

def kill_process(pid):
    try:
        p = psutil.Process(int(pid))
        p.terminate()
        log.insert(tk.END, f"Killed process {pid}\n")
    except Exception as e:
        log.insert(tk.END, f"Error killing {pid}: {e}\n")

def prioritize_process(app):
    for proc in psutil.process_iter(['name']):
        if app.lower() in proc.info['name'].lower():
            proc.nice(-10 if OS == "Windows" else 10)  # Higher priority
            log.insert(tk.END, f"Prioritized {app}\n")
            break

# Deadlock Simulation
def check_deadlock():
    # Simplified: Check if two processes are waiting indefinitely (toy example)
    log.insert(tk.END, "Simulating deadlock check...\n")
    time.sleep(2)
    log.insert(tk.END, "No deadlock detected (simulated).\n")

# IPC Demo
def ipc_process(conn):
    conn.send("Hello from child!")
    conn.close()

def start_ipc_demo():
    parent_conn, child_conn = Pipe()
    p = Process(target=ipc_process, args=(child_conn,))
    p.start()
    log.insert(tk.END, f"IPC Message: {parent_conn.recv()}\n")
    p.join()

# Sync Demo
lock = threading.Lock()
shared_counter = 0

def increment_counter():
    global shared_counter
    with lock:
        temp = shared_counter
        time.sleep(0.1)  # Simulate work
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

# Start Voice Listener
def voice_loop():
    while True:
        get_voice_command()

# Run GUI and Voice in Parallel
threading.Thread(target=voice_loop, daemon=True).start()
update_process_list()
root.mainloop()
