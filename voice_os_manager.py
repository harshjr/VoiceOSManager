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
import os
from datetime import datetime

class SecurityManager:
    def __init__(self):
        self.username = "harsh123"
        self.password = "harshpassword1"
    def authenticate(self, username, password):
        return username == self.username and password == self.password

class LoginWindow:
    def __init__(self, root, on_success_callback):
        self.root = root
        self.on_success_callback = on_success_callback
        self.security_manager = SecurityManager()
        self.root.title("VoiceOS Manager Login")
        self.root.geometry("400x300")
        self.root.configure(bg="#1E1E1E")
        self.show_login_screen()
    def show_login_screen(self):
        self.login_frame = tk.Frame(self.root, bg="#1E1E1E")
        self.login_frame.pack(expand=True)
        tk.Label(self.login_frame, text="VoiceOS Manager Login", font=("Arial", 16)).pack(pady=20)
        tk.Label(self.login_frame, text="Username:").pack()
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.pack(pady=5)
        tk.Label(self.login_frame, text="Password:").pack()
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.pack(pady=5)
        tk.Button(self.login_frame, text="Login", command=self.validate_login).pack(pady=20)
    def validate_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if self.security_manager.authenticate(username, password):
            self.login_frame.destroy()
            self.on_success_callback()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

def make_image_round(image_path, size):
    img = Image.open(image_path).convert("RGBA")
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    img.putalpha(mask)
    return img

