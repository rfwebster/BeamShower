import tkinter as tk
from tkinter import ttk
import time

def start_progress():
    progress_var.set(0)  # Reset the progress bar to 0
    update_progress()

def update_progress():
    progress_value = progress_var.get()
    if progress_value < 100:
        progress_value += 5  # Increment the progress by 5% in this example
        progress_var.set(progress_value)
        progress_label.config(text=f"Progress: {progress_value}%")
        progressbar.after(500, update_progress)  # Update progress every 500 milliseconds
    else:
        progress_label.config(text="Progress: Done!")

# Create the main tkinter window
root = tk.Tk()
root.title("Progress Bar Example")

# Create a label for progress display
progress_label = tk.Label(root, text="Progress: 0%")
progress_label.place(x=10, y=10)

# Create a progress bar
progress_var = tk.DoubleVar()
progressbar = ttk.Progressbar(root, variable=progress_var, orient=tk.HORIZONTAL, length=200, mode='determinate')
progressbar.place(x=10, y=30)

# Create a button to start the progress
start_button = tk.Button(root, text="Start Progress", command=start_progress)
start_button.place(x=10, y=70)

# Start the main event loop
root.mainloop()
