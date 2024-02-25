import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
import threading
import time
import queue
import winsound
import sys
import os

GBA_FPS = 59.7275
GBA_FRAMERATE = 1000 / GBA_FPS

class CountdownTimer:
    def __init__(self, root, update_time_cb, finish_cb, queue):
        self.root = root
        self.update_time_cb = update_time_cb
        self.finish_cb = finish_cb
        self.queue = queue
        self.thread = None
        self.stop_event = threading.Event()

    def start(self, duration_ms):
        self.stop()  # Ensure any existing timer is stopped before starting a new one
        self.duration_ms = duration_ms
        self.start_time = time.time()
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        while not self.stop_event.is_set():
            elapsed_time = (time.time() - self.start_time) * 1000
            if elapsed_time < self.duration_ms:
                time_left = int(self.duration_ms - elapsed_time)
                self.queue.put(lambda: self.update_time_cb(time_left) if not self.stop_event.is_set() else None)
            else:
                self.queue.put(lambda: self.update_time_cb(0))
                winsound.Beep(1300, 200)  # Beep at 440Hz for 100ms
                break
            time.sleep(0.01)
    
        if not self.stop_event.is_set():
            self.queue.put(self.finish_cb)

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join()

class App:
    def __init__(self, root):
        self.root = root
        self.queue = queue.Queue()
        self.setup_ui()
        self.timer = None
        self.timer_running = False
        self.process_queue()
        self.timer_running = False
        self.active_timers = 0
        root.bind('<space>', self.toggle_start_stop)

    def setup_ui(self):
        # Determine if the script is run as a standalone executable or as a script
        if getattr(sys, 'frozen', False):
            # If the script is run as a standalone executable
            application_path = sys._MEIPASS
        else:
            # If the script is run from a Python interpreter
            application_path = os.path.dirname(os.path.abspath(__file__))

        logo_path = os.path.join(application_path, 'logo.png')
        logo_image = PhotoImage(file=logo_path)
        logo_image = logo_image.subsample(5, 5)
        logo_label = ttk.Label(self.root, image=logo_image)
        logo_label.image = logo_image
        logo_label.grid(column=3, row=0, rowspan=5, sticky="ne", padx=10, pady=10)
        
        vcmd = (self.root.register(self.validate_input), '%P')
        timer_font = ('Helvetica', 80, 'bold')

        self.lag_var = tk.IntVar(value=0)
        self.target_frame_var = tk.IntVar(value=0)
        self.frame_hit_var = tk.IntVar(value=0)
        self.time_var = tk.StringVar(value='0.0')

        ttk.Label(self.root, text="Lag (ms):").grid(column=0, row=0)
        self.lag_entry = ttk.Entry(self.root, textvariable=self.lag_var, validate='key', validatecommand=vcmd)
        self.lag_entry.grid(column=1, row=0)

        ttk.Label(self.root, text="Target frame:").grid(column=0, row=1)
        self.target_frame_entry = ttk.Entry(self.root, textvariable=self.target_frame_var, validate='key', validatecommand=vcmd)
        self.target_frame_entry.grid(column=1, row=1)

        ttk.Label(self.root, text="Frame hit:").grid(column=0, row=2)
        self.frame_hit_entry = ttk.Entry(self.root, textvariable=self.frame_hit_var, validate='key', validatecommand=vcmd)
        self.frame_hit_entry.grid(column=1, row=2)

        ttk.Label(self.root, text="Time (s):").grid(column=0, row=3)
        ttk.Label(self.root, textvariable=self.time_var, font=timer_font).grid(column=1, row=3)

        ttk.Button(self.root, text="Update", command=self.update_lag).grid(column=0, row=4)
        ttk.Button(self.root, text="Start", command=self.start_timer).grid(column=1, row=4)
        ttk.Button(self.root, text="Stop", command=self.stop_timer).grid(column=2, row=4)

        # Add a label to display the start/stop key information
        ttk.Label(self.root, text="Start/Stop key: Spacebar").grid(column=0, row=5, columnspan=3, pady=(10, 0))

        self.target_frame_var.trace_add("write", self.handle_empty_input)
        self.lag_var.trace_add("write", self.handle_empty_input)
        self.frame_hit_var.trace_add("write", self.handle_empty_input)
        
    def validate_input(self, new_value):
        # This method should return True if the new_value is a valid input and within the 7 digits limit, False otherwise
        # The condition checks if the input is either a digit or empty (for deletion) and its length is less than or equal to 7
        return (new_value.isdigit() or new_value == "") and len(new_value) <= 7

        
    def toggle_start_stop(self, event=None):  # event parameter is needed for bind method
        if self.timer_running:
            self.stop_timer()
        else:
            self.start_timer()
            
            
    def handle_empty_input(self, *args):
        self.root.after(10, self.delayed_check_empty_input)
    
    def delayed_check_empty_input(self):
        for entry, var in [(self.lag_entry, self.lag_var), 
                        (self.target_frame_entry, self.target_frame_var), 
                        (self.frame_hit_entry, self.frame_hit_var)]:
            if not entry.get():
                var.set(0)
    
        if not self.timer_running:
            self.refresh_timer_display()

    def refresh_timer_display(self):
        self.update_time_display(self.target_frame_var.get() * GBA_FRAMERATE + self.lag_var.get())

    def update_time_display(self, time_ms):
        time_s = time_ms / 1000
        self.time_var.set(f'{time_s:.1f}')  # Changed from :.2f to :.1f

    def update_lag(self):
        if self.frame_hit_var.get() != 0:
            new_lag = self.lag_var.get() + (self.target_frame_var.get() - self.frame_hit_var.get()) * GBA_FRAMERATE
            self.lag_var.set(int(new_lag))
        # Set focus back to the root window to prevent spacebar from triggering the button
        self.root.focus_set()

    def start_timer(self):
        self.stop_timer(clear_queue=False)  # Stop any running timers without clearing the queue
        self.timer_running = True
    
        self.active_timers += 1
        
        # Check if entry fields are empty and treat them as 0 if they are
        target_frame_value = self.target_frame_var.get() if self.target_frame_entry.get() != "" else 0
        lag_value = self.lag_var.get() if self.lag_entry.get() != "" else 0
    
        time_ms = max(0, target_frame_value * GBA_FRAMERATE + lag_value)
        self.update_time_display(time_ms)
        self.timer = CountdownTimer(self.root, lambda t: self.update_time_display(t) if self.timer_running else None, self.finish_main_timer, self.queue)
        self.timer.start(time_ms)
    
    def finish_main_timer(self):
        # Decrement the active_timers counter each time a timer finishes
        self.active_timers -= 1

        # Only reset the timer display if there are no more active timers
        if self.active_timers == 0:
            self.timer_running = False
            # Delay the reset to allow for quick restarts without resetting the display
            self.root.after(2000, self.reset_timer_display_if_inactive)
 
    def reset_timer_display_if_inactive(self):
        # Only reset the display if there are no more active timers
        if self.active_timers == 0:
            self.reset_timer_display()

    def stop_timer(self, clear_queue=True):
        if self.timer:
            self.timer.stop()
            self.timer = None
    
        self.timer_running = False
        self.active_timers = max(0, self.active_timers - 1)
        
        if clear_queue:
            self.root.after(50, self.reset_timer_display)
        
        # Set focus back to the root window to ensure spacebar hotkey works
        self.root.focus_set()


    def clear_queue(self):
        try:
            while True:
                self.queue.get_nowait()
        except queue.Empty:
            pass

    def reset_timer_display(self):
        self.clear_queue()
        main_timer_start_time = self.target_frame_var.get() * GBA_FRAMERATE + self.lag_var.get()
        self.update_time_display(main_timer_start_time)

    def process_queue(self):
        try:
            while True:
                update_func = self.queue.get_nowait()
                update_func()
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

def main():
    root = tk.Tk()
    root.title("G3 Sniper")

    # Determine if the script is run as a standalone executable or as a script
    if getattr(sys, 'frozen', False):
        # If the script is run as a standalone executable
        application_path = sys._MEIPASS
    else:
        # If the script is run from a Python interpreter
        application_path = os.path.dirname(os.path.abspath(__file__))

    logo_path = os.path.join(application_path, 'icon.png')
    logo_image = tk.PhotoImage(file=logo_path)
    root.iconphoto(True, logo_image)

    root.resizable(False, False)  # This will lock the window size

    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
