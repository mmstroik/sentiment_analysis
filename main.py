import os
import sys
import tkinter as tk
from tkinter import filedialog, scrolledtext
import tkinter.font as tkFont
from tkinter.font import nametofont
import webbrowser

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.utility import enable_high_dpi_awareness
from ttkbootstrap.tooltip import ToolTip

import pandas as pd
import darkdetect
from functools import partial

from src import connector_functions, bw_upload_only, metrics, tkmd, input_config


class SentimentAnalysisApp:
    def __init__(self, master):
        self.master = master
        self.master.minsize(450, 200)
        self.master.title("Sentiment Analysis Tool")
        icon_path = self.resource_path("themes/pie_icon.ico")
        self.master.iconbitmap(icon_path)

        # initialize styles
        self.init_styles()

        # Initialize variables
        self.init_variables()

        # Create and setup GUI components
        self.create_gui()

        self.config_manager = input_config.ConfigManager()

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

            if darkdetect.isDark():
                self.style.theme_use("custom-dark")
            else:
                self.style.theme_use("custom-light")

        except Exception as e:
            print(f"Error loading themes: {e}")
            self.style.theme_use("darkly")

        self.style.configure("TNotebook", tabposition="n")
        self.style.configure("Toolbutton", font=("Segoe UI", 12))
        self.style.configure("radios.Toolbutton", font=("Segoe UI", 11), padding=5)
        self.style.configure("run.TButton", font=("Segoe UI", 13))
        self.style.configure("tooltip.TLabel", font=("Segoe UI", 10))
        self.default_font = tkFont.nametofont("TkDefaultFont")
        self.default_font.configure(family="Segoe UI")

    def init_variables(self):
        self.input_var = tk.StringVar()
        self.input_var.trace_add("write", self.check_file_exists)
        self.output_var = tk.StringVar()
        self.output_var.trace_add("write", self.check_file_exists)
        self.progress_var = tk.DoubleVar()
        self.customization_var = tk.StringVar(value=" Default ")
        self.gpt_model_var = tk.StringVar(value=" GPT-4o mini ")
        self.bw_checkbox_var = tk.IntVar()
        self.advanced_checkbox_var = tk.IntVar()
        self.logprob_checkbox_var = tk.IntVar()
        self.separate_company_tags_checkbox_var = tk.IntVar()

    def create_gui(self):
        # Main frames
        self.instructions_frame = ttk.Frame(self.master)
        self.instructions_frame.pack(
            side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.BOTH
        )
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.BOTH)
        self.advanced_frame = ttk.Frame(self.master)

        # Create GUI components
        self.create_input_section()
        self.create_notebook()
        self.create_sentiment_tab()
        self.create_bw_tab_run_button()
        self.create_progress_bar()
        self.create_log_area()
        self.create_instructions()
        self.create_advanced_options()

    def create_input_section(self):
        input_label = tk.Label(
            self.main_frame, text="Input File:", font=("Segoe UI", 12)
        )
        input_label.pack()

        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack()

        self.input_entry = tk.Entry(
            input_frame, textvariable=self.input_var, width=50, font=("Segoe UI", 11)
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
            self.main_frame, style="TNotebook", takefocus=False, padding=[0, 15, 0, 10]
        )
        self.notebook.pack(expand=True, fill=tk.BOTH)

        self.sentiment_tab_frame = tk.Frame(self.notebook)
        self.notebook.add(
            self.sentiment_tab_frame, text="Sentiment Analysis", padding=[15, 5, 15, 5]
        )

        self.bw_tab_frame = tk.Frame(self.notebook)
        self.notebook.add(
            self.bw_tab_frame, text="BW Upload Only", padding=[15, 5, 15, 5]
        )

    def create_sentiment_tab(self):
        self.create_output_section()
        self.create_main_checkboxes()
        self.create_customization_section()
        self.create_model_selection()
        self.create_run_button()

    def create_output_section(self):
        output_label = tk.Label(
            self.sentiment_tab_frame, text="Output File:", font=("Segoe UI", 12)
        )
        output_label.pack(pady=(3, 0))

        output_frame = tk.Frame(self.sentiment_tab_frame)
        output_frame.pack()

        self.output_entry = tk.Entry(
            output_frame, textvariable=self.output_var, width=50, font=("Segoe UI", 11)
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

        advanced_checkbox = ttk.Checkbutton(
            self.sentiment_tab_frame,
            text=" Advanced Options",
            variable=self.advanced_checkbox_var,
            style="Roundtoggle.Toolbutton",
            command=self.on_advanced_checkbox,
        )
        advanced_checkbox.pack(pady=(15, 0))

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
            self.sentiment_tab_frame, width=16, font=("Segoe UI", 11)
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
            self.multi_company_frame, width=20, font=("Segoe UI", 11)
        )

        multi_company_label = tk.Label(
            self.multi_company_frame,
            text="List BW companies seperated by commas (in order of priority):",
            font=("Segoe UI", 12),
        )
        self.multi_company_entry = tk.Text(
            self.multi_company_frame,
            width=52,
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
            width=50,
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
            self.user_prompt_entry_frame, width=6, font=("Segoe UI", 11)
        )
        self.user_prompt_entry.insert(tk.END, "Text:")
        self.user_prompt_entry.pack(side=tk.LEFT)
        user_prompt_tweet_label = tk.Label(
            self.user_prompt_entry_frame, text='"{Sample Text}"', font=("Segoe UI", 11)
        )
        user_prompt_tweet_label.pack(side=tk.LEFT, padx=(5, 5))
        self.user_prompt_entry2 = tk.Entry(
            self.user_prompt_entry_frame, width=10, font=("Segoe UI", 11)
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
        )
        self.sentiment_run_button.pack(pady=(30, 12), side="bottom")

    def create_bw_tab_run_button(self):
        # Add the new label
        note_label = ttk.Label(
            self.bw_tab_frame,
            text="Note: This feature does not code sentiment and is only meant for\n"
            "updating BW with already-coded output files.",
            font=("Segoe UI", 10),
            justify="center",
            wraplength=400,
        )
        note_label.pack(pady=(10, 5))

        self.bw_upload_button = ttk.Button(
            self.bw_tab_frame,
            text="Upload to Brandwatch",
            style="run.TButton",
            command=self.start_bw_upload,
        )
        self.bw_upload_button.pack(pady=(5, 12))
        self.bw_api_metrics_button = ttk.Button(
            self.bw_tab_frame,
            text="Get BW API Metrics",
            style="run.TButton",
            command=self.start_metrics_analysis,
        )
        self.bw_api_metrics_button.pack(pady=(20, 12))

    def create_progress_bar(self):
        self.placeholder_frame = ttk.Frame(self.main_frame, height=11, width=450)
        self.placeholder_frame.pack(pady=(5, 0), padx=(5, 5), fill=tk.X)
        self.placeholder_frame.pack_propagate(False)

    def create_log_area(self):
        log_label = ttk.Label(
            self.main_frame, text="Log Messages:", font=("Segoe UI", 12)
        )
        log_label.pack(pady=(10, 0))

        self.log_text_area = scrolledtext.ScrolledText(
            self.main_frame, wrap=tk.WORD, width=57, height=9, font=("Segoe UI", 11)
        )
        self.log_text_area.configure(state="disabled")
        self.log_text_area.pack(pady=(2, 0))

    def create_instructions(self):
        instructions_font = tkFont.nametofont("TkDefaultFont")
        instructions_font.configure(size=12)
        instructions_label = tk.Label(
            self.instructions_frame, text="Instructions:", font=("Segoe UI", 12)
        )
        instructions_label.pack(fill="x")

        instructions_text_area = tkmd.SimpleMarkdownText(
            self.instructions_frame,
            wrap=tk.WORD,
            width=50,
            height=34,
            font=instructions_font,
        )
        instructions_text_area.pack(fill=BOTH, expand=True)

        instructions_text = """1. Ensure your input file is a .xlsx or .csv (or .zip containing a .csv) with a "Content" or "Full Text" column (default for BW).
* Note: Works with column headers in any of the first 20 rows (BW exports).

2. Click on the "Browse" button next to "Input File" and select the file containing the mentions.
* Note: If the file is saved to OneDrive/SharePoint, close it before running the tool.

3. Click on the "Browse" button next to "Output File" and create a new filename for the output.

4. (Optional): Update sentiment values in Brandwatch (will also mark updated mentions as "Checked" in BW).
* Requires 'Query Id' and 'Resource Id' columns in input file

5. (Optional) Select a customization option:
* Default: Use the default system and user prompts.
* Company: Specify a single company name.
* Multi-Company: Specify Brandwatch company categories
* Custom: Provide custom system and user prompts

6. (Optional) Select a model:
* GPT-3.5 (Legacy): Less accurate but much less neutral
* GPT-4o mini: Best for larger batches and/or shorter text.
* GPT-4o: Best for smaller batches and/or long text.
            
7. Click "Run Sentiment Analysis. A success message will be displayed when finished.
"""
        instructions_text_area.insert_markdown(instructions_text)

        hyperlink = tkmd.HyperlinkManager(instructions_text_area)
        instructions_text_area.insert(
            "end",
            "Full Documentation/Instructions",
            hyperlink.add(
                partial(
                    webbrowser.open,
                    "https://docs.google.com/document/d/1R5qPnn5xbGOv3aZk6Cf5egfvrMVJ6TI2v_xg6FiFqp8/edit",
                )
            ),
        )
        instructions_text_area.configure(state="disabled")

    def create_advanced_options(self):
        # Create a container frame to hold all content
        content_frame = ttk.Frame(self.advanced_frame)
        
        # Create all widgets in the content frame instead of advanced_frame
        self.advanced_options_label = tk.Label(
            content_frame, text="Advanced Options:", font=("Segoe UI", 12)
        )
        self.advanced_options_label.pack()

        self.logprob_checkbox = ttk.Checkbutton(
            content_frame,
            text=" Output probabilities for each sentiment prediction",
            variable=self.logprob_checkbox_var,
            style="Roundtoggle.Toolbutton",
        )
        self.logprob_checkbox.pack(pady=(15, 0))

        # temperature slider
        self.temperature_label = tk.Label(
            content_frame, text="Temperature: 0.3", font=("Segoe UI", 12)
        )
        self.temperature_label.pack(pady=(15, 0))
        self.temperature_scale = ttk.Scale(
            content_frame,
            length=200,
            from_=0,
            to=2,
            orient="horizontal",
            value=0.3,
            command=self.update_temperature_label,
        )
        self.temperature_scale.pack(pady=(2, 0))

        # max tokens slider
        self.max_tokens_label = tk.Label(
            content_frame, text="Max Completion Tokens: 1", font=("Segoe UI", 12)
        )
        self.max_tokens_label.pack(pady=(15, 0))
        self.max_tokens_scale = ttk.Scale(
            content_frame,
            length=200,
            from_=1,
            to=20,
            orient="horizontal",
            value=1,
            command=self.update_max_tokens_label,
        )
        self.max_tokens_scale.pack(pady=(2, 0))

        # Pack the content frame with expand=True to center it vertically
        content_frame.pack(expand=True)

        # Add an empty frame at the bottom to push content up slightly
        bottom_spacer = ttk.Frame(self.advanced_frame, height=200)  # Adjust height as needed
        bottom_spacer.pack(side='bottom')

    def update_temperature_label(self, value):
        formatted_value = "{:.1f}".format(
            float(value)
        )  # Round to 1 decimal place for display
        self.temperature_label.config(text=f"Temperature: {formatted_value}")

    def update_max_tokens_label(self, value):
        formatted_value = str(int(float(value)))  # Convert to whole integer
        self.max_tokens_label.config(text=f"Max Completion Tokens: {formatted_value}")

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
        file_path = self.output_var.get()
        if os.path.isfile(file_path):
            self.warning_label.config(
                text="Warning: output file exists and will be overwritten.", fg="red"
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

    def on_advanced_checkbox(self):
        advanced_checkbox_bool = self.advanced_checkbox_var.get()
        if advanced_checkbox_bool:
            self.advanced_frame.pack(
                side=tk.RIGHT, padx=(20, 20), pady=10, expand=True, fill=tk.BOTH
            )
        else:
            self.advanced_frame.pack_forget()

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
            self.log_text_area.configure(state="normal")
            self.log_text_area.insert(tk.END, message + "\n")
            self.log_text_area.configure(state="disabled")
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
