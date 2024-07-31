import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np

class WaterAllocationApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Water Allocation Optimizer")
        self.master.geometry("1000x700")

        self.benefit_table = {}
        self.water_allocations = []
        self.num_users = None
        self.max_water = None

        self.create_widgets()

    def create_widgets(self):
        # Input Frame
        input_frame = ttk.Frame(self.master, padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Button(input_frame, text="Show Excel Format", command=self.show_excel_format).pack(pady=5)
        ttk.Button(input_frame, text="Upload Excel File", command=self.upload_excel).pack(pady=5)

        # Table Frame
        self.table_frame = ttk.Frame(self.master, padding="10")
        self.table_frame.pack(fill=tk.BOTH, expand=True)

        # Result Frame
        self.result_frame = ttk.Frame(self.master, padding="10")
        self.result_frame.pack(fill=tk.BOTH, expand=True)

    def show_excel_format(self):
        format_window = tk.Toplevel(self.master)
        format_window.title("Excel File Format")
        format_window.geometry("400x200")

        ttk.Label(format_window, text="Excel File Format:").pack(pady=10)
        ttk.Label(format_window, text="Column A: Water Allocation").pack()
        ttk.Label(format_window, text="Columns B onwards: Benefits for each user").pack()
        ttk.Label(format_window, text="Example:").pack(pady=10)
        ttk.Label(format_window, text="A    B    C    D").pack()
        ttk.Label(format_window, text="10   5    8    6").pack()
        ttk.Label(format_window, text="20   12   15   10").pack()
        ttk.Label(format_window, text="30   18   20   16").pack()

    def upload_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if not file_path:
            return

        try:
            df = pd.read_excel(file_path, header=None)
            if self.validate_excel_data(df):
                self.load_data_from_df(df)
                self.update_table()
            else:
                messagebox.showerror("Error", "Invalid Excel format. Please check the file and try again.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read Excel file: {str(e)}")

    def validate_excel_data(self, df):
        if df.shape[1] < 2:  # At least two columns (water allocation and one user)
            return False
        if not df[0].dtype.kind in 'iu':  # Check if first column (water allocation) is integer
            return False
        for col in df.columns[1:]:
            if not df[col].dtype.kind in 'iu':  # Check if benefit columns are integers
                return False
        return True

    def load_data_from_df(self, df):
        self.benefit_table = {}
        self.water_allocations = []
        self.num_users = df.shape[1] - 1

        for _, row in df.iterrows():
            water = int(row[0])
            benefits = [int(b) for b in row[1:]]
            self.benefit_table[water] = benefits
            self.water_allocations.append(water)

    def update_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        headers = ["Water"] + [f"User {i+1}" for i in range(self.num_users)]
        for col, header in enumerate(headers):
            ttk.Label(self.table_frame, text=header, font=('Arial', 10, 'bold')).grid(row=0, column=col, padx=5, pady=5)

        self.entry_widgets = {}
        for row, (water, benefits) in enumerate(self.benefit_table.items(), start=1):
            water_entry = ttk.Entry(self.table_frame, width=10)
            water_entry.insert(0, str(water))
            water_entry.grid(row=row, column=0, padx=5, pady=2)
            water_entry.bind('<FocusOut>', lambda e, r=row, c=0: self.update_cell(r, c))
            self.entry_widgets[(row, 0)] = water_entry

            for col, benefit in enumerate(benefits, start=1):
                benefit_entry = ttk.Entry(self.table_frame, width=10)
                benefit_entry.insert(0, str(benefit))
                benefit_entry.grid(row=row, column=col, padx=5, pady=2)
                benefit_entry.bind('<FocusOut>', lambda e, r=row, c=col: self.update_cell(r, c))
                self.entry_widgets[(row, col)] = benefit_entry

        ttk.Button(self.table_frame, text="Optimize", command=self.run_optimization).grid(row=len(self.benefit_table)+1, column=0, columnspan=self.num_users+1, pady=10)

    def update_cell(self, row, col):
        try:
            value = int(self.entry_widgets[(row, col)].get())
            if col == 0:
                old_water = self.water_allocations[row-1]
                self.water_allocations[row-1] = value
                benefits = self.benefit_table.pop(old_water)
                self.benefit_table[value] = benefits
            else:
                water = self.water_allocations[row-1]
                self.benefit_table[water][col-1] = value
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integer values.")
            self.entry_widgets[(row, col)].focus_set()

    def run_optimization(self):
        self.max_water = max(self.water_allocations)
        results = self.optimize_allocation()
        self.display_results(results)

    def optimize_allocation(self):
        memo = {}
        water_allocations = sorted(self.water_allocations)
        water_interval = water_allocations[1] - water_allocations[0] if len(water_allocations) > 1 else 1

        def dp(water, user):
            if water < 0 or user == self.num_users:
                return 0, []
            
            if (water, user) in memo:
                return memo[(water, user)]
            
            max_benefit = 0
            best_allocation = []
            
            for x in [w for w in water_allocations if w <= water]:
                benefit = self.benefit_table[x][user]
                sub_benefit, sub_allocation = dp(water - x, user + 1)
                total_benefit = benefit + sub_benefit
                
                if total_benefit > max_benefit:
                    max_benefit = total_benefit
                    best_allocation = [x] + sub_allocation
            
            memo[(water, user)] = (max_benefit, best_allocation)
            return max_benefit, best_allocation

        results = []
        for water in range(0, self.max_water + water_interval, water_interval):
            benefit, allocation = dp(water, 0)
            results.append((water, benefit, allocation))
        
        return results

    def display_results(self, results):
        for widget in self.result_frame.winfo_children():
            widget.destroy()

        # Create a table for results
        columns = ["Water", "Max Benefit"] + [f"User {i+1}" for i in range(self.num_users)]
        tree = ttk.Treeview(self.result_frame, columns=columns, show="headings")
        tree.heading("Water", text="Water")
        tree.heading("Max Benefit", text="Max Benefit")
        for i in range(self.num_users):
            tree.heading(f"User {i+1}", text=f"User {i+1}")
        tree.pack(fill=tk.BOTH, expand=True)

        for water, benefit, allocation in results:
            values = [water, benefit] + allocation
            tree.insert("", "end", values=values)

        # Create a plot
        fig, ax = plt.subplots(figsize=(10, 6))
        water_values = [r[0] for r in results]
        benefit_values = [r[1] for r in results]
        
        ax.plot(water_values, benefit_values, marker='o')
        
        for x, y in zip(water_values, benefit_values):
            ax.annotate(f'({x}, {y})', (x, y), textcoords="offset points", xytext=(0,10), ha='center')

        ax.set_xlabel("Water")
        ax.set_ylabel("Max Benefit")
        ax.set_title("Max Benefit vs Water Allocation")

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.result_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def main():
    root = tk.Tk()
    app = WaterAllocationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()