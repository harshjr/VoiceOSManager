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
        self.show_login_screen()
    def show_login_screen(self):
        self.login_frame = tk.Frame(self.root)
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
        self.root.geometry("800x600")
        self.root.configure(bg="#3A4A4B")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.style = ttk.Style()
        self.style.configure("Treeview", background="#3A4A4B", foreground="#66DFFF", fieldbackground="#3A4A4B", rowheight=25)
        self.style.configure("Treeview.Heading", background="#4A5A5B", foreground="#66DFFF", font=("Orbitron", 10, "bold"))
        self.style.map("Treeview", background=[("selected", "#66DFFF")])
        self.style.configure("TButton", font=("Orbitron", 9), padding=6, background="#66DFFF", foreground="white")
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
        threading.Thread(target=self.voice_loop, daemon=True).start()
    def setup_gui(self):
        self.header = tk.Label(self.root, text="VoiceOS Manager", font=("Orbitron", 16, "bold"), bg="#3A4A4B", fg="white")
        self.header.grid(row=0, column=0, pady=10, sticky="ew")
        self.process_frame = tk.Frame(self.root, bg="#3A4A4B")
        self.process_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.process_frame.columnconfigure(0, weight=1)
        self.process_label = tk.Label(self.process_frame, text="VOICESS PROCESS", font=("Orbitron", 10, "bold"), bg="#3A4A4B", fg="white")
        self.process_label.pack(fill="x")
        self.tree = ttk.Treeview(self.process_frame, columns=("PID", "Name", "CPU", "Memory"), show="headings", height=8)
        self.tree.heading("PID", text="PID")
        self.tree.heading("Name", text="Process Name")
        self.tree.heading("CPU", text="CPU %")
        self.tree.heading("Memory", text="Memory %")
        self.tree.pack(fill="both", expand=True)
        self.scrollbar = ttk.Scrollbar(self.process_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        def resize_columns(event=None):
            tree_width = self.tree.winfo_width() - self.scrollbar.winfo_width()
            if tree_width < 400:
                tree_width = 400
            pid_width = tree_width // 6
            name_width = tree_width // 2
            cpu_width = tree_width // 6
            mem_width = tree_width // 6
            total = pid_width + name_width + cpu_width + mem_width
            if total < tree_width:
                name_width += (tree_width - total)
            self.tree.column("PID", width=pid_width, anchor="center")
            self.tree.column("Name", width=name_width)
            self.tree.column("CPU", width=cpu_width, anchor="center")
            self.tree.column("Memory", width=mem_width, anchor="center")
        self.root.bind("<Configure>", resize_columns)
        self.control_frame = tk.Frame(self.root, bg="#3A4A4B")
        self.control_frame.grid(row=2, column=0, pady=10, sticky="ew")
        self.button_frame = tk.Frame(self.control_frame, bg="#3A4A4B")
        self.button_frame.pack(anchor="center")
        self.start_frame = tk.Frame(self.button_frame, bg="#3A4A4B")
        self.start_frame.pack(side="left", padx=5)
        self.start_label = tk.Label(self.start_frame, text="START PROCESS", font=("Orbitron", 9, "bold"), bg="#3A4A4B", fg="white")
        self.start_label.pack()
        self.start_entry = tk.Entry(self.start_frame, width=15, bg="#4A5A5B", fg="white", insertbackground="white", font=("Orbitron", 8))
        self.start_entry.pack(pady=2)
        self.start_btn = ttk.Button(self.start_frame, text="Start", command=lambda: self.start_process(self.start_entry.get()))
        self.start_btn.pack()
        self.kill_frame = tk.Frame(self.button_frame, bg="#3A4A4B")
        self.kill_frame.pack(side="left", padx=5)
        self.kill_label = tk.Label(self.kill_frame, text="KILL PROCESS", font=("Orbitron", 9, "bold"), bg="#3A4A4B", fg="white")
        self.kill_label.pack()
        self.kill_entry = tk.Entry(self.kill_frame, width=15, bg="#4A5A5B", fg="white", insertbackground="white", font=("Orbitron", 8))
        self.kill_entry.pack(pady=2)
        self.kill_btn = ttk.Button(self.kill_frame, text="Kill", command=lambda: self.kill_process(self.kill_entry.get()))
        self.kill_btn.pack()
        self.prioritize_frame = tk.Frame(self.button_frame, bg="#3A4A4B")
        self.prioritize_frame.pack(side="left", padx=5)
        self.prioritize_label = tk.Label(self.prioritize_frame, text="PRIORITIZE TASK", font=("Orbitron", 9, "bold"), bg="#3A4A4B", fg="white")
        self.prioritize_label.pack()
        self.prioritize_entry = tk.Entry(self.prioritize_frame, width=15, bg="#4A5A5B", fg="white", insertbackground="white", font=("Orbitron", 8))
        self.prioritize_entry.pack(pady=2)
        self.prioritize_btn = ttk.Button(self.prioritize_frame, text="Prioritize", command=lambda: self.prioritize_process(self.prioritize_entry.get()))
        self.prioritize_btn.pack()
        self.search_frame = tk.Frame(self.button_frame, bg="#3A4A4B")
        self.search_frame.pack(side="left", padx=5)
        self.search_label = tk.Label(self.search_frame, text="SEARCH PROCESS", font=("Orbitron", 9, "bold"), bg="#3A4A4B", fg="white")
        self.search_label.pack()
        self.search_inner_frame = tk.Frame(self.search_frame, bg="#3A4A4B")
        self.search_inner_frame.pack()
        self.search_entry = tk.Entry(self.search_inner_frame, width=15, bg="#4A5A5B", fg="white", insertbackground="white", font=("Orbitron", 8))
        self.search_entry.pack(side="left", pady=2)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        mic_path = os.path.join(script_dir, "mic.png")
        try:
            mic_img_pil = make_image_round(mic_path, 20)
            self.mic_img = ImageTk.PhotoImage(mic_img_pil)
            self.mic_label = tk.Label(self.search_inner_frame, image=self.mic_img, bg="#3A4A4B")
            self.mic_label.pack(side="left", padx=5)
        except Exception as e:
            print(f"Error loading mic image: {e}")
            self.mic_label = tk.Label(self.search_inner_frame, text="[Mic]", bg="#3A4A4B", fg="white")
            self.mic_label.pack(side="left", padx=5)
        self.search_btn = ttk.Button(self.search_frame, text="Search", command=lambda: self.search_process(self.search_entry.get()))
        self.search_btn.pack()
        self.search_entry.bind("<KeyRelease>", self.on_search_entry_change)
        self.bottom_frame = tk.Frame(self.root, bg="#3A4A4B")
        self.bottom_frame.grid(row=3, column=0, pady=10, sticky="ew")
        try:
            self.fig, self.ax = plt.subplots(figsize=(3, 1.5), facecolor="#3A4A4B")
            self.ax.set_facecolor("#4A5A5B")
            self.ax.tick_params(colors="white", labelsize=6)
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.bottom_frame)
            self.canvas.get_tk_widget().pack()
        except Exception as e:
            print(f"Error initializing Matplotlib graph: {e}")
            self.fig = None
            self.ax = None
            self.canvas = None
        self.listening_label = tk.Label(self.bottom_frame, text="LISTENING...", font=("Orbitron", 10), bg="#3A4A4B", fg="#FF99FF")
        self.listening_label.pack()
        self.pulse_listening()
    def pulse_listening(self):
        current_color = self.listening_label.cget("fg")
        self.listening_label.config(fg="#FFCCFF" if current_color == "#FF99FF" else "#FF99FF")
        self.root.after(500, self.pulse_listening)
    def update_process_list(self):
        search_term = self.current_search_term.lower()
        for i in self.tree.get_children():
            self.tree.delete(i)
        processes = []
        for idx, proc in enumerate(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])):
            cpu = proc.info['cpu_percent']
            mem = proc.info['memory_percent']
            cpu_str = f"{cpu:.1f}" if cpu is not None else "N/A"
            mem_str = f"{mem:.1f}" if mem is not None else "N/A"
            processes.append({
                "pid": proc.info['pid'],
                "name": proc.info['name'],
                "cpu": cpu_str,
                "mem": mem_str,
                "idx": idx
            })
        processes.sort(key=lambda x: (x["name"].lower(), x["pid"]))
        if search_term:
            filtered_processes = [p for p in processes if search_term in p["name"].lower()]
        else:
            filtered_processes = processes
        matching_items = []
        for p in filtered_processes:
            item = self.tree.insert("", "end", values=(p["pid"], p["name"], p["cpu"], p["mem"]), tags=("even" if p["idx"] % 2 == 0 else "odd"))
            if search_term and search_term in p["name"].lower():
                matching_items.append(item)
        self.tree.tag_configure("even", background="#3A4A4B")
        self.tree.tag_configure("odd", background="#4A5A5B")
        if search_term and matching_items:
            self.tree.selection_set(matching_items)
            self.tree.see(matching_items[0])
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
        if not hasattr(self, 'ax') or self.ax is None:
            print("Matplotlib graph not available.")
            self.root.after(5000, self.update_graph)
            return
        total_cpu = psutil.cpu_percent()
        total_mem = psutil.virtual_memory().percent
        self.cpu_data.append(total_cpu)
        self.mem_data.append(total_mem)
        if len(self.cpu_data) > 2:
            self.cpu_data.pop(0)
            self.mem_data.pop(0)
        self.ax.clear()
        self.ax.bar([0], [self.cpu_data[-1]], color="#66DFFF", width=0.4)
        self.ax.bar([1], [self.mem_data[-1]], color="#FF99FF", width=0.4)
        self.ax.set_ylim(0, 100)
        self.ax.set_xticks([0, 1])
        self.ax.set_xticklabels(["CPU", "Memory"], fontsize=6, color="white")
        self.canvas.draw()
        self.root.after(5000, self.update_graph)
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
            self.listening_label.config(text="LISTENING...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                command = self.recognizer.recognize_google(audio).lower()
                self.process_command(command)
                self.listening_label.config(text="Command processed")
            except sr.UnknownValueError:
                self.listening_label.config(text="Unrecognized command")
            except sr.RequestError:
                self.listening_label.config(text="Speech service error")
            except sr.WaitTimeoutError:
                self.listening_label.config(text="No command detected")
            except Exception as e:
                self.listening_label.config(text=f"Error: {e}")
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
