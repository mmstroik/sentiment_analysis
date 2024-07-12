import ctypes
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

import pandas as pd
import darkdetect
from functools import partial

from src.connector_functions import setup_sentiment_analysis, create_bw_upload_thread
from src.tkmd import SimpleMarkdownText, HyperlinkManager


# Calls connnector functions (triggered on button click)
def start_sentiment_analysis():
    setup_progress_bar(placeholder_frame, progress_var)
    progress_var.set(0)
    setup_sentiment_analysis(
        input_file=input_entry.get(),
        output_file=output_entry.get(),
        update_progress_gui=update_progress_gui,
        log_message=log_message,
        enable_button=enable_button,
        disable_button=disable_button,
        customization_option=customization_var.get(),
        company_entry=company_entry.get(),
        system_prompt_entry=system_prompt_entry.get("1.0", tk.END),
        user_prompt_entry=user_prompt_entry.get(),
        user_prompt_entry2=user_prompt_entry2.get(),
        gpt_model=gpt_model_var.get(),
        bw_checkbox_var=bw_checkbox_var.get(),
        logprob_checkbox_var=logprob_checkbox_var.get(),
    )


def start_bw_upload():
    setup_progress_bar(placeholder_frame, progress_var)
    progress_var.set(0)
    create_bw_upload_thread(
        input_file=input_entry.get(),
        update_progress_gui=update_progress_gui,
        log_message=log_message,
        enable_button=enable_button,
        disable_button=disable_button,
    )


"""GUI EVENT HANDLING FUNCTIONS"""


def enable_button():
    window.after(0, sentiment_run_button.config, {"state": tk.NORMAL})
    window.after(0, bw_upload_button.config, {"state": tk.NORMAL})


def disable_button():
    window.after(0, sentiment_run_button.config, {"state": tk.DISABLED})
    window.after(0, bw_upload_button.config, {"state": tk.DISABLED})


# Set up the progress bar widget that gets updated by the core logic
def setup_progress_bar(placeholder_frame, progress_var):
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


# Log a message to the GUI
def log_message(message):
    def gui_safe_log():
        log_text_area.configure(state="normal")
        log_text_area.insert(tk.END, message + "\n")
        log_text_area.configure(state="disabled")
        log_text_area.see(tk.END)

    window.after(0, gui_safe_log)


# Update the progress bar
def update_progress_gui(progress):
    def gui_safe_update():
        progress_var.set(progress)
        window.update_idletasks()

    window.after(0, gui_safe_update)


# Browse for input file
def browse_input_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
    input_entry.delete(0, tk.END)
    input_entry.insert(0, file_path)


# Browse for output file
def browse_output_file():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")]
    )
    output_entry.delete(0, tk.END)
    output_entry.insert(0, file_path)


# Used for warning message
def check_file_exists(*args):
    file_path = output_var.get()
    if os.path.isfile(file_path):
        warning_label.config(
            text="Warning: output file exists and will be overwritten.", fg="red"
        )
    else:
        warning_label.config(text="")


# Reset the system and user prompt entry
def reset_system_prompt():
    system_prompt_entry.delete("1.0", tk.END)
    system_prompt_entry.insert(
        tk.END,
        "Classify the sentiment of the following "
        "Text in one word from this list "
        "[Positive, Neutral, Negative].",
    )
    user_prompt_entry.delete(0, tk.END)
    user_prompt_entry.insert(tk.END, "Text:")


def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder for icon
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Handle GUI changes based on the customization option selected
def on_customization_selected(*args):
    selected_option = customization_var.get()
    if selected_option == "Default":
        company_label.pack_forget()
        company_entry.pack_forget()
        system_prompt_frame.pack_forget()
        system_prompt_entry.pack_forget()
        user_prompt_frame.pack_forget()
        user_prompt_entry_frame.pack_forget()
    elif selected_option == "Company":
        company_label.pack(before=gpt_model_label, pady=(15, 0))
        company_entry.pack(before=gpt_model_label)
        system_prompt_frame.pack_forget()
        system_prompt_entry.pack_forget()
        user_prompt_frame.pack_forget()
        user_prompt_entry_frame.pack_forget()
    elif selected_option == "Custom":
        company_label.pack_forget()
        company_entry.pack_forget()
        system_prompt_frame.pack(before=gpt_model_label, pady=(18, 0))
        system_prompt_entry.pack(before=gpt_model_label, pady=(0, 0))
        user_prompt_frame.pack(before=gpt_model_label, pady=(5, 0))
        user_prompt_entry_frame.pack(before=gpt_model_label)


# DPI scaling
def set_dpi_awareness():
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except AttributeError:
            pass
        except Exception as e:
            print(f"Error setting DPI Awareness: {e}")


"""GUI SETUP"""


enable_high_dpi_awareness()

# Create the main window
window = tk.Tk()

if darkdetect.isDark():
    style = ttk.Style("quadrant")
else:
    style = ttk.Style("quadrant-light")

window.minsize(450, 200)
window.title("Sentiment Analysis Tool")
icon_path = resource_path("pie_icon.ico")
window.iconbitmap(icon_path)

