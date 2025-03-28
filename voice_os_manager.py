import speech_recognition as sr
import psutil
import subprocess
import platform
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from multiprocessing import Process, Pipe
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ttkthemes import ThemedTk
from PIL import Image, ImageTk, ImageDraw

# Function to make the mic image round
def make_image_round(image_path, size):
    img = Image.open(image_path).convert("RGBA")
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    img.putalpha(mask)
    return img

# GUI Setup with Theme
root = ThemedTk(theme="equilux")
root.title("VoiceOS Manager")
root.geometry("800x600")
root.configure(bg="#3A4A4B")

# Make the window resizable and allow full-screen
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

# Styling
style = ttk.Style()
style.configure("Treeview", background="#3A4A4B", foreground="#66DFFF", fieldbackground="#3A4A4B", rowheight=25)
style.configure("Treeview.Heading", background="#4A5A5B", foreground="#66DFFF", font=("Orbitron", 10, "bold"))
style.map("Treeview", background=[("selected", "#66DFFF")])
style.configure("TButton", font=("Orbitron", 9), padding=6, background="#66DFFF", foreground="white")
style.map("TButton", background=[("active", "#99EFFF")])

# Header
header = tk.Label(root, text="VoiceOS Manager", font=("Orbitron", 16, "bold"), bg="#3A4A4B", fg="white")
header.grid(row=0, column=0, pady=10, sticky="ew")

# Process List (Top)
process_frame = tk.Frame(root, bg="#3A4A4B")
process_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
process_frame.columnconfigure(0, weight=1)
process_label = tk.Label(process_frame, text="VOICESS PROCESS", font=("Orbitron", 10, "bold"), bg="#3A4A4B", fg="white")
process_label.pack(fill="x")
tree = ttk.Treeview(process_frame, columns=("PID", "Name", "CPU", "Memory"), show="headings", height=8)
tree.heading("PID", text="PID")
tree.heading("Name", text="Process Name")
tree.heading("CPU", text="CPU %")
tree.heading("Memory", text="Memory %")
tree.pack(fill="both", expand=True)

scrollbar = ttk.Scrollbar(process_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# Function to resize Treeview columns dynamically
def resize_columns(event=None):
    tree_width = tree.winfo_width() - scrollbar.winfo_width()
    if tree_width < 400:
        tree_width = 400
    pid_width = tree_width // 6
    name_width = tree_width // 2
    cpu_width = tree_width // 6
    mem_width = tree_width // 6
    total = pid_width + name_width + cpu_width + mem_width
    if total < tree_width:
        name_width += (tree_width - total)
    tree.column("PID", width=pid_width, anchor="center")
    tree.column("Name", width=name_width)
    tree.column("CPU", width=cpu_width, anchor="center")
    tree.column("Memory", width=mem_width, anchor="center")

root.bind("<Configure>", resize_columns)

# Control Buttons (Centered in Middle)
control_frame = tk.Frame(root, bg="#3A4A4B")
control_frame.grid(row=2, column=0, pady=10, sticky="ew")

# Inner frame to group buttons and center them
button_frame = tk.Frame(control_frame, bg="#3A4A4B")
button_frame.pack(anchor="center")

# Start Process
start_frame = tk.Frame(button_frame, bg="#3A4A4B")
start_frame.pack(side="left", padx=5)
start_label = tk.Label(start_frame, text="START PROCESS", font=("Orbitron", 9, "bold"), bg="#3A4A4B", fg="white")
start_label.pack()
start_entry = tk.Entry(start_frame, width=15, bg="#4A5A5B", fg="white", insertbackground="white", font=("Orbitron", 8))
start_entry.pack(pady=2)
start_btn = ttk.Button(start_frame, text="Start", command=lambda: start_process(start_entry.get()))
start_btn.pack()

# Kill Process
kill_frame = tk.Frame(button_frame, bg="#3A4A4B")
kill_frame.pack(side="left", padx=5)
kill_label = tk.Label(kill_frame, text="KILL PROCESS", font=("Orbitron", 9, "bold"), bg="#3A4A4B", fg="white")
kill_label.pack()
kill_entry = tk.Entry(kill_frame, width=10, bg="#4A5A5B", fg="white", insertbackground="white", font=("Orbitron", 8))
kill_entry.pack(pady=2)
kill_btn = ttk.Button(kill_frame, text="Kill", command=lambda: kill_process(kill_entry.get()))
kill_btn.pack()

# Prioritize Task
prioritize_frame = tk.Frame(button_frame, bg="#3A4A4B")
prioritize_frame.pack(side="left", padx=5)
prioritize_label = tk.Label(prioritize_frame, text="PRIORITIZE TASK", font=("Orbitron", 9, "bold"), bg="#3A4A4B", fg="white")
prioritize_label.pack()
prioritize_entry = tk.Entry(prioritize_frame, width=15, bg="#4A5A5B", fg="white", insertbackground="white", font=("Orbitron", 8))
prioritize_entry.pack(pady=2)
prioritize_btn = ttk.Button(prioritize_frame, text="Prioritize", command=lambda: prioritize_process(prioritize_entry.get()))
prioritize_btn.pack()

# Search Process (with Mic Icon)
search_frame = tk.Frame(button_frame, bg="#3A4A4B")
search_frame.pack(side="left", padx=5)
search_label = tk.Label(search_frame, text="SEARCH PROCESS", font=("Orbitron", 9, "bold"), bg="#3A4A4B", fg="white")
search_label.pack()
search_inner_frame = tk.Frame(search_frame, bg="#3A4A4B")
search_inner_frame.pack()
search_entry = tk.Entry(search_inner_frame, width=15, bg="#4A5A5B", fg="white", insertbackground="white", font=("Orbitron", 8))
search_entry.pack(side="left", pady=2)
mic_img_pil = make_image_round("/Users/harshkumar/Python Tutorial/College PPTs/VoiceOSManager/mic.png", 20)
mic_img = ImageTk.PhotoImage(mic_img_pil)
mic_label = tk.Label(search_inner_frame, image=mic_img, bg="#3A4A4B")
mic_label.pack(side="left", padx=5)
search_btn = ttk.Button(search_frame, text="Search", command=lambda: search_process(search_entry.get()))
search_btn.pack()

# Graph and Listening (Row 3)
bottom_frame = tk.Frame(root, bg="#3A4A4B")
bottom_frame.grid(row=3, column=0, pady=10, sticky="ew")
fig, ax = plt.subplots(figsize=(3, 1.5), facecolor="#3A4A4B")
ax.set_facecolor("#4A5A5B")
ax.tick_params(colors="white", labelsize=6)
canvas = FigureCanvasTkAgg(fig, master=bottom_frame)
canvas.get_tk_widget().pack()
listening_label = tk.Label(bottom_frame, text="LISTENING...", font=("Orbitron", 10), bg="#3A4A4B", fg="#FF99FF")
listening_label.pack()
def pulse_listening():
    current_color = listening_label.cget("fg")
    listening_label.config(fg="#FFCCFF" if current_color == "#FF99FF" else "#FF99FF")
    root.after(500, pulse_listening)
pulse_listening()

# Voice Recognizer & OS Detection
recognizer = sr.Recognizer()
OS = platform.system()

# Process List Management
def update_process_list():
    for i in tree.get_children():
        tree.delete(i)
    for idx, proc in enumerate(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])):
        cpu = proc.info['cpu_percent']
        mem = proc.info['memory_percent']
        cpu_str = f"{cpu:.1f}" if cpu is not None else "N/A"
        mem_str = f"{mem:.1f}" if mem is not None else "N/A"
        tree.insert("", "end", values=(proc.info['pid'], proc.info['name'], cpu_str, mem_str), tags=("even" if idx % 2 == 0 else "odd"))
    tree.tag_configure("even", background="#3A4A4B")
    tree.tag_configure("odd", background="#4A5A5B")
    update_graph()
    root.after(5000, update_process_list)

