import os
import sys
import tkinter as tk
from tkinter import filedialog, scrolledtext
import tkinter.font as tkFont
import ctypes

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.utility import enable_high_dpi_awareness
from ttkbootstrap.tooltip import ToolTip


import darkdetect

from src import connector_functions, bw_upload_only, metrics, input_config
from src.gui_utils.collapsed import CollapsingHeader
from src.gui_utils.scrolled import ScrolledText
from src.gui_utils import instructions


class SentimentAnalysisApp:
    def __init__(self, master):
        self.master = master
        self.master.withdraw()
        self.master.minsize(450, 200)
        self.master.title("Sentiment Analysis Tool")
        self.master.resizable(False, False)

        # initialize styles
        self.init_styles()

        # Initialize variables
        self.init_variables()

        # Create and setup GUI components
        self.create_gui()

        self.config_manager = input_config.ConfigManager()

        icon_path = self.resource_path("themes/pie_icon.ico")
        self.master.iconbitmap(icon_path)
        
        # Center window before showing
        self.center_window()
        self.master.after_idle(self.master.deiconify)

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS  # type: ignore
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def init_styles(self):
        themes_path = self.resource_path("themes/themes.json")
        try:
            self.style = ttk.Style()
            self.style.load_user_themes(themes_path)
        except Exception as e:
            print(f"Error loading themes: {e}")
            self.style.theme_use("darkly")

        self.update_theme()
        self.default_font = tkFont.nametofont("TkDefaultFont")
        self.default_font.configure(family="Segoe UI")

    def update_theme(self, *args):
        selected_theme = (
            self.theme_var.get().strip() if hasattr(self, "theme_var") else "System"
        )

        if selected_theme == "System":
            theme = "custom-dark" if darkdetect.isDark() else "custom-light"
        elif selected_theme == "Dark":
            theme = "custom-dark"
        else:  # Light
            theme = "custom-light"

        try:
            self.style.theme_use(theme)
            self.set_titlebar_color(theme)

        except Exception as e:
            self.style.theme_use("darkly")
            print(f"Error setting theme: {e}")

        # Update styles to match theme
        self.style.configure("TNotebook", tabposition="n")
        self.style.configure("Toolbutton", font=("Segoe UI", 12))
        self.style.configure("run.TButton", font=("Segoe UI", 13))
        self.style.configure("tooltip.TLabel", font=("Segoe UI", 10))
        self.style.configure(
            "radios.Toolbutton",
            font=("Segoe UI", 11),
            padding=7,
            background=self.style.colors.selectbg,
            borderwidth=0,
        )
        self.style.configure(
            "Transparent.TButton",
            background=self.style.colors.bg,
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
        )
        self.style.map(
            "Transparent.TButton", background=[("active", self.style.colors.bg)]
        )

    def set_titlebar_color(self, theme):
        if sys.platform.startswith("win"):
            try:
                # Store current window state and focused widget
                current_state = self.master.state()
                focused_widget = self.master.focus_get()

                # Hide window temporarily
                self.master.withdraw()
                self.master.update()
                is_dark = theme == "custom-dark"
                hwnd = ctypes.windll.user32.GetParent(self.master.winfo_id())
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                value = 1 if is_dark else 0

                # Try setting the dark mode attribute
                result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_USE_IMMERSIVE_DARK_MODE,
                    ctypes.byref(ctypes.c_int(value)),
                    ctypes.sizeof(ctypes.c_int(value)),
                )

                # If the first attempt failed, try with the pre-20H1 attribute
                if result != 0:
                    DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd,
                        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                        ctypes.byref(ctypes.c_int(value)),
                        ctypes.sizeof(ctypes.c_int(value)),
                    )

                # Restore window state
                if current_state == "normal":
                    self.master.deiconify()
                elif current_state == "zoomed":
                    self.master.state("zoomed")
                else:
                    self.master.state(current_state)

                # Restore focus
                if focused_widget:
                    self.master.after(1, focused_widget.focus)

            except Exception as e:
                print(f"Failed to set titlebar color: {e}")
                # Ensure window is shown even if there's an error
                self.master.deiconify()

    def init_variables(self):
        self.input_var = tk.StringVar()
        self.input_var.trace_add("write", self.check_file_exists)
        self.output_var = tk.StringVar()
        self.output_var.trace_add("write", self.check_file_exists)
        self.progress_var = tk.DoubleVar()
        self.customization_var = tk.StringVar(value=" Default ")
        self.gpt_model_var = tk.StringVar(value=" GPT-4o mini ")
        self.bw_checkbox_var = tk.IntVar()
        self.separate_company_tags_checkbox_var = tk.IntVar()

        self.logprob_checkbox_var = tk.IntVar()
        self.temperature_var = tk.DoubleVar(value=0.3)
        self.max_tokens_var = tk.DoubleVar(value=1)
        self.dual_model_var = tk.BooleanVar(value=False)
        self.second_model_var = tk.StringVar(value=" GPT-3.5 ")
        self.split_scale_var = tk.DoubleVar(value=50)
        self.theme_var = tk.StringVar(value=" System ")

    def create_gui(self):
        # Main frames
        instructions_frame = ttk.Frame(self.master)
        instructions_frame.pack(
            side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.BOTH
        )
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(side="left", padx=10, pady=10, expand=True, fill="both")
        self.advanced_frame = ttk.Frame(self.master)

        # Create GUI components
        self.create_input_section()
        self.create_notebook()
        self.create_sentiment_tab()
        self.create_bw_tab_run_button()
        self.create_progress_frame()
        instructions.create_instructions(instructions_frame)
        self.create_advanced_options()

    def create_input_section(self):
        self.input_section = ttk.Frame(self.main_frame)
        self.input_section.pack()
        input_label = tk.Label(
            self.input_section, text="Input File:", font=("Segoe UI", 12)
        )
        input_label.pack()

        input_frame = ttk.Frame(self.input_section)
        input_frame.pack()

        self.input_entry = tk.Entry(
            input_frame, textvariable=self.input_var, width=55, font=("Segoe UI", 11)
        )
        self.input_entry.pack(side=tk.RIGHT, padx=(0, 10))

        input_button = tk.Button(
            input_frame,
            text="Browse",
            font=("Segoe UI", 11),
            command=self.browse_input_file,
        )
        input_button.pack(side=tk.RIGHT, padx=(10, 0))

    def create_notebook(self):
        self.notebook = ttk.Notebook(
            self.main_frame, style="TNotebook", takefocus=False, padding=[0, 10, 0, 10]
        )
        self.notebook.pack(expand=True, fill=tk.BOTH)

        self.sentiment_tab_frame = tk.Frame(self.notebook)
        self.notebook.add(
            self.sentiment_tab_frame, text="Sentiment Analysis", padding=[20, 5, 20, 5]
        )

        self.bw_tab_frame = tk.Frame(self.notebook)
        self.notebook.add(
            self.bw_tab_frame, text="BW Upload Only", padding=[20, 5, 20, 5]
        )

    def create_sentiment_tab(self):
        self.create_output_section()
        self.create_main_checkboxes()
        self.create_customization_section()
        self.create_model_selection()
        self.create_run_button()

    def create_progress_frame(self):
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.BOTH)
        self.create_progress_bar()
        self.create_log_area()

    def create_output_section(self):
        output_label = tk.Label(
            self.sentiment_tab_frame, text="Output File:", font=("Segoe UI", 12)
        )
        output_label.pack(pady=(3, 0))

        output_frame = tk.Frame(self.sentiment_tab_frame)
        output_frame.pack()

        self.output_entry = tk.Entry(
            output_frame, textvariable=self.output_var, width=55, font=("Segoe UI", 11)
        )
        self.output_entry.pack(side=tk.RIGHT)

        output_button = tk.Button(
            output_frame,
            text="Browse",
            font=("Segoe UI", 11),
            command=self.browse_output_file,
        )
        output_button.pack(side=tk.RIGHT)

        # Add tooltip to the output button
        ToolTip(
            output_button,
            text="Tip: For very large files, use .csv as the output type for better performance.",
            wraplength=250,
            delay=100,
        )

        self.warning_label = tk.Label(
            self.sentiment_tab_frame,
            text="",
            font=("Segoe UI", 10, "italic"),
            fg="#b53d38",
        )
        self.warning_label.pack()

    def create_main_checkboxes(self):
        bw_checkbox = ttk.Checkbutton(
            self.sentiment_tab_frame,
            text=" Upload sentiment values to Brandwatch",
            variable=self.bw_checkbox_var,
            style="Roundtoggle.Toolbutton",
        )
        bw_checkbox.pack(pady=(0, 0))
        self.create_advanced_header()

    def create_advanced_header(self):
        self.advanced_header = CollapsingHeader(
            self.sentiment_tab_frame,
            text="Advanced Options",
            resource_path_func=self.resource_path,
        )
        self.advanced_header.pack(pady=(15, 0), fill="x")
        self.advanced_header.bind(
            "<<AdvancedOptionsToggled>>", self.toggle_advanced_options
        )

    def create_customization_section(self):
        customization_label = tk.Label(
            self.sentiment_tab_frame,
            text="Prompt Customization Option:",
            font=("Segoe UI", 12),
        )
        customization_label.pack(pady=(15, 0))
        prompt_radio_frame = tk.Frame(self.sentiment_tab_frame)
        prompt_radio_frame.pack()
        prompt_options = [" Default ", " Company ", " Multi-Company ", " Custom "]
        for option in prompt_options:
            prompt_radio_button = ttk.Radiobutton(
                prompt_radio_frame,
                text=option,
                value=option,
                variable=self.customization_var,
                style="radios.Toolbutton",
                command=self.on_customization_selected,
            )
            prompt_radio_button.pack(side="left")

        self.company_label = tk.Label(
            self.sentiment_tab_frame, text="Company name:", font=("Segoe UI", 12)
        )
        self.company_entry = tk.Entry(
            self.sentiment_tab_frame, width=18, font=("Segoe UI", 11)
        )

        self.create_multi_company_section()
        self.create_custom_prompt_section()

    def create_multi_company_section(self):
        self.multi_company_frame = tk.Frame(self.sentiment_tab_frame)

        company_column_label = tk.Label(
            self.multi_company_frame,
            text="Company column (BW parent category):",
            font=("Segoe UI", 12),
        )
        self.company_column_entry = tk.Entry(
            self.multi_company_frame, width=25, font=("Segoe UI", 11)
        )

        multi_company_label = tk.Label(
            self.multi_company_frame,
            text="List BW companies seperated by commas (in order of priority):",
            font=("Segoe UI", 12),
        )
        self.multi_company_entry = tk.Text(
            self.multi_company_frame,
            width=55,
            height=2,
            font=("Segoe UI", 11),
            wrap=tk.WORD,
        )

        separate_company_tags_checkbox_frame = tk.Frame(self.multi_company_frame)
        separate_company_tags_checkbox = ttk.Checkbutton(
            separate_company_tags_checkbox_frame,
            variable=self.separate_company_tags_checkbox_var,
            style="Roundtoggle.Toolbutton",
        )
        separate_company_tags_checkbox_label = tk.Label(
            separate_company_tags_checkbox_frame,
            text=" Separately code sentiment toward each company\n  mentioned in a post (adds BW tag for each company)",
            font=("Segoe UI", 12),
        )

        company_column_label.pack(pady=(0, 0))
        self.company_column_entry.pack(pady=(1, 0))
        multi_company_label.pack(pady=(8, 0))
        self.multi_company_entry.pack(pady=(1, 0))
        separate_company_tags_checkbox_frame.pack(pady=(10, 0))
        separate_company_tags_checkbox.pack(side=tk.LEFT)
        separate_company_tags_checkbox_label.pack(side=tk.LEFT)

    def create_custom_prompt_section(self):
        self.system_prompt_frame = tk.Frame(self.sentiment_tab_frame)

        system_prompt_reset_button = tk.Button(
            self.system_prompt_frame,
            text="Reset",
            font=("Segoe UI", 10),
            command=self.reset_system_prompt,
        )
        system_prompt_reset_button.pack(side=tk.LEFT)
        system_prompt_label = tk.Label(
            self.system_prompt_frame, text="System Prompt:", font=("Segoe UI", 12)
        )

        system_prompt_label.pack(side=tk.LEFT, padx=(5, 0))

        self.system_prompt_entry = tk.Text(
            self.sentiment_tab_frame,
            width=55,
            height=3,
            font=("Segoe UI", 11),
            wrap=tk.WORD,
        )
        self.system_prompt_entry.insert(
            tk.END,
            "Classify the sentiment of the following "
            "Text in one word from this list "
            "[Positive, Neutral, Negative].",
        )

        self.user_prompt_frame = tk.Frame(self.sentiment_tab_frame)

        user_prompt_label = tk.Label(
            self.user_prompt_frame, text="User Prompt:", font=("Segoe UI", 12)
        )
        user_prompt_label.pack(side=tk.LEFT, padx=(5, 0))

        self.user_prompt_entry_frame = tk.Frame(self.sentiment_tab_frame)

        self.user_prompt_entry = tk.Entry(
            self.user_prompt_entry_frame, width=7, font=("Segoe UI", 11)
        )
        self.user_prompt_entry.insert(tk.END, "Text:")
        self.user_prompt_entry.pack(side=tk.LEFT)
        user_prompt_tweet_label = tk.Label(
            self.user_prompt_entry_frame, text='"{Sample Text}"', font=("Segoe UI", 11)
        )
        user_prompt_tweet_label.pack(side=tk.LEFT, padx=(5, 5))
        self.user_prompt_entry2 = tk.Entry(
            self.user_prompt_entry_frame, width=12, font=("Segoe UI", 11)
        )
        self.user_prompt_entry2.insert(tk.END, "Sentiment:")
        self.user_prompt_entry2.pack(side=tk.LEFT)

    def create_model_selection(self):
        self.gpt_model_label = tk.Label(
            self.sentiment_tab_frame, text="GPT Model:", font=("Segoe UI", 12)
        )
        self.gpt_model_label.pack(pady=(20, 0))
        model_radio_frame = tk.Frame(self.sentiment_tab_frame)
        model_radio_frame.pack()
        model_options = [" GPT-3.5 ", " GPT-4o mini ", " GPT-4o "]
        for option in model_options:
            model_radio_button = ttk.Radiobutton(
                model_radio_frame,
                text=option,
                value=option,
                variable=self.gpt_model_var,
                style="radios.Toolbutton",
            )
            model_radio_button.pack(side="left")

    def create_run_button(self):
        self.sentiment_run_button = ttk.Button(
            self.sentiment_tab_frame,
            text="Run Sentiment Analysis",
            style="run.TButton",
            command=self.start_sentiment_analysis,
            takefocus=False,
        )
        self.sentiment_run_button.pack(pady=(30, 12), side="bottom")

    def create_bw_tab_run_button(self):
        self.bw_tab_frame.update_idletasks()
        # get tab width
        tab_width = self.sentiment_tab_frame.winfo_reqwidth()
        # Add the new label
        note_label = ttk.Label(
            self.bw_tab_frame,
            text="Note: This feature does not code sentiment and is only meant for updating BW with already-coded output files.",
            font=("Segoe UI", 10),
            justify="center",
            wraplength=(tab_width * 2) / 3,
        )
        note_label.pack(pady=(10, 5))

        self.bw_upload_button = ttk.Button(
            self.bw_tab_frame,
            text="Upload to Brandwatch",
            style="run.TButton",
            command=self.start_bw_upload,
            takefocus=False,
        )
        self.bw_upload_button.pack(pady=(5, 12))
        self.bw_api_metrics_button = ttk.Button(
            self.bw_tab_frame,
            text="Get BW API Metrics",
            style="run.TButton",
            command=self.start_metrics_analysis,
            takefocus=False,
        )
        self.bw_api_metrics_button.pack(pady=(20, 12))

    def create_progress_bar(self):
        self.placeholder_frame = ttk.Frame(self.progress_frame, height=11, width=450)
        self.placeholder_frame.pack(pady=(5, 0), fill=tk.X)
        self.placeholder_frame.pack_propagate(False)

    def create_log_area(self):
        self.log_label = ttk.Label(
            self.progress_frame, text="Log Messages:", font=("Segoe UI", 12)
        )
        self.log_label.pack(pady=(10, 0))
        log_font = tkFont.nametofont("TkDefaultFont")
        log_font.configure(size=12)
        self.log_text_area = ScrolledText(
            self.progress_frame,
            wrap=tk.WORD,
            padding=0,
            bootstyle="round",
            autohide=True,
            width=60,
            height=9,
            font=log_font,
        )
        self.log_text_area.text.configure(state="disabled")
        self.log_text_area.pack(pady=(2, 0), expand=True, fill=tk.BOTH)

    def toggle_advanced_options(self, event):
        if self.advanced_header.is_open:
            self.advanced_frame.pack(side=tk.RIGHT, padx=(10, 10), pady=10, fill=tk.Y)
        else:
            self.advanced_frame.pack_forget()

    def create_advanced_options(self):
        theme_frame = tk.Frame(self.advanced_frame)
        theme_frame.pack()

        theme_label = ttk.Label(theme_frame, text="Theme:")
        theme_label.pack()
        for option in [" System ", " Light ", " Dark "]:
            theme_radio_button = ttk.Radiobutton(
                theme_frame,
                text=option,
                value=option,
                variable=self.theme_var,
                style="radios.Toolbutton",
                command=self.update_theme,
            )
            theme_radio_button.pack(side="left")

        self.main_frame.update_idletasks()
        self.advanced_frame.update_idletasks()
        theme_frame.update_idletasks()

        input_height = self.input_section.winfo_reqheight()
        theme_height = theme_frame.winfo_reqheight()
        input_minus_theme = input_height - theme_height
        theme_label_height = theme_label.winfo_reqheight()
        
        tab_height = self.get_tab_height()
        spacer_height = tab_height + input_minus_theme - (theme_label_height / 2)

        # Add an empty frame
        top_spacer = ttk.Frame(self.advanced_frame, height=spacer_height)
        top_spacer.pack(side="top")
        
        notebook_frame_height = self.sentiment_tab_frame.winfo_reqheight()

        # Create notebook for advanced options
        self.advanced_options_label_frame = ttk.LabelFrame(
            self.advanced_frame,
            text="Advanced Options",
            takefocus=False,
            height=notebook_frame_height,
        )
        self.advanced_options_label_frame.pack(expand=True, fill=tk.Y)

        # Create the advanced options content frame
        advanced_options = ttk.Frame(
            self.advanced_options_label_frame, padding=[20, 5, 20, 5]
        )
        advanced_options.pack()

        advanced_reset_button = tk.Button(
            advanced_options,
            text="Reset to Defaults",
            font=("Segoe UI", 10),
            command=self.reset_advanced_options,
        )
        advanced_reset_button.pack(pady=(10, 0))

        self.logprob_checkbox = ttk.Checkbutton(
            advanced_options,
            text=" Output sentiment probabilities",
            variable=self.logprob_checkbox_var,
            style="Roundtoggle.Toolbutton",
        )
        self.logprob_checkbox.pack(pady=(15, 0))

        # temperature slider
        self.temperature_label = tk.Label(
            advanced_options, text="Temperature: 0.3", font=("Segoe UI", 12)
        )
        self.temperature_label.pack(pady=(15, 0))
        self.temperature_scale = ttk.Scale(
            advanced_options,
            length=200,
            from_=0,
            to=2,
            orient="horizontal",
            variable=self.temperature_var,
            command=self.update_temperature_label,
        )
        self.temperature_scale.pack(pady=(2, 0))

        # max tokens slider
        self.max_tokens_label = tk.Label(
            advanced_options, text="Max Completion Tokens: 1", font=("Segoe UI", 12)
        )
        self.max_tokens_label.pack(pady=(15, 0))
        self.max_tokens_scale = ttk.Scale(
            advanced_options,
            length=200,
            from_=1,
            to=20,
            orient="horizontal",
            variable=self.max_tokens_var,
            command=self.update_max_tokens_label,
        )
        self.max_tokens_scale.pack(pady=(2, 0))
        self.analyze_images_var = tk.BooleanVar(value=False)
        self.analyze_images_checkbox = ttk.Checkbutton(
            advanced_options,
            text=" Analyze images in posts (GPT-4o and 4o mini only)",
            variable=self.analyze_images_var,
            style="Roundtoggle.Toolbutton",
        )
        self.analyze_images_checkbox.pack(pady=(15, 0))

        # Add dual model section
        self.create_dual_model_section(advanced_options)
        self.progress_frame.update_idletasks()
        self.log_height = self.progress_frame.winfo_reqheight()
        # Add an empty frame at the bottom to account for log text area height
        bottom_spacer = ttk.Frame(self.advanced_frame, height=self.log_height + 10)
        bottom_spacer.pack(side="bottom", fill=tk.Y)

    def get_tab_height(self, tab_id=0):
        # Create temporary label to measure tab text height
        temp_label = ttk.Label(self.advanced_frame, text=self.notebook.tab(tab_id, "text"))
        tab_style = self.style.lookup("TNotebook.Tab", "font")
        if tab_style:
            temp_label.configure(font=tab_style)
        temp_label.update_idletasks()   
        height = temp_label.winfo_reqheight()

        tab_padding = self.style.lookup("TNotebook.Tab", "padding")
        if tab_padding:
            try:
                pad_top = int(tab_padding[1])
                pad_bottom = int(tab_padding[3] if len(tab_padding) > 3 else tab_padding[1])
                height += pad_top + pad_bottom
            except (IndexError, TypeError):
                pass

        # Get notebook padding
        notebook_padding = self.notebook.cget("padding")
        if notebook_padding:
            try:
                nb_top_padding = notebook_padding[1]  # Get top padding value
                height += nb_top_padding
            except (IndexError, TypeError):
                pass

        # Clean up the temporary label
        temp_label.destroy()
        return height

    def create_dual_model_section(self, parent_frame):
        """Create the dual model selection section in the advanced options."""
        self.dual_model_checkbox = ttk.Checkbutton(
            parent_frame,
            text=" Use two models",
            variable=self.dual_model_var,
            command=self.toggle_dual_model_options,
            style="Roundtoggle.Toolbutton",
        )
        self.dual_model_checkbox.pack(pady=(20, 0))

        # Create frame for dual model options (initially hidden)
        self.dual_model_frame = ttk.Frame(parent_frame)

        # Second model selection
        self.second_model_label = tk.Label(
            self.dual_model_frame, text="Second Model:", font=("Segoe UI", 12)
        )
        self.second_model_label.pack()

        model_radio_frame = tk.Frame(self.dual_model_frame)
        model_radio_frame.pack()
        for option in [" GPT-3.5 ", " GPT-4o mini ", " GPT-4o "]:
            model_radio_button = ttk.Radiobutton(
                model_radio_frame,
                text=option,
                value=option,
                variable=self.second_model_var,
                style="radios.Toolbutton",
            )
            model_radio_button.pack(side="left")

        # Split percentage slider
        self.split_label = tk.Label(
            self.dual_model_frame,
            text="First Model Percentage: 50%",
            font=("Segoe UI", 12),
        )
        self.split_label.pack(pady=(15, 0))

        self.split_scale = ttk.Scale(
            self.dual_model_frame,
            length=200,
            from_=5,
            to=95,
            orient="horizontal",
            variable=self.split_scale_var,
            command=self.update_split_label,
        )
        self.split_scale.pack(pady=(2, 0))

    def center_window(self):
        # Temporarily show advanced frame and multi-company option
        self.advanced_frame.pack(side=tk.RIGHT, padx=(10, 10), pady=10, fill=tk.Y)
        self.customization_var.set(" Multi-Company ")
        self.on_customization_selected()
        
        # Force window to calculate its dimensions
        self.master.update_idletasks()
        
        # Get window and screen dimensions
        window_width = self.master.winfo_reqwidth()
        window_height = self.master.winfo_reqheight()
        screen_width = self.master.winfo_screenwidth()
        
        # Get work area height (screen minus taskbar)
        if sys.platform.startswith('win'):
            try:
                from ctypes import windll
                work_area_height = windll.user32.GetSystemMetrics(17)  # SM_CYFULLSCREEN
            except Exception as e:
                print(f"Error getting work area height: {e}")
                work_area_height = self.master.winfo_screenheight() - 90  # Fallback
        else:
            work_area_height = self.master.winfo_screenheight() - 60  # Non-Windows fallback
        
        # Calculate position
        x = (screen_width - window_width) // 2
        y = (work_area_height - window_height) // 2
        
        # Reset to default state
        self.advanced_frame.pack_forget()
        self.customization_var.set(" Default ")
        self.on_customization_selected()
        
        # Set position
        self.master.geometry(f"+{x}+{y}")

    # GUI EVENT HANDLING FUNCTIONS
    def browse_input_file(self):
        file_path = filedialog.askopenfilename(
            title="Select an Input File (Excel, CSV, or Zip containing a CSV)",
            filetypes=[
                ("All Compatible Files", "*.xlsx *.csv *.zip"),
                ("Excel Files", "*.xlsx"),
                ("CSV Files", "*.csv"),
                ("Zip Files", "*.zip"),
            ],
        )
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, file_path)

    def browse_output_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx")],
        )
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, file_path)

    def check_file_exists(self, *args):
        output_path = self.output_var.get()
        input_path = self.input_var.get()
        
        # If output path is empty, no warning needed yet
        if not output_path:
            self.warning_label.config(text="")
            return
        
        # Apply the same default logic as in file_operations.py
        if not os.path.splitext(output_path)[1]:
            output_path += ".csv"
        
        if not os.path.dirname(output_path) and input_path:
            output_path = os.path.join(os.path.dirname(input_path), output_path)
        
        if os.path.isfile(output_path):
            self.warning_label.config(
                text=f"Warning: '{os.path.basename(output_path)}' exists and will be overwritten.", 
                fg="red"
            )
        else:
            self.warning_label.config(text="")

    def on_customization_selected(self, *args):
        selected_option = self.customization_var.get()
        if selected_option == " Default ":
            self.company_label.pack_forget()
            self.company_entry.pack_forget()
            self.multi_company_frame.pack_forget()
            self.system_prompt_frame.pack_forget()
            self.system_prompt_entry.pack_forget()
            self.user_prompt_frame.pack_forget()
            self.user_prompt_entry_frame.pack_forget()
        elif selected_option == " Company ":
            self.company_label.pack(before=self.gpt_model_label, pady=(15, 0))
            self.company_entry.pack(before=self.gpt_model_label)
            self.multi_company_frame.pack_forget()
            self.system_prompt_frame.pack_forget()
            self.system_prompt_entry.pack_forget()
            self.user_prompt_frame.pack_forget()
            self.user_prompt_entry_frame.pack_forget()
        elif selected_option == " Multi-Company ":
            self.company_label.pack_forget()
            self.company_entry.pack_forget()
            self.multi_company_frame.pack(before=self.gpt_model_label, pady=(15, 0))
            self.system_prompt_frame.pack_forget()
            self.system_prompt_entry.pack_forget()
            self.user_prompt_frame.pack_forget()
            self.user_prompt_entry_frame.pack_forget()
        elif selected_option == " Custom ":
            self.company_label.pack_forget()
            self.company_entry.pack_forget()
            self.multi_company_frame.pack_forget()
            self.system_prompt_frame.pack(before=self.gpt_model_label, pady=(18, 0))
            self.system_prompt_entry.pack(before=self.gpt_model_label, pady=(0, 0))
            self.user_prompt_frame.pack(before=self.gpt_model_label, pady=(5, 0))
            self.user_prompt_entry_frame.pack(before=self.gpt_model_label)

    def reset_system_prompt(self):
        self.system_prompt_entry.delete("1.0", tk.END)
        self.system_prompt_entry.insert(
            tk.END,
            "Classify the sentiment of the following "
            "Text in one word from this list "
            "[Positive, Neutral, Negative].",
        )
        self.user_prompt_entry.delete(0, tk.END)
        self.user_prompt_entry.insert(tk.END, "Text:")

    def update_temperature_label(self, value):
        formatted_value = "{:.1f}".format(
            float(value)
        )  # Round to 1 decimal place for display
        self.temperature_label.config(text=f"Temperature: {formatted_value}")

    def update_max_tokens_label(self, value):
        formatted_value = str(int(float(value)))  # Convert to whole integer
        self.max_tokens_label.config(text=f"Max Completion Tokens: {formatted_value}")

    def toggle_dual_model_options(self):
        if self.dual_model_var.get():
            self.dual_model_frame.pack(pady=(10, 0))
        else:
            self.dual_model_frame.pack_forget()

    def update_split_label(self, value):
        self.split_label.config(text=f"First Model Percentage: {int(float(value))}%")

    def reset_advanced_options(self):
        """Reset all advanced options to their default values."""
        # Reset variables to defaults
        self.logprob_checkbox_var.set(0)
        self.temperature_var.set(0.3)
        self.max_tokens_var.set(1)
        self.dual_model_var.set(False)
        self.second_model_var.set(" GPT-3.5 ")
        self.split_scale_var.set(50)

        # Update labels and hide dual model frame
        self.update_temperature_label(0.3)
        self.update_max_tokens_label(1)
        self.update_split_label(50)
        self.dual_model_frame.pack_forget()

    def start_sentiment_analysis(self):
        self.config_manager.update_sentiment_config(
            input_file=self.input_entry.get(),
            output_file=self.output_entry.get(),
            customization_option=self.customization_var.get().strip(),
            company_entry=self.company_entry.get(),
            system_prompt=self.system_prompt_entry.get("1.0", tk.END),
            user_prompt=self.user_prompt_entry.get(),
            user_prompt2=self.user_prompt_entry2.get(),
            gpt_model=self.gpt_model_var.get().strip(),
            update_brandwatch=bool(self.bw_checkbox_var.get()),
            output_probabilities=bool(self.logprob_checkbox_var.get()),
            company_column=self.company_column_entry.get(),
            multi_company_entry=self.multi_company_entry.get("1.0", tk.END),
            separate_company_analysis=bool(
                self.separate_company_tags_checkbox_var.get()
            ),
            temperature=float(self.temperature_scale.get()),
            max_tokens=int(self.max_tokens_scale.get()),
            analyze_images=bool(self.analyze_images_var.get()),
            use_dual_models=bool(self.dual_model_var.get()),
            second_gpt_model=self.second_model_var.get().strip(),
            model_split_percentage=int(self.split_scale_var.get()),
        )

        self.setup_progress_bar(self.placeholder_frame, self.progress_var)
        self.progress_var.set(0)
        connector_functions.setup_sentiment_analysis(
            config=self.config_manager.sentiment_config,
            update_progress_gui=self.update_progress_gui,
            log_message=self.log_message,
            enable_button=self.enable_button,
            disable_button=self.disable_button,
        )

    def start_bw_upload(self):
        self.setup_progress_bar(self.placeholder_frame, self.progress_var)
        self.progress_var.set(0)
        bw_upload_only.create_bw_upload_thread(
            input_file=self.input_entry.get(),
            update_progress_gui=self.update_progress_gui,
            log_message=self.log_message,
            enable_button=self.enable_button,
            disable_button=self.disable_button,
        )

    def start_metrics_analysis(self):
        metrics.analyze_api_metrics(
            log_message=self.log_message,
            enable_button=self.enable_button,
            disable_button=self.disable_button,
        )

    def setup_progress_bar(self, placeholder_frame, progress_var):
        if not hasattr(placeholder_frame, "progress_bar"):
            progress_bar = ttk.Progressbar(
                placeholder_frame,
                length=450,
                variable=progress_var,
                maximum=100,
                style="TProgressbar",
            )
            progress_bar.pack(fill=tk.BOTH, expand=True)
            placeholder_frame.progress_bar = progress_bar
        else:
            progress_bar = placeholder_frame.progress_bar
        return progress_bar

    def update_progress_gui(self, progress):
        def gui_safe_update():
            self.progress_var.set(progress)
            self.master.update_idletasks()

        self.master.after(0, gui_safe_update)

    def log_message(self, message):
        def gui_safe_log():
            self.log_text_area.text.configure(state="normal")
            self.log_text_area.insert(tk.END, message + "\n")
            self.log_text_area.text.configure(state="disabled")
            self.log_text_area.see(tk.END)

        self.master.after(0, gui_safe_log)

    def enable_button(self):
        self.sentiment_run_button.config(state=tk.NORMAL)
        self.bw_upload_button.config(state=tk.NORMAL)
        self.bw_api_metrics_button.config(state=tk.NORMAL)

    def disable_button(self):
        self.sentiment_run_button.config(state=tk.DISABLED)
        self.bw_upload_button.config(state=tk.DISABLED)
        self.bw_api_metrics_button.config(state=tk.DISABLED)


if __name__ == "__main__":
    enable_high_dpi_awareness()
    root = tk.Tk()
    app = SentimentAnalysisApp(root)
    root.mainloop()