default_font = tkFont.nametofont("TkDefaultFont")
default_font.configure(family="Segoe UI")

# Create a progress bar variable
progress_var = tk.DoubleVar()

# Create two main frames
main_frame = tk.Frame(window)
main_frame.pack(side=RIGHT, padx=10, pady=10, expand=True, fill=BOTH)
instructions_frame = tk.Frame(window)
instructions_frame.pack(side=LEFT, padx=10, pady=10, expand=True, fill=BOTH)

# Input file packing
input_label = tk.Label(main_frame, text="Input File:", font=("Segoe UI", 12))
input_label.pack()

# Create a frame to hold the button and the entry
input_frame = tk.Frame(main_frame)
input_frame.pack()

# input var for existing file check function
input_var = tk.StringVar()
input_var.trace_add("write", check_file_exists)
input_entry = tk.Entry(input_frame, textvariable=input_var, width=50, font=("Segoe UI", 11))
input_entry.pack(side=tk.RIGHT, padx=(0, 10))

# Add a bit of packing in between the button and entry
input_button = tk.Button(
    input_frame, text="Browse", font=("Segoe UI", 11), command=browse_input_file
)
input_button.pack(side=tk.RIGHT, padx=(10, 0))

# create notebook with tabs
style.configure('TNotebook', tabposition='n') 
notebook = ttk.Notebook(main_frame, style='TNotebook', takefocus=False, padding=[0, 15, 0, 10])
notebook.pack(expand=True, fill=BOTH)

# Sentiment tab
sentiment_tab_frame = tk.Frame(notebook)
notebook.add(sentiment_tab_frame, text="Sentiment Analysis")

# BW tab
bw_tab_frame = tk.Frame(notebook)
notebook.add(bw_tab_frame, text="BW Upload Only")

# Output file packing
output_label = tk.Label(sentiment_tab_frame, text="Output File:", font=("Segoe UI", 12))
output_label.pack(pady=(3, 0))

output_var = tk.StringVar()
output_var.trace_add("write", check_file_exists)

output_frame = tk.Frame(sentiment_tab_frame)
output_frame.pack()

output_entry = tk.Entry(
    output_frame, textvariable=output_var, width=50, font=("Segoe UI", 11)
)
output_entry.pack(side=tk.RIGHT, padx=(0, 10))

output_button = tk.Button(
    output_frame,
    text="Browse",
    font=("Segoe UI", 11),
    command=browse_output_file,
)
output_button.pack(side=tk.RIGHT, padx=(10, 0))

warning_label = tk.Label(
    sentiment_tab_frame, text="", font=("Segoe UI", 10, "italic"), fg="#b53d38"
)
warning_label.pack()

# BW API update checkbox
style.configure("Toolbutton", font=("Segoe UI", 12))
bw_checkbox_var = tk.IntVar()

bw_checkbox = ttk.Checkbutton(
    sentiment_tab_frame,
    text=" Update sentiment values in Brandwatch",
    variable=bw_checkbox_var,
    style="Roundtoggle.Toolbutton",
)
bw_checkbox.pack(pady=(0, 0))


# logprob checkbox
logprob_checkbox_var = tk.IntVar()
logprob_checkbox = ttk.Checkbutton(
    sentiment_tab_frame,
    text=" Output probabilities for each sentiment prediction",
    variable=logprob_checkbox_var,
    style="Roundtoggle.Toolbutton",
)
logprob_checkbox.pack(pady=(15, 0))


# Prompt customization option packing
style.configure("radios.Toolbutton", font=("Segoe UI", 11), padding=5)
customization_label = tk.Label(
    sentiment_tab_frame, text="Prompt Customization Option:", font=("Segoe UI", 12)
)
customization_label.pack(pady=(15, 0))
customization_var = tk.StringVar(value="Default")
prompt_radio_frame = tk.Frame(sentiment_tab_frame)
prompt_radio_frame.pack()
prompt_options = ["Default", "Company", "Custom"]
for option in prompt_options:
    prompt_radio_button = ttk.Radiobutton(
        prompt_radio_frame,
        text=option,
        value=option,
        variable=customization_var,
        style="radios.Toolbutton",
        command=on_customization_selected,
        width=9,
    )
    prompt_radio_button.pack(side="left")


# Company entry
company_label = tk.Label(
    sentiment_tab_frame, text="Company name:", font=("Segoe UI", 12)
)
company_entry = tk.Entry(sentiment_tab_frame, width=16, font=("Segoe UI", 11))


# System prompt
system_prompt_frame = tk.Frame(sentiment_tab_frame)

system_prompt_reset_button = tk.Button(
    system_prompt_frame,
    text="Reset",
    font=("Segoe UI", 10),
    command=reset_system_prompt,
)
system_prompt_reset_button.pack(side=tk.LEFT)
system_prompt_label = tk.Label(
    system_prompt_frame, text="System Prompt:", font=("Segoe UI", 12)
)

system_prompt_label.pack(side=tk.LEFT, padx=(5, 0))

