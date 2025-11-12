import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime
import json
import os


import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


DATA_FILE = "multi_user_bmi_data.json"
DEFAULT_USER_NAME = "Default User"

BMI_CATEGORIES = [
    (18.5, "Underweight 😟", "#ff8c00"),
    (25.0, "Normal Weight 😊", "#3cb371"),
    (30.0, "Overweight 😐", "#ffd700"),
    (float('inf'), "Obese 😔", "#dc143c")
]

INCH_TO_METER = 0.0254


def calculate_bmi(weight_kg, height_m):
    if height_m <= 0:
        return 0.0
    return round(weight_kg / (height_m ** 2), 2)

def classify_bmi(bmi):
    for limit, category, color in BMI_CATEGORIES:
        if bmi < limit:
            return category, color
    return "Unknown", "gray"

def convert_to_meters(feet, inches):
    total_inches = (feet * 12) + inches
    return total_inches * INCH_TO_METER

def load_data():
    if not os.path.exists(DATA_FILE):
        return {DEFAULT_USER_NAME: []}
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return data if data else {DEFAULT_USER_NAME: []}
    except (IOError, json.JSONDecodeError):
        messagebox.showerror("Data Error", "Could not load user data. Starting fresh.")
        return {DEFAULT_USER_NAME: []}

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError:
        messagebox.showerror("Error", "Could not save historical data.")

def plot_bmi_history(history_data, history_window, current_user):

    for widget in history_window.winfo_children():
        if isinstance(widget, tk.Frame) and widget.winfo_name() == 'plot_frame':
            widget.destroy()

    plot_frame = tk.Frame(history_window, name='plot_frame', bg='white')
    plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    if len(history_data) < 2:
        tk.Label(plot_frame, text="Need at least 2 entries to plot a trend.", fg='red', font=('Arial', 12), bg='white').pack(pady=20)
        return

    dates = [datetime.datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S") for entry in history_data]
    bmis = [entry['bmi'] for entry in history_data]

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(6, 4))

    ax.plot(dates, bmis, marker='o', linestyle='-', color='#007bff', linewidth=2, label=f'{current_user} BMI')

    mean_bmi = np.mean(bmis)
    ax.axhline(mean_bmi, color='gray', linestyle='--', linewidth=1.5, label=f'Avg BMI: {mean_bmi:.2f}')

    normal_color = next(c for l, cat, c in BMI_CATEGORIES if cat.startswith("Normal"))
    ax.axhspan(18.5, 25.0, color=normal_color, alpha=0.2, zorder=0, label='Normal Range')

    ax.set_title(f'BMI Trend Analysis for {current_user}', fontsize=14, color='#333333')
    ax.set_xlabel('Date Recorded', fontsize=10)
    ax.set_ylabel('BMI Value', fontsize=10)
    ax.grid(True, axis='y', linestyle=':', alpha=0.7)
    ax.legend(loc='best', fontsize=8)
    fig.autofmt_xdate(rotation=30)
    plt.tight_layout()
    fig.patch.set_facecolor('white')
    ax.patch.set_facecolor('white')

    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    canvas.draw()


