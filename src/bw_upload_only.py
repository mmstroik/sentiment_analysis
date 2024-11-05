import threading
import os
import pandas as pd
from tkinter import messagebox

from src import file_operations, bw_api_handling


def create_bw_upload_thread(
    input_file, update_progress_gui, log_message, enable_button, disable_button
):
    disable_button()
    try:
        thread = threading.Thread(
            target=setup_bw_upload,
            args=(
                input_file,
                update_progress_gui,
                log_message,
                enable_button,
            ),
        )
        thread.start()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        enable_button()


def setup_bw_upload(
    input_file,
    update_progress_gui,
    log_message,
    enable_button,
):
    try:
        log_message(f"-------\nReading file: '{os.path.basename(input_file)}'...")

        try:
            df = file_operations.read_file(input_file, log_message)
        except ValueError as e:
            log_message(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
            enable_button()
            return

        if "Query Id" not in df.columns or "Resource Id" not in df.columns:
            messagebox.showerror(
                "Error",
                "The input file does not contain the required BW columns 'Query Id' or 'Resource Id'.",
            )
            enable_button()
            return

        if "Sentiment" not in df.columns:
            messagebox.showerror(
                "Error",
                "The input file does not contain a Sentiment column.",
            )
            enable_button()
            return

        log_message(f"Updating sentiment values in Brandwatch...")
        bw_api_handling.update_bw_sentiment(df, update_progress_gui, log_message)
        update_progress_gui(98)
        update_progress_gui(100)
        messagebox.showinfo("Success", "Brandwatch upload completed successfully.")
        enable_button()
        return
    except Exception as e:
        error_message = f"{str(e)}"
        log_message(f"Error: {error_message}")
        messagebox.showerror("Error", f"Error: {error_message}")
        enable_button()
        return