system_prompt_entry = tk.Text(
    sentiment_tab_frame, width=50, height=3, font=("Segoe UI", 11), wrap=tk.WORD
)
system_prompt_entry.insert(
    tk.END,
    "Classify the sentiment of the following "
    "Text in one word from this list "
    "[Positive, Neutral, Negative].",
)


# User prompt
user_prompt_frame = tk.Frame(sentiment_tab_frame)

user_prompt_label = tk.Label(
    user_prompt_frame, text="User Prompt:", font=("Segoe UI", 12)
)
user_prompt_label.pack(side=tk.LEFT, padx=(5, 0))

user_prompt_entry_frame = tk.Frame(sentiment_tab_frame)

user_prompt_entry = tk.Entry(user_prompt_entry_frame, width=6, font=("Segoe UI", 11))
user_prompt_entry.insert(tk.END, "Text:")
user_prompt_entry.pack(side=tk.LEFT)
user_prompt_tweet_label = tk.Label(
    user_prompt_entry_frame, text=' "{Sample Text}"', font=("Segoe UI", 11)
)
user_prompt_tweet_label.pack(side=tk.LEFT, padx=(5, 5))
user_prompt_entry2 = tk.Entry(user_prompt_entry_frame, width=10, font=("Segoe UI", 11))
user_prompt_entry2.insert(tk.END, "Sentiment:")
user_prompt_entry2.pack(side=tk.LEFT)

# GPT Model Selection
gpt_model_label = tk.Label(
    sentiment_tab_frame, text="GPT Model:", font=("Segoe UI", 12)
)
gpt_model_label.pack(pady=(20, 0))
gpt_model_var = tk.StringVar(value="GPT-3.5")
model_radio_frame = tk.Frame(sentiment_tab_frame)
model_radio_frame.pack()
model_options = ["GPT-3.5", "GPT-4", "GPT-4o"]
for option in model_options:
    model_radio_button = ttk.Radiobutton(
        model_radio_frame,
        text=option,
        value=option,
        variable=gpt_model_var,
        style="radios.Toolbutton",
        width=7,
    )
    model_radio_button.pack(side="left")


# Sentiment run button
style.configure("run.TButton", font=("Segoe UI", 13))
sentiment_run_button = ttk.Button(
    sentiment_tab_frame,
    text="Run Sentiment Analysis",
    style="run.TButton",
    command=start_sentiment_analysis,
)
sentiment_run_button.pack(pady=(30, 12), side="bottom")


# BW upload button
style.configure("run.TButton", font=("Segoe UI", 13))
bw_upload_button = ttk.Button(
    bw_tab_frame,
    text="Upload to Brandwatch",
    style="run.TButton",
    command=start_bw_upload,
)
bw_upload_button.pack(pady=(30, 12))


# Placeholder frame for progress bar
placeholder_frame = tk.Frame(main_frame, height=11, width=450)
placeholder_frame.pack(pady=(5, 0), padx=(5, 5), fill=tk.X)
placeholder_frame.pack_propagate(False)


# Logging section
log_label = tk.Label(main_frame, text="Log Messages:", font=("Segoe UI", 12))
log_label.pack(pady=(10, 0))
log_text_area = scrolledtext.ScrolledText(
    main_frame, wrap=tk.WORD, width=55, height=9, font=("Segoe UI", 11)
)
log_text_area.configure(state="disabled")
log_text_area.pack(pady=(2, 0))

instructions_text = """1. Ensure your input file is a .xlsx and contains a column named "Full Text".
* Note: Works with column headers in any of the first 20 rows (BW exports).

2. Click on the "Browse" button under "Input File" and select the file containing the mentions/tweets.
* Note: If the file is saved to OneDrive, close it before running the tool.

3. Click on the "Browse" button under "Output File" and choose a location and filename for the output.

4. (Optional): Update sentiment values in Brandwatch (will also mark updated mentions as "Checked" in BW).
* Requires 'Query Id' and 'Resource Id' columns in input file

5. (Optional) Select a customization option:
* Default: Use the default system and user prompts.
* Company: Specify a company name to analyze sentiment "towards".
* Custom: Provide custom system and user prompts

6. (Optional) Select a model:
* GPT-3.5: Best for large batches with less complex text samples.
* GPT-4: Best for smaller sample sizes and/or longer text samples.
    
7. Click "Run Sentiment Analysis. 
* A success message will be displayed when finished.
"""

instructions_font = tkFont.nametofont("TkDefaultFont")
instructions_font.configure(size=12)
instructions_label = tk.Label(
    instructions_frame, text="Instructions:", font=("Segoe UI", 12)
)
instructions_label.pack(fill="x")
instructions_text_area = SimpleMarkdownText(
    instructions_frame,
    wrap=tk.WORD,
    width=50,
    height=34,
    font=instructions_font,
)
instructions_text_area.pack(fill=BOTH, expand=True)
instructions_text_area.insert_markdown(instructions_text)

hyperlink = HyperlinkManager(instructions_text_area)
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


# Start the GUI event loop
window.mainloop()
