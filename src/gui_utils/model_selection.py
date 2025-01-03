import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk

class ModelSelector:
    def __init__(self, parent_frame, variable, label_text=None):
        self.parent_frame = parent_frame
        self.variable = variable
        self.last_other_selection = None
        self.container_frame = None
        self._label = None

        # Model lists - single source of truth
        self.main_models = ["GPT-3.5", "GPT-4o mini", "GPT-4o"]
        self.other_models = ["Gemini 1.5 Flash", "Gemini 1.5 Pro", "DeepSeek-V3"]
        
        if label_text:
            self.create_label(label_text)
        self.create_selector()

    def create_label(self, text):
        self._label = tk.Label(self.parent_frame, text=text, font=("Segoe UI", 12))
        self._label.pack(pady=(20, 0))

    def create_selector(self):
        # Create container frame
        self.container_frame = tk.Frame(self.parent_frame)
        self.container_frame.pack()

        # First row - main models
        radio_frame1 = tk.Frame(self.container_frame)
        radio_frame1.pack()

        for option in self.main_models:
            ttk.Radiobutton(
                radio_frame1,
                text=f" {option} ",
                value=option,
                variable=self.variable,
                style="radios.Toolbutton"
            ).pack(side="left")

        # Second row - other models
        radio_frame2 = tk.Frame(self.container_frame)
        radio_frame2.pack(pady=(0, 0))

        # Create Other button
        self.other_button = ttk.Menubutton(
            radio_frame2, text=" Other ", style="TMenubutton"
        )
        self.other_button.pack(side="left")

        # Create dropdown menu
        other_menu = tk.Menu(
            self.other_button,
            tearoff=0,
            borderwidth=0,
            activeborderwidth=0,
            relief="flat",
            font=("Segoe UI", 10)
        )
        self.other_button.configure(menu=other_menu)

        # Add menu items
        for model in self.other_models:
            other_menu.add_radiobutton(
                label=model,
                value=model,
                variable=self.variable,
            )

        # Set up event handling
        self.setup_events()
        
    @property
    def frame(self):
        """Access the container frame"""
        return self.container_frame

    @property
    def label(self):
        """Access the label"""
        return self._label

    def setup_events(self):
        def update_other_button_state(*args):
            selected_model = self.variable.get()
            if selected_model in self.other_models:
                self.other_button.configure(text=f" {selected_model} ")
                self.other_button.state(["pressed"])
            else:
                self.other_button.configure(text=" Other ")
                self.other_button.state(["!pressed"])

        def on_other_click(event):
            selected_model = self.variable.get()
            if selected_model in self.other_models:
                self.last_other_selection = selected_model
                update_other_button_state()

        self.other_button.bind("<Button-1>", on_other_click)
        self.other_button.bind("<Leave>", update_other_button_state)
        self.variable.trace_add("write", update_other_button_state)