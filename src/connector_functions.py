import asyncio
import threading
import os
import pandas as pd
from tkinter import messagebox

from src.async_core_logic import process_tweets_in_batches
from src.bw_api_handling import update_bw_sentiment



"""GUI <-> CORE LOGIC CONNECTOR FUNCTIONS"""


# Set the token and requests limits based on model selection
def select_model(gpt_model):
    model_limits = {
        "gpt-3.5-turbo": {"token_limit": 160000, "requests_limit": 5000},
        "gpt-4-turbo": {"token_limit": 600000, "requests_limit": 5000},
    }
    model = "gpt-3.5-turbo" if gpt_model == "GPT-3.5 (Default)" else "gpt-4-turbo"
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
        company = company_entry
        system_prompt = f"Classify the sentiment of the following Text toward {company} in one word from this list [Positive, Neutral, Negative]."
        user_prompt = "Text:"
    elif customization_option == "Custom":
        system_prompt = system_prompt_entry.strip()
        user_prompt = user_prompt_entry
    return system_prompt, user_prompt



def setup_sentiment_analysis(
    input_file,
    output_file,
    update_progress_gui,
    log_message,
    enable_button,
    disable_button,
    customization_option,
    company_entry,
    system_prompt_entry,
    user_prompt_entry,
    gpt_model,
    bw_checkbox_var,
):
    if not input_file or not output_file:
        messagebox.showerror(
            "Error", "Please provide both input and output file paths."
        )
        return
    model, batch_token_limit, batch_requests_limit = select_model(gpt_model)
    system_prompt, user_prompt = set_prompts(
        customization_option, company_entry, system_prompt_entry, user_prompt_entry
    )

    disable_button()
    try:
        thread = threading.Thread(
            target=run_sentiment_analysis_thread,
            args=(
                input_file,
                output_file,
                update_progress_gui,
                log_message,
                enable_button,
                system_prompt,
                user_prompt,
                model,
                batch_token_limit,
                batch_requests_limit,
                bw_checkbox_var,
            ),
        )
        thread.start()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        enable_button()


# Handle file reading and writing and call the core logic in a separate thread
def run_sentiment_analysis_thread(
    input_file,
    output_file,
    update_progress_gui,
    log_message,
    enable_button,
    system_prompt,
    user_prompt,
    model,
    batch_token_limit,
    batch_requests_limit,
    bw_checkbox_var,
):
    log_message(f"Reading file: '{os.path.basename(input_file)}'.")

    df = pd.read_excel(input_file)
    if "Full Text" not in df.columns:
        df = pd.read_excel(input_file, skiprows=8)
    if "Full Text" not in df.columns:
        df = pd.read_excel(input_file, skiprows=9)
    if "Full Text" not in df.columns:
        df = pd.read_excel(input_file, skiprows=10)
    if "Full Text" not in df.columns:
        df = pd.read_excel(input_file, skiprows=11)
    if "Full Text" not in df.columns:
        df = pd.read_excel(input_file, skiprows=12)

    if "Full Text" not in df.columns:
        log_message("Error: The input file does not contain the required column 'Full Text'.")
        messagebox.showerror(
            "Error",
            "The input file does not contain the required column 'Full Text'.",
        )
        enable_button()
        return

    log_message("'Full Text' column found.")

    if bw_checkbox_var:
        if "Query Id" not in df.columns or "Resource Id" not in df.columns:
            messagebox.showerror(
                "Error",
                "The input file does not contain the required BW columns 'Query Id' or 'Resource Id'.",
            )
            enable_button()
            return

    if "Sentiment" not in df.columns:
        df["Sentiment"] = ""

    log_message(f"Starting sentiment analysis with {model}...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    df = loop.run_until_complete(
        process_tweets_in_batches(
            df,
            update_progress_gui,
            log_message,
            system_prompt,
            user_prompt,
            model,
            batch_token_limit,
            batch_requests_limit,
        )
    )
    loop.close()

    if bw_checkbox_var:
        log_message(f"Updating sentiment values in Brandwatch...")
        update_bw_sentiment(df, log_message)

    log_message(f"Saving results to excel...")
    df.drop(columns=["Token Count"], inplace=True)
    update_progress_gui(98)
    df.to_excel(output_file, index=False)
    update_progress_gui(100)
    log_message(f"Sentiment analysis results saved to {output_file}.")
    messagebox.showinfo("Success", "Sentiment analysis completed successfully.")
    enable_button()
    return