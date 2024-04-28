import asyncio
import ctypes
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import tkinter.font as tkFont
import webbrowser

import sv_ttk
import pandas as pd

from async_core_logic import process_tweets_in_batches
from bw_api_handling import update_bw_sentiment
import darkdetect


"""GUI <-> CORE LOGIC CONNECTOR FUNCTIONS"""


# Set the token and requests limits based on model selection
def select_model(gpt_model_var):
    model_limits = {
        "gpt-3.5-turbo": {"token_limit": 160000, "requests_limit": 5000},
        "gpt-4-turbo": {"token_limit": 600000, "requests_limit": 5000},
    }
    model = (
        "gpt-3.5-turbo" if gpt_model_var.get() == "GPT-3.5 (Default)" else "gpt-4-turbo"
    )
    return (
        model,
        model_limits[model]["token_limit"],
        model_limits[model]["requests_limit"],
    )


# Set the system and user prompts based on the customization option selected
def set_prompts(
    customization_option, company_entry, system_prompt_entry, user_prompt_entry
):
    if customization_option == "Default":
        system_prompt = "Classify the sentiment of the following Text in one word from this list [Positive, Neutral, Negative]."
        user_prompt = "Text:"
    elif customization_option == "Company":
        company = company_entry.get()
        system_prompt = f"Classify the sentiment of the following Text toward {company} in one word from this list [Positive, Neutral, Negative]."
        user_prompt = "Text:"
    elif customization_option == "Custom":
        system_prompt = system_prompt_entry.get("1.0", tk.END).strip()
        user_prompt = user_prompt_entry.get()
    return system_prompt, user_prompt


# Main function to run sentiment analysis
# (called when the "Run Sentiment Analysis" button is clicked)
def run_sentiment_analysis():
    global progress_bar
    input_file = input_entry.get()
    output_file = output_entry.get()
    customization_option = customization_var.get()
    if not input_file or not output_file:
        messagebox.showerror(
            "Error", "Please provide both input and output file paths."
        )
        return
    model, batch_token_limit, batch_requests_limit = select_model(gpt_model_var)
    system_prompt, user_prompt = set_prompts(
        customization_option, company_entry, system_prompt_entry, user_prompt_entry
    )
    progress_bar = setup_progress_bar(placeholder_frame, progress_var)
    progress_var.set(0)
    run_button.config(state=tk.DISABLED)
    try:
        thread = threading.Thread(
            target=run_sentiment_analysis_thread,
            args=(
                input_file,
                output_file,
                update_progress_gui,
                system_prompt,
                user_prompt,
                model,
                batch_token_limit,
                batch_requests_limit,
            ),
        )
        thread.start()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        run_button.config(state=tk.NORMAL)


# Handle file reading and writing and call the core logic in a separate thread
def run_sentiment_analysis_thread(
    input_file,
    output_file,
    update_progress_callback,
    system_prompt,
    user_prompt,
    model,
    batch_token_limit,
    batch_requests_limit,
):
    log_message(
        f"Starting sentiment analysis for text samples in {os.path.basename(input_file)}."
    )

    df = pd.read_excel(input_file)
    if "Full Text" not in df.columns:
        df = pd.read_excel(input_file, skiprows=9)

    if "Full Text" not in df.columns:
        messagebox.showerror(
            "Error",
            "The input file does not contain the required column 'Full Text'.",
        )
        window.after(0, lambda: run_button.config(state=tk.NORMAL))
        return
    
    log_message("'Full Text' column found.")

    if bw_checkbox_var.get():
        if "Query Id" not in df.columns or "Resource Id" not in df.columns:
            messagebox.showerror(
                "Error",
                "The input file does not contain the required BW columns 'Query Id' or 'Resource Id'.",
            )
            window.after(0, lambda: run_button.config(state=tk.NORMAL))
            return
        
    if "Sentiment" not in df.columns:
        df["Sentiment"] = ""

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    df = loop.run_until_complete(
        process_tweets_in_batches(
            df,
            update_progress_callback,
            log_message,
            system_prompt,
            user_prompt,
            model,
            batch_token_limit,
            batch_requests_limit,
        )
    )
    loop.close()

    if bw_checkbox_var.get():
        log_message(f"Updating sentiment values in Brandwatch...")
        update_bw_sentiment(df, log_message)

    # Remove the token count column and save the df to the output file
    log_message(f"Saving results to excel...")
    df.drop(columns=["Token Count"], inplace=True)
    update_progress_callback(98)
    df.to_excel(output_file, index=False)
    update_progress_callback(100)
    log_message(f"Sentiment analysis results saved to {output_file}.")
    messagebox.showinfo("Success", "Sentiment analysis completed successfully.")
    window.after(0, lambda: run_button.config(state=tk.NORMAL))
    return df