class UltimateBMICalculatorApp:
    def __init__(self, master):
        self.master = master
        master.title("🚀 Ultimate Multi-User BMI Tracker (Imperial Input) 📈")
        master.geometry("750x550")
        master.configure(bg='#e6e6fa')

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#e6e6fa')
        style.configure('TButton', font=('Helvetica', 10, 'bold'), padding=8, foreground='white', background='#007bff')
        style.map('TButton', background=[('active', '#0056b3')])
        style.configure('TLabel', background='#e6e6fa', font=('Helvetica', 10), foreground='#333333')
        style.configure('TCombobox', font=('Helvetica', 12), padding=2)
        style.configure('ResultTLabel', background='white', borderwidth=2, relief='groove', padding=10)

        self.all_users_data = load_data()
        initial_user = list(self.all_users_data.keys())[0] if self.all_users_data else DEFAULT_USER_NAME
        self.current_user = tk.StringVar(value=initial_user)

        self.feet_var = tk.DoubleVar()
        self.inches_var = tk.DoubleVar()
        self.weight_kg_var = tk.DoubleVar()

        self.bmi_result_var = tk.StringVar(value="N/A")
        self.category_result_var = tk.StringVar(value="N/A")
        self.category_color_var = tk.StringVar(value="gray")

        self.feet_var.trace_add("write", self.realtime_update)
        self.inches_var.trace_add("write", self.realtime_update)
        self.weight_kg_var.trace_add("write", self.realtime_update)
        self.current_user.trace_add("write", self.load_user_profile)

        self.create_widgets()
        self.load_user_profile()

    def create_widgets(self):
        top_frame = ttk.Frame(self.master, padding="15 10 15 10", relief=tk.FLAT, style='TFrame')
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="👤 Current User:", font=('Helvetica', 14, 'bold'), foreground='#333333').pack(side=tk.LEFT, padx=5)

        user_options = list(self.all_users_data.keys())
        self.user_selector = ttk.Combobox(top_frame, textvariable=self.current_user, values=user_options, width=15, font=('Helvetica', 12))
        self.user_selector.pack(side=tk.LEFT, padx=10)

        ttk.Button(top_frame, text="➕ New User Profile", command=self.add_new_user).pack(side=tk.LEFT, padx=15)

        main_frame = ttk.Frame(self.master, padding="30 20 30 20", style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_columnconfigure((0, 1), weight=1)

        input_frame = ttk.LabelFrame(main_frame, text="🏋️ Enter Measurements", padding="15", style='TFrame', relief=tk.RIDGE)
        input_frame.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        ttk.Label(input_frame, text="Height:", font=('Helvetica', 12, 'bold')).grid(row=0, column=0, sticky='w', pady=15, padx=5)

        height_input_frame = ttk.Frame(input_frame, style='TFrame')
        height_input_frame.grid(row=0, column=1, pady=15, padx=5, sticky='w')

        self.feet_entry = ttk.Entry(height_input_frame, textvariable=self.feet_var, width=5, font=('Helvetica', 14), justify='center')
        self.feet_entry.pack(side=tk.LEFT)
        ttk.Label(height_input_frame, text="ft", font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT, padx=(2, 10))

        self.inches_entry = ttk.Entry(height_input_frame, textvariable=self.inches_var, width=5, font=('Helvetica', 14), justify='center')
        self.inches_entry.pack(side=tk.LEFT)
        ttk.Label(height_input_frame, text="in", font=('Helvetica', 12, 'bold')).pack(side=tk.LEFT, padx=2)

        ttk.Label(input_frame, text="Weight:", font=('Helvetica', 12, 'bold')).grid(row=1, column=0, sticky='w', pady=15, padx=5)
        self.weight_entry = ttk.Entry(input_frame, textvariable=self.weight_kg_var, width=15, font=('Helvetica', 14), justify='center')
        self.weight_entry.grid(row=1, column=1, pady=15, padx=5, sticky='w')
        ttk.Label(input_frame, text="kg", font=('Helvetica', 12)).grid(row=1, column=1, sticky='e', padx=5)

        result_frame = ttk.LabelFrame(main_frame, text="✨ Real-time BMI Status", padding="15", style='TFrame', relief=tk.RIDGE)
        result_frame.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")

        ttk.Label(result_frame, text="Calculated BMI:", font=('Helvetica', 14, 'bold')).pack(pady=10)

        self.bmi_display = ttk.Label(result_frame, textvariable=self.bmi_result_var, font=('Helvetica', 40, 'bold'), foreground='#007bff', style='Result.TLabel')
        self.bmi_display.pack(pady=10, fill=tk.X)

        ttk.Label(result_frame, text="Classification:", font=('Helvetica', 14, 'bold')).pack(pady=10)
        self.category_display = ttk.Label(result_frame, textvariable=self.category_result_var, font=('Helvetica', 18, 'bold'), style='Result.TLabel')
        self.category_display.pack(pady=10, fill=tk.X)

        self.category_color_var.trace_add("write", lambda *args: self.category_display.config(foreground=self.category_color_var.get()))

        action_frame = ttk.Frame(main_frame, padding="10", style='TFrame')
        action_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        ttk.Button(action_frame, text="💾 Save Current Reading", command=self.save_current_reading).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=15)
        ttk.Button(action_frame, text="📈 View Trend Analysis", command=self.show_history_window).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=15)

    def add_new_user(self):
        new_user_name = simpledialog.askstring("New User", "Enter new user name (e.g., Jane Doe):")
        if new_user_name and new_user_name not in self.all_users_data:
            self.all_users_data[new_user_name] = []
            save_data(self.all_users_data)

            user_options = list(self.all_users_data.keys())
            self.user_selector['values'] = user_options
            self.current_user.set(new_user_name)
            messagebox.showinfo("Success", f"User **{new_user_name}** created! Welcome.")
        elif new_user_name:
            messagebox.showwarning("Warning", f"User '{new_user_name}' already exists or input was invalid.")

    def load_user_profile(self, *args):
        user_history = self.all_users_data.get(self.current_user.get(), [])

        if user_history:
            last_entry = user_history[-1]

            height_m = last_entry.get('height_m', 0.0)

            total_inches = height_m / INCH_TO_METER

            feet = int(total_inches // 12)
            inches = round(total_inches % 12, 1)

            self.feet_var.set(feet)
            self.inches_var.set(inches)
            self.weight_kg_var.set(last_entry.get('weight_kg', 0.0))

            self.realtime_update()
        else:
            self.feet_var.set(0.0)
            self.inches_var.set(0.0)
            self.weight_kg_var.set(0.0)
            self.bmi_result_var.set("N/A")
            self.category_result_var.set("N/A")
            self.category_color_var.set("gray")


    def validate_and_get_inputs(self):
        try:
            w = self.weight_kg_var.get()
            f = self.feet_var.get()
            i = self.inches_var.get()

            if f < 0 or i < 0 or w <= 0:
                return None, None

            height_m = convert_to_meters(f, i)

            if height_m < 0.5 or w < 10:
                return None, None
            
            return height_m, w
        except tk.TclError:
            return None, None
        except ValueError:
            return None, None

    def realtime_update(self, *args):
        height_m, weight = self.validate_and_get_inputs()

        if height_m and weight:
            bmi_value = calculate_bmi(weight, height_m)
            category, color = classify_bmi(bmi_value)

            self.bmi_result_var.set(f"{bmi_value:.2f}")
            self.category_result_var.set(category)
            self.category_color_var.set(color)
        else:
            self.bmi_result_var.set("...")
            self.category_result_var.set("Invalid Input")
            self.category_color_var.set("#dc143c")

    def save_current_reading(self):
        height_m, weight = self.validate_and_get_inputs()

        if not height_m or not weight:
            messagebox.showerror("Error", "🚫 Cannot save: Please enter valid, positive height and weight.")
            return

        bmi_value = calculate_bmi(weight, height_m)
        category, _ = classify_bmi(bmi_value)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = {
            "timestamp": timestamp,
            "weight_kg": weight,
            "height_m": height_m,
            "bmi": bmi_value,
            "category": category
        }

        user = self.current_user.get()
        self.all_users_data[user].append(new_entry)
        save_data(self.all_users_data)

        messagebox.showinfo("Success! 🎉", f"BMI reading successfully saved for **{user}**.\n\nBMI: **{bmi_value:.2f}** ({category})")

    def show_history_window(self):
        history_window = tk.Toplevel(self.master)
        history_window.title(f"📈 BMI Trend Analysis: {self.current_user.get()}")
        history_window.geometry("750x650")
        history_window.configure(bg='white')

        user = self.current_user.get()
        user_history = self.all_users_data.get(user, [])

        plot_bmi_history(user_history, history_window, user)

        log_frame = ttk.Frame(history_window, padding="10", style='TFrame', relief=tk.FLAT)
        log_frame.pack(padx=10, pady=10, fill='both', expand=True)

        ttk.Label(log_frame, text="📊 Detailed History Log:", font=('Helvetica', 12, 'bold'), foreground='#333333').pack(pady=5, anchor='w')

        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(text_frame, wrap='word', height=5, width=60, yscrollcommand=scrollbar.set, font=('Consolas', 10), bg='#f8f8ff')
        text_widget.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.config(command=text_widget.yview)

        if not user_history:
            text_widget.insert(tk.END, "No historical data recorded yet for this user. Save a reading first!")
        else:
            text_widget.insert(tk.END, "Date/Time             | Weight | Height | BMI   | Category\n")
            text_widget.insert(tk.END, "="*55 + "\n")

            for entry in reversed(user_history):
                display_line = (
                    f"{entry['timestamp']:<20}| {entry['weight_kg']:.1f}kg | {entry['height_m']:.2f}m | {entry['bmi']:<5.2f} | {entry['category']}\n"
                )
                text_widget.insert(tk.END, display_line)

        text_widget.config(state=tk.DISABLED)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = UltimateBMICalculatorApp(root)
        messagebox.showinfo("Welcome!", "You can now enter height in **Feet** and **Inches**! The app will automatically convert it to meters for the calculation. Have fun tracking! 👍")
        root.mainloop()
    except Exception as e:
        messagebox.showerror("CRITICAL ERROR", f"The application encountered a fatal error:\n\nError: {e}\n\nCheck if **matplotlib** and **numpy** are installed correctly (`pip install matplotlib numpy`).")
