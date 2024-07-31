import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class ReservoirOperationApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Reservoir Operation Optimizer")
        self.master.geometry("1000x700")

        self.benefit_table = {}
        self.release_amounts = []
        self.num_months = None
        self.max_capacity = None
        self.monthly_inflows = []

        self.create_widgets()

    def create_widgets(self):
        # Main Frame
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Input Frame
        input_frame = ttk.Frame(main_frame, padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(input_frame, text="Max Reservoir Capacity:").pack()
        self.capacity_entry = ttk.Entry(input_frame, width=10)
        self.capacity_entry.pack()

        ttk.Label(input_frame, text="Enter data (see format below):").pack()
        self.data_text = scrolledtext.ScrolledText(input_frame, width=50, height=10)
        self.data_text.pack(fill=tk.BOTH, expand=True)

        ttk.Button(input_frame, text="Load Data", command=self.load_data).pack()

        # Result Frame
        self.result_frame = ttk.Frame(main_frame, padding="10")
        self.result_frame.pack(fill=tk.BOTH, expand=True)

        # Show data format
        self.show_data_format()

    def show_data_format(self):
        format_text = """Data Format:
First line: Monthly inflows separated by spaces
Following lines: Release amount followed by benefits for each month, separated by spaces

Example:
20 25 30 35
0 0 0 0 0
10 5 8 6 7
20 12 15 10 14
30 18 20 16 22
"""
        ttk.Label(self.master, text=format_text, justify=tk.LEFT).pack()

    def load_data(self):
        try:
            data = self.data_text.get("1.0", tk.END).strip().split('\n')
            self.monthly_inflows = list(map(float, data[0].split()))
            self.num_months = len(self.monthly_inflows)

            self.benefit_table = {}
            self.release_amounts = []

            for line in data[1:]:
                values = list(map(float, line.split()))
                release = values[0]
                benefits = values[1:]
                if len(benefits) != self.num_months:
                    raise ValueError(f"Number of benefits ({len(benefits)}) doesn't match number of months ({self.num_months})")
                self.benefit_table[release] = benefits
                self.release_amounts.append(release)

            self.max_capacity = float(self.capacity_entry.get())

            messagebox.showinfo("Success", "Data loaded successfully")
            self.run_optimization()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")

    def run_optimization(self):
        results = self.optimize_operation()
        self.display_results(results)

    def optimize_operation(self):
        memo = {}
        
        def dp(stage, month):
            if month == self.num_months:
                return 0, []
            
            if (stage, month) in memo:
                return memo[(stage, month)]
            
            max_benefit = float('-inf')
            best_release = None
            
            for release in self.release_amounts:
                if 0 <= release <= self.monthly_inflows[month] + stage:
                    new_stage = min(stage + self.monthly_inflows[month] - release, self.max_capacity)
                    benefit = self.benefit_table[release][month]
                    future_benefit, future_releases = dp(new_stage, month + 1)
                    total_benefit = benefit + future_benefit
                    
                    if total_benefit > max_benefit:
                        max_benefit = total_benefit
                        best_release = release
            
            memo[(stage, month)] = (max_benefit, [best_release] + (future_releases if best_release is not None else []))
            return memo[(stage, month)]

        max_benefit, optimal_releases = dp(0, 0)
        return max_benefit, optimal_releases

    def display_results(self, results):
        for widget in self.result_frame.winfo_children():
            widget.destroy()

        max_benefit, optimal_releases = results

        # Create a table for results
        columns = ["Month", "Inflow", "Release", "Stage", "Benefit"]
        tree = ttk.Treeview(self.result_frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
        tree.pack(fill=tk.BOTH, expand=True)

        stage = 0
        for month, (inflow, release) in enumerate(zip(self.monthly_inflows, optimal_releases), start=1):
            stage = min(stage + inflow - release, self.max_capacity)
            benefit = self.benefit_table[release][month-1]
            tree.insert("", "end", values=(month, inflow, release, stage, benefit))

        ttk.Label(self.result_frame, text=f"Total Benefit: {max_benefit:.2f}", font=('Arial', 12, 'bold')).pack(pady=10)

        # Create a plot
        fig, ax = plt.subplots(figsize=(10, 6))
        months = range(1, self.num_months + 1)
        
        ax.plot(months, self.monthly_inflows, marker='o', label='Inflow')
        ax.plot(months, optimal_releases, marker='s', label='Release')
        
        ax.set_xlabel("Month")
        ax.set_ylabel("Water Amount")
        ax.set_title("Inflow and Optimal Release by Month")
        ax.legend()

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.result_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def main():
    root = tk.Tk()
    app = ReservoirOperationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()