"""GUI EVENT HANDLING FUNCTIONS"""


# Set up the progress bar widget that gets updated by the core logic
def setup_progress_bar(placeholder_frame, progress_var):
    if not hasattr(placeholder_frame, "progress_bar"):
        progress_bar = ttk.Progressbar(
            placeholder_frame, length=400, variable=progress_var, maximum=100
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
def on_customization_selected(event):
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
        system_prompt_frame.pack(before=gpt_model_label, pady=(20, 0))
        system_prompt_entry.pack(before=gpt_model_label, pady=(2, 0))
        user_prompt_frame.pack(before=gpt_model_label, pady=(5, 0))
        user_prompt_entry_frame.pack(before=gpt_model_label)


# DPI scaling
def set_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except AttributeError:
        pass
    except Exception as e:
        print(f"Error setting DPI Awareness: {e}")


"""GUI SETUP"""

set_dpi_awareness()

# Create the main window
window = tk.Tk()
window.title("Sentiment Analysis Tool")
icon_path = resource_path("pie_icon.ico")
window.iconbitmap(icon_path)

# Create a progress bar variable
progress_var = tk.DoubleVar()

# Create frames for input/output and instructions
main_frame = tk.Frame(window)
main_frame.pack(side=tk.RIGHT, padx=10, pady=10, expand=True, fill=tk.BOTH)

instructions_frame = tk.Frame(window)
instructions_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH)

# Input file packing
input_label = tk.Label(main_frame, text="Input File:", font=("Segoe UI", 12))
input_label.pack()
input_entry = tk.Entry(main_frame, width=50, font=("Segoe UI", 11))
input_entry.pack()
input_button = tk.Button(
    main_frame, text="Browse", font=("Segoe UI", 12), command=browse_input_file
)
input_button.pack()

# Output file packing
output_label = tk.Label(main_frame, text="Output File:", font=("Segoe UI", 12))
output_label.pack(pady=(20, 0))
output_entry = tk.Entry(main_frame, width=50, font=("Segoe UI", 11))
output_entry.pack()
output_button = tk.Button(
    main_frame, text="Browse", font=("Segoe UI", 12), command=browse_output_file
)
output_button.pack()

# BW API update checkbox
bw_checkbox_var = tk.IntVar()
style = ttk.Style()
style.configure("TCheckbutton", font=("Segoe UI", 14))
bw_checkbox = ttk.Checkbutton(
    main_frame,
    text="Update sentiment values in Brandwatch",
    variable=bw_checkbox_var,
    style="TCheckbutton",
)
bw_checkbox.pack(pady=(20, 0))
bw_checkbox_label = tk.Label(
    main_frame,
    text="(Requires 'Query Id' and 'Resource Id' columns in input file)",
    font=("Segoe UI", 10, "italic"),
)
bw_checkbox_label.pack()

# Customization option packing
customization_label = tk.Label(
    main_frame, text="Customization Option:", font=("Segoe UI", 12)
)
customization_label.pack(pady=(20, 0))
customization_var = tk.StringVar()
customization_var.set("Default")
customization_dropdown = ttk.Combobox(
    main_frame,
    textvariable=customization_var,
    values=["Default", "Company", "Custom"],
    font=("Segoe UI", 11),
    state="readonly",
    width=12,
)
customization_dropdown.bind("<<ComboboxSelected>>", on_customization_selected)
customization_dropdown.pack()

# GPT Model Selection
gpt_model_label = tk.Label(main_frame, text="GPT Model:", font=("Segoe UI", 12))
gpt_model_label.pack(pady=(20, 0))
gpt_model_var = tk.StringVar()
gpt_model_var.set("GPT-3.5 (Default)")  # Default selection
gpt_model_dropdown = ttk.Combobox(
    main_frame,
    textvariable=gpt_model_var,
    values=["GPT-3.5 (Default)", "GPT-4"],
    font=("Segoe UI", 11),
    state="readonly",
    width=16,
)
gpt_model_dropdown.pack()

# Company entry
company_label = tk.Label(main_frame, text="Company name:", font=("Segoe UI", 12))
company_entry = tk.Entry(main_frame, width=16, font=("Segoe UI", 11))

# System prompt
system_prompt_frame = tk.Frame(main_frame)

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
    main_frame, width=55, height=3, font=("Segoe UI", 11), wrap=tk.WORD
)
system_prompt_entry.insert(
    tk.END,
    "Classify the sentiment of the following "
    "Text in one word from this list "
    "[Positive, Neutral, Negative].",
)