def search_process(name):
    if not name.strip():
        messagebox.showwarning("Warning", "Enter a process name")
        return
    for item in tree.get_children():
        if name.lower() in tree.item(item, "values")[1].lower():
            tree.selection_set(item)
            tree.see(item)
            return
    messagebox.showinfo("Search Result", f"No process found matching '{name}'")

# Graph Update
cpu_data, mem_data = [], []
def update_graph():
    total_cpu = psutil.cpu_percent()
    total_mem = psutil.virtual_memory().percent
    cpu_data.append(total_cpu)
    mem_data.append(total_mem)
    if len(cpu_data) > 2:
        cpu_data.pop(0)
        mem_data.pop(0)
    ax.clear()
    ax.bar([0], [cpu_data[-1]], color="#66DFFF", width=0.4)
    ax.bar([1], [mem_data[-1]], color="#FF99FF", width=0.4)
    ax.set_ylim(0, 100)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["CPU", "Memory"], fontsize=6, color="white")
    canvas.draw()
    root.after(5000, update_graph)

# Process Management Functions
def start_process(app):
    try:
        if OS == "Windows":
            subprocess.Popen(app + ".exe")
        elif OS == "Darwin":
            subprocess.Popen(["open", "-a", app])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start {app}: {e}")

def kill_process(pid):
    try:
        pid = int(pid)
        p = psutil.Process(pid)
        p.terminate()
        time.sleep(0.5)
        if p.is_running():
            p.kill()
    except psutil.NoSuchProcess:
        messagebox.showerror("Error", f"Process {pid} not found")
    except psutil.AccessDenied:
        messagebox.showerror("Error", f"Permission denied for {pid}. Run with sudo.")
    except ValueError:
        messagebox.showerror("Error", "Invalid PID - enter a number")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to kill {pid}: {e}")

def prioritize_process(app):
    if not app.strip():
        messagebox.showwarning("Warning", "Enter a process name to prioritize")
        return
    found = False
    for proc in psutil.process_iter(['name']):
        if app.lower() in proc.info['name'].lower():
            try:
                proc.nice(-10 if OS == "Windows" else 10)
                messagebox.showinfo("Success", f"Prioritized {app}")
                found = True
                break
            except psutil.AccessDenied:
                messagebox.showerror("Error", f"Permission denied for {app}. Run with sudo.")
                return
    if not found:
        messagebox.showerror("Error", f"Process {app} not found")

def check_deadlock():
    time.sleep(2)

def ipc_process(conn):
    conn.send("Hello from child!")
    conn.close()

def start_ipc_demo():
    parent_conn, child_conn = Pipe()
    p = Process(target=ipc_process, args=(child_conn,))
    p.start()
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

# Voice Command Handler
def get_voice_command():
    with sr.Microphone() as source:
        listening_label.config(text="LISTENING...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio).lower()
            process_command(command)
            listening_label.config(text="Command processed")
        except sr.UnknownValueError:
            listening_label.config(text="Unrecognized command")
        except sr.RequestError:
            listening_label.config(text="Speech service error")

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
update_graph()
root.mainloop()
