import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk

class CollapsingHeader(ttk.Frame):
    def __init__(self, master, text, resource_path_func=None):
        super().__init__(master)
        self.is_open = False

        # Create a container frame with expand
        self.container = ttk.Frame(self)
        self.container.pack(expand=True)

        # Load icons
        self.right_icon = ttk.PhotoImage(file=resource_path_func("themes/right.png"))
        self.left_icon = ttk.PhotoImage(file=resource_path_func("themes/left.png"))

        # Create a temporary button to get width
        temp_button = ttk.Button(
            self,
            image=self.right_icon,
            style="Transparent.TButton",
        )
        temp_button.pack()
        self.update_idletasks()
        button_width = temp_button.winfo_reqwidth()
        temp_button.destroy()

        # Create a spacer frame on the left first
        self.left_spacer = ttk.Frame(self.container, width=button_width)
        self.left_spacer.pack(side=tk.LEFT)
        self.left_spacer.pack_propagate(False)

        # Title label centered
        self.title = ttk.Label(
            self.container,
            text=text,
        )
        self.title.pack(side=tk.LEFT)

        # Toggle button
        self.toggle_button = ttk.Button(
            self.container,
            image=self.right_icon,
            command=self.toggle,
            style="Transparent.TButton",
            takefocus=False,
        )
        self.toggle_button.pack(side=tk.LEFT)
        
        self.update_button_text()

    def toggle(self):
        self.is_open = not self.is_open
        self.update_button_text()
        self.event_generate("<<AdvancedOptionsToggled>>")

    def update_button_text(self):
        self.toggle_button.configure(image=self.left_icon if self.is_open else self.right_icon)