# User prompt
user_prompt_frame = tk.Frame(main_frame)

user_prompt_label = tk.Label(
    user_prompt_frame, text="User Prompt:", font=("Segoe UI", 12)
)
user_prompt_label.pack(side=tk.LEFT, padx=(5, 0))

user_prompt_entry_frame = tk.Frame(main_frame)

user_prompt_entry = tk.Entry(user_prompt_entry_frame, width=8, font=("Segoe UI", 11))
user_prompt_entry.insert(tk.END, "Text:")
user_prompt_entry.pack(side=tk.LEFT)
user_prompt_tweet_label = tk.Label(
    user_prompt_entry_frame, text=' "{Sample Text}"  Sentiment:', font=("Segoe UI", 11)
)
user_prompt_tweet_label.pack(side=tk.LEFT, padx=(5, 0))

# Run button
run_label = tk.Label(main_frame, text="")
run_label.pack(pady=(5, 0))
run_button = tk.Button(
    main_frame,
    text="Run Sentiment Analysis",
    font=("Segoe UI", 12),
    command=run_sentiment_analysis,
)
run_button.pack()

placeholder_frame = tk.Frame(main_frame, height=20, width=400)
placeholder_frame.pack(pady=10)
placeholder_frame.pack_propagate(False)

# Logging section
log_label = tk.Label(main_frame, text="Log Messages:", font=("Segoe UI", 12))
log_label.pack(pady=(0, 0))
log_text_area = scrolledtext.ScrolledText(
    main_frame, wrap=tk.WORD, width=55, height=8, font=("Segoe UI", 11)
)
log_text_area.configure(state="disabled")
log_text_area.pack(pady=(2, 5))

instructions_text = """1. Prepare and save your Excel file, with the text/tweets stored under a column titled "Full Text".
    - Note: If the file is saved to a cloud drive (e.g., OneDrive), close the file before running the tool.

2. Click on the "Browse" button under "Input File" and select the file containing the tweets.

3. Click on the "Browse" button next to "Output File" and choose a (local) location and new filename for the output Excel file.

4. (Optional) Select a customization option:
    - Default: Use the default system and user prompts.
    - Company: Specify a company name to analyze sentiment toward that company.
    - Custom: Provide custom system and user prompts

5. (Optional) Select a model (GPT 3.5 or 4).

6. Click "Run Sentiment Analysis".

7. When the script finishes (may take a few min), a success message will be displayed, and the output file will be saved to the specified location.

* Click reset to restore the default prompt.
** Change to match your system prompt. E.g., if your system prompt refers to the "Tweet" instead of "Text", change the user prompt to "Tweet:".
"""

instructions_label = tk.Label(
    instructions_frame, text="Instructions:", font=("Segoe UI", 12)
)
instructions_label.pack(fill="x")
instructions_text_area = scrolledtext.ScrolledText(
    instructions_frame, wrap=tk.WORD, width=60, height=30, font=("Segoe UI", 11)
)
instructions_text_area.insert(tk.END, instructions_text)
instructions_text_area.configure(state="disabled")
instructions_text_area.pack()


class Linkbutton(ttk.Button):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.font = tkFont.Font(family="Segoe UI", size=11)
        style = ttk.Style()
        style.configure("Link.TLabel", foreground="#357fde", font=self.font)
        self.configure(style="Link.TLabel", cursor="hand2")
        self.bind("<Enter>", self.on_mouse_enter)
        self.bind("<Leave>", self.on_mouse_leave)

    def on_mouse_enter(self, event):
        self.font.configure(underline=True)

    def on_mouse_leave(self, event):
        self.font.configure(underline=False)


docs_link = Linkbutton(
    instructions_frame,
    text="Full Documentation/Instructions",
    command=lambda: webbrowser.open(
        "https://docs.google.com/document/d/1R5qPnn5xbGOv3aZk6Cf5egfvrMVJ6TI2v_xg6FiFqp8/edit"
    ),
)
docs_link.pack(pady=(5, 2))

if darkdetect.isDark():
    sv_ttk.set_theme("dark")
    style = ttk.Style()
    style.map("Link.TLabel", foreground=[("active", "#357fde"), ("!active", "#357fde")])
else:
    sv_ttk.set_theme("light")
    style = ttk.Style()
    style.map("Link.TLabel", foreground=[("active", "#357fde"), ("!active", "#357fde")])

# Start the GUI event loop
window.mainloop()