class VoiceOSManager:
    def __init__(self, root):
        self.root = root
        self.root.title("VoiceOS Manager")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1E1E1E")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.style = ttk.Style()
        self.style.configure("Treeview", background="#2D2D2D", foreground="white", fieldbackground="#2D2D2D", rowheight=30)
        self.style.configure("Treeview.Heading", background="#1E1E1E", foreground="#66DFFF", font=("Orbitron", 10, "bold"))
        self.style.map("Treeview", background=[("selected", "#66DFFF")], foreground=[("selected", "black")])
        self.style.configure("TButton", font=("Orbitron", 9), padding=6, background="#66DFFF", foreground="black")
        self.style.map("TButton", background=[("active", "#99EFFF")])
        self.recognizer = sr.Recognizer()
        self.OS = platform.system()
        self.current_search_term = ""
        self.lock = threading.Lock()
        self.shared_counter = 0
        self.cpu_data, self.mem_data = [], []
        self.setup_gui()
        self.update_process_list()
        self.update_graph()
        self.update_status_bar()
        threading.Thread(target=self.voice_loop, daemon=True).start()
    def setup_gui(self):
        self.header_frame = tk.Frame(self.root, bg="#1E1E1E")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.header = tk.Label(self.header_frame, text="VoiceOS Manager", font=("Orbitron", 24, "bold"), bg="#1E1E1E", fg="#66DFFF")
        self.header.pack(side="left")
        self.system_info = tk.Label(self.header_frame, text=f"OS: {platform.system()} {platform.release()}", font=("Orbitron", 10), bg="#1E1E1E", fg="white")
        self.system_info.pack(side="right")
        self.content_frame = tk.Frame(self.root, bg="#1E1E1E")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        self.setup_process_list()
        self.setup_control_panel()
        self.setup_resource_monitor()
        self.setup_status_bar()
    def setup_process_list(self):
        process_frame = tk.Frame(self.content_frame, bg="#1E1E1E")
        process_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        process_frame.columnconfigure(0, weight=1)
        process_frame.rowconfigure(1, weight=1)
        
        # Process List Header with enhanced styling
        process_header = tk.Frame(process_frame, bg="#1E1E1E")
        process_header.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Title with gradient effect
        title_label = tk.Label(
            process_header,
            text="Running Processes",
            font=("Orbitron", 14, "bold"),
            bg="#1E1E1E",
            fg="#66DFFF"
        )
        title_label.pack(side="left")
        
        # Search Frame with enhanced styling
        search_frame = tk.Frame(process_header, bg="#1E1E1E")
        search_frame.pack(side="right")
        
        # Search Entry with placeholder
        self.search_entry = tk.Entry(
            search_frame,
            width=30,
            bg="#2D2D2D",
            fg="white",
            insertbackground="white",
            font=("Orbitron", 9)
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.insert(0, "Search processes...")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0, "end") if self.search_entry.get() == "Search processes..." else None)
        self.search_entry.bind("<FocusOut>", lambda e: self.search_entry.insert(0, "Search processes...") if not self.search_entry.get() else None)
        self.search_entry.bind("<KeyRelease>", self.on_search_entry_change)
        
        # Search Button with enhanced styling
        search_btn = ttk.Button(
            search_frame,
            text="Search",
            command=lambda: self.search_process(self.search_entry.get()),
            style="Accent.TButton"
        )
        search_btn.pack(side="left", padx=5)
        
        # Process Treeview with enhanced styling
        self.tree = ttk.Treeview(
            process_frame,
            columns=("PID", "Name", "CPU", "Memory", "Status"),
            show="headings",
            height=15,
            style="Custom.Treeview"
        )
        self.tree.grid(row=1, column=0, sticky="nsew")
        
        # Configure Treeview Headings with enhanced styling
        self.tree.heading("PID", text="PID", command=lambda: self.sort_column("PID", False))
        self.tree.heading("Name", text="Process Name", command=lambda: self.sort_column("Name", False))
        self.tree.heading("CPU", text="CPU %", command=lambda: self.sort_column("CPU", False))
        self.tree.heading("Memory", text="Memory %", command=lambda: self.sort_column("Memory", False))
        self.tree.heading("Status", text="Status", command=lambda: self.sort_column("Status", False))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(process_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure custom styles
        self.style.configure(
            "Custom.Treeview",
            background="#2D2D2D",
            foreground="white",
            fieldbackground="#2D2D2D",
            rowheight=30,
            font=("Orbitron", 9)
        )
        self.style.configure(
            "Custom.Treeview.Heading",
            background="#1E1E1E",
            foreground="#66DFFF",
            font=("Orbitron", 10, "bold")
        )
        self.style.configure(
            "Accent.TButton",
            font=("Orbitron", 9, "bold"),
            background="#66DFFF",
            foreground="black",
            padding=5
        )
        self.style.map(
            "Accent.TButton",
            background=[("active", "#99EFFF")],
            foreground=[("active", "black")]
        )
    def setup_control_panel(self):
        control_frame = tk.Frame(self.content_frame, bg="#1E1E1E")
        control_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Control Panel Title
        control_title = tk.Label(
            control_frame,
            text="Process Controls",
            font=("Orbitron", 14, "bold"),
            bg="#1E1E1E",
            fg="#66DFFF"
        )
        control_title.pack(pady=(0, 10))
        
        button_frame = tk.Frame(control_frame, bg="#1E1E1E")
        button_frame.pack(expand=True)
        
        # Start Process Frame
        start_frame = tk.Frame(button_frame, bg="#1E1E1E")
        start_frame.pack(side="left", padx=10)
        
        start_label = tk.Label(
            start_frame,
            text="Start Process",
            font=("Orbitron", 11, "bold"),
            bg="#1E1E1E",
            fg="#66DFFF"
        )
        start_label.pack()
        
        self.start_entry = tk.Entry(
            start_frame,
            width=20,
            bg="#2D2D2D",
            fg="white",
            insertbackground="white",
            font=("Orbitron", 9)
        )
        self.start_entry.pack(pady=2)
        
        start_btn = ttk.Button(
            start_frame,
            text="Start",
            command=lambda: self.start_process(self.start_entry.get()),
            style="Accent.TButton"
        )
        start_btn.pack()
        
        # Kill Process Frame
        kill_frame = tk.Frame(button_frame, bg="#1E1E1E")
        kill_frame.pack(side="left", padx=10)
        
        kill_label = tk.Label(
            kill_frame,
            text="Kill Process",
            font=("Orbitron", 11, "bold"),
            bg="#1E1E1E",
            fg="#FF6666"
        )
        kill_label.pack()
        
        self.kill_entry = tk.Entry(
            kill_frame,
            width=20,
            bg="#2D2D2D",
            fg="white",
            insertbackground="white",
            font=("Orbitron", 9)
        )
        self.kill_entry.pack(pady=2)
        
        kill_btn = ttk.Button(
            kill_frame,
            text="Kill",
            command=lambda: self.kill_process(self.kill_entry.get()),
            style="Accent.TButton"
        )
        kill_btn.pack()
        
        # Prioritize Process Frame
        prioritize_frame = tk.Frame(button_frame, bg="#1E1E1E")
        prioritize_frame.pack(side="left", padx=10)
        
        prioritize_label = tk.Label(
            prioritize_frame,
            text="Prioritize Process",
            font=("Orbitron", 11, "bold"),
            bg="#1E1E1E",
            fg="#99FF99"
        )
        prioritize_label.pack()
        
        self.prioritize_entry = tk.Entry(
            prioritize_frame,
            width=20,
            bg="#2D2D2D",
            fg="white",
            insertbackground="white",
            font=("Orbitron", 9)
        )
        self.prioritize_entry.pack(pady=2)
        
        prioritize_btn = ttk.Button(
            prioritize_frame,
            text="Prioritize",
            command=lambda: self.prioritize_process(self.prioritize_entry.get()),
            style="Accent.TButton"
        )
        prioritize_btn.pack()
    def setup_resource_monitor(self):
        monitor_frame = tk.Frame(self.content_frame, bg="#1E1E1E")
        monitor_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        graph_frame = tk.Frame(monitor_frame, bg="#1E1E1E")
        graph_frame.pack(expand=True, fill="both")
        cpu_frame = tk.Frame(graph_frame, bg="#1E1E1E")
        cpu_frame.pack(side="left", expand=True, fill="both", padx=5)
        tk.Label(cpu_frame, text="CPU Usage", font=("Orbitron", 10, "bold"), bg="#1E1E1E", fg="white").pack()
        self.cpu_fig, self.cpu_ax = plt.subplots(figsize=(4, 2), facecolor="#1E1E1E")
        self.cpu_ax.set_facecolor("#2D2D2D")
        self.cpu_ax.tick_params(colors="white", labelsize=8)
        self.cpu_canvas = FigureCanvasTkAgg(self.cpu_fig, master=cpu_frame)
        self.cpu_canvas.get_tk_widget().pack(expand=True, fill="both")
        mem_frame = tk.Frame(graph_frame, bg="#1E1E1E")
        mem_frame.pack(side="left", expand=True, fill="both", padx=5)
        tk.Label(mem_frame, text="Memory Usage", font=("Orbitron", 10, "bold"), bg="#1E1E1E", fg="white").pack()
        self.mem_fig, self.mem_ax = plt.subplots(figsize=(4, 2), facecolor="#1E1E1E")
        self.mem_ax.set_facecolor("#2D2D2D")
        self.mem_ax.tick_params(colors="white", labelsize=8)
        self.mem_canvas = FigureCanvasTkAgg(self.mem_fig, master=mem_frame)
        self.mem_canvas.get_tk_widget().pack(expand=True, fill="both")
    def setup_status_bar(self):
        self.status_bar = tk.Frame(self.root, bg="#1E1E1E", height=25)
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        self.status_label = tk.Label(self.status_bar, text="Ready", font=("Orbitron", 9), bg="#1E1E1E", fg="white")
        self.status_label.pack(side="left")
        self.voice_status = tk.Label(self.status_bar, text="Listening...", font=("Orbitron", 9), bg="#1E1E1E", fg="#FF99FF")
        self.voice_status.pack(side="right")
    def update_status_bar(self):
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used / (1024 * 1024 * 1024)  # Convert to GB
        status_text = f"CPU: {cpu_percent}% | Memory: {memory_percent}% ({memory_used:.1f} GB used)"
        self.status_label.config(text=status_text)
        self.root.after(1000, self.update_status_bar)
    def sort_column(self, col, reverse):
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children("")]
        items.sort(reverse=reverse)
        for index, (val, item) in enumerate(items):
            self.tree.move(item, "", index)
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))
    def update_process_list(self):
        search_term = self.current_search_term.lower()
        for i in self.tree.get_children():
            self.tree.delete(i)
        processes = []
        for idx, proc in enumerate(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status'])):
            try:
                cpu = proc.info['cpu_percent']
                mem = proc.info['memory_percent']
                status = proc.info['status']
                cpu_str = f"{cpu:.1f}" if cpu is not None else "N/A"
                mem_str = f"{mem:.1f}" if mem is not None else "N/A"
                processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "cpu": cpu_str,
                    "mem": mem_str,
                    "status": status,
                    "idx": idx
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        processes.sort(key=lambda x: (x["name"].lower(), x["pid"]))
        if search_term:
            filtered_processes = [p for p in processes if search_term in p["name"].lower()]
        else:
            filtered_processes = processes
        for p in filtered_processes:
            self.tree.insert("", "end", values=(p["pid"], p["name"], p["cpu"], p["mem"], p["status"]), tags=("even" if p["idx"] % 2 == 0 else "odd"))
        self.tree.tag_configure("even", background="#2D2D2D")
        self.tree.tag_configure("odd", background="#1E1E1E")
        self.root.after(5000, self.update_process_list)
    def search_process(self, name):
        if not name.strip():
            messagebox.showwarning("Warning", "Enter a process name")
            self.current_search_term = ""
            self.search_entry.delete(0, tk.END)
            return
        self.current_search_term = name
        self.update_process_list()
    def on_search_entry_change(self, *args):
        search_term = self.search_entry.get()
        if not search_term.strip():
            self.current_search_term = ""
            self.update_process_list()
        else:
            self.current_search_term = search_term
            self.update_process_list()
    def update_graph(self):
        if not hasattr(self, 'cpu_ax') or not hasattr(self, 'mem_ax'):
            self.root.after(5000, self.update_graph)
            return
        total_cpu = psutil.cpu_percent()
        self.cpu_data.append(total_cpu)
        if len(self.cpu_data) > 20:
            self.cpu_data.pop(0)
        self.cpu_ax.clear()
        self.cpu_ax.plot(self.cpu_data, color="#66DFFF", linewidth=2)
        self.cpu_ax.set_ylim(0, 100)
        self.cpu_ax.set_facecolor("#2D2D2D")
        self.cpu_ax.tick_params(colors="white", labelsize=8)
        self.cpu_canvas.draw()
        total_mem = psutil.virtual_memory().percent
        self.mem_data.append(total_mem)
        if len(self.mem_data) > 20:
            self.mem_data.pop(0)
        self.mem_ax.clear()
        self.mem_ax.plot(self.mem_data, color="#FF99FF", linewidth=2)
        self.mem_ax.set_ylim(0, 100)
        self.mem_ax.set_facecolor("#2D2D2D")
        self.mem_ax.tick_params(colors="white", labelsize=8)
        self.mem_canvas.draw()
        self.root.after(1000, self.update_graph)
    def start_process(self, app):
        try:
            if self.OS == "Windows":
                if not app.lower().endswith(".exe"):
                    app = app + ".exe"
                subprocess.Popen([app], shell=True)
            elif self.OS == "Darwin":
                subprocess.Popen(["open", "-a", app])
            else:
                messagebox.showerror("Error", f"Unsupported OS: {self.OS}")
        except FileNotFoundError:
            messagebox.showerror("Error", f"Application '{app}' not found. Please check the name and try again.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start {app}: {e}")
    def kill_process(self, identifier):
        if not identifier.strip():
            messagebox.showerror("Error", "Please enter a PID or process name")
            return
        try:
            pid = int(identifier)
            try:
                p = psutil.Process(pid)
                process_name = p.name()
                p.terminate()
                time.sleep(0.5)
                if p.is_running():
                    p.kill()
                messagebox.showinfo("Success", f"Process {process_name} (PID: {pid}) terminated successfully")
            except psutil.NoSuchProcess:
                messagebox.showerror("Error", f"Process with PID {pid} not found")
            except psutil.AccessDenied:
                messagebox.showerror("Error", f"Permission denied for PID {pid}. Run with sudo/admin privileges.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to kill PID {pid}: {e}")
        except ValueError:
            process_name = identifier
            found = False
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'].lower() == process_name.lower():
                    try:
                        proc.terminate()
                        time.sleep(0.5)
                        if proc.is_running():
                            proc.kill()
                        messagebox.showinfo("Success", f"Process {process_name} (PID: {proc.info['pid']}) terminated successfully")
                        found = True
                        break
                    except psutil.NoSuchProcess:
                        continue
                    except psutil.AccessDenied:
                        messagebox.showerror("Error", f"Permission denied for {process_name} (PID: {proc.info['pid']}). Run with sudo/admin privileges.")
                        return
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to kill {process_name}: {e}")
                        return
            if not found:
                messagebox.showerror("Error", f"Process {process_name} not found")
    def prioritize_process(self, app):
        if not app.strip():
            messagebox.showwarning("Warning", "Enter a process name to prioritize")
            return
        found = False
        for proc in psutil.process_iter(['name']):
            if app.lower() in proc.info['name'].lower():
                try:
                    if self.OS == "Windows":
                        proc.nice(-10)
                    elif self.OS == "Darwin":
                        proc.nice(-10)
                    else:
                        messagebox.showerror("Error", f"Unsupported OS: {self.OS}")
                        return
                    messagebox.showinfo("Success", f"Prioritized {app}")
                    found = True
                    break
                except psutil.AccessDenied:
                    messagebox.showerror("Error", f"Permission denied for {app}. Run with sudo/admin privileges.")
                    return
        if not found:
            messagebox.showerror("Error", f"Process {app} not found")
    def check_deadlock(self):
        time.sleep(2)
    def ipc_process(self, conn):
        conn.send("Hello from child!")
        conn.close()
    def start_ipc_demo(self):
        parent_conn, child_conn = Pipe()
        p = Process(target=self.ipc_process, args=(child_conn,))
        p.start()
        p.join()
    def increment_counter(self):
        with self.lock:
            temp = self.shared_counter
            time.sleep(0.1)
            self.shared_counter = temp + 1
    def start_sync_demo(self):
        self.shared_counter = 0
        threads = [threading.Thread(target=self.increment_counter) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    def get_voice_command(self):
        with sr.Microphone() as source:
            self.voice_status.config(text="LISTENING...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                command = self.recognizer.recognize_google(audio).lower()
                self.process_command(command)
                self.voice_status.config(text="Command processed")
            except sr.UnknownValueError:
                self.voice_status.config(text="Unrecognized command")
            except sr.RequestError:
                self.voice_status.config(text="Speech service error")
            except sr.WaitTimeoutError:
                self.voice_status.config(text="No command detected")
            except Exception as e:
                self.voice_status.config(text=f"Error: {e}")
    def process_command(self, command):
        if "list processes" in command:
            self.update_process_list()
        elif "start" in command:
            app = command.replace("start ", "")
            self.start_process(app)
        elif "kill" in command:
            identifier = command.replace("kill ", "")
            self.kill_process(identifier)
        elif "prioritize" in command:
            app = command.replace("prioritize ", "")
            self.prioritize_process(app)
        elif "check deadlock" in command:
            self.check_deadlock()
        elif "start ipc" in command:
            self.start_ipc_demo()
        elif "start sync" in command:
            self.start_sync_demo()
    def voice_loop(self):
        while True:
            self.get_voice_command()

def main():
    root = ThemedTk(theme="equilux")
    def show_voiceos_manager():
        voiceos_manager = VoiceOSManager(root)
    login_window = LoginWindow(root, show_voiceos_manager)
    root.mainloop()

if __name__ == "__main__":
    main()
