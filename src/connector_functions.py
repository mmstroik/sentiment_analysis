import asyncio
import threading
import os
import pandas as pd
from tkinter import messagebox
import time

from src.async_core_logic import process_tweets_in_batches
from src.bw_api_handling import update_bw_sentiment
from src.multi_company_analysis import process_multi_company, merge_separate_company_results


"""GUI <-> CORE LOGIC CONNECTOR FUNCTIONS"""


# Set the token and requests limits based on model selection
def select_model(gpt_model):
    model_limits = {
        "gpt-3.5-turbo": {"token_limit": 5000000, "requests_limit": 5000},
        "gpt-4o": {"token_limit": 1000000, "requests_limit": 5000},
        "gpt-4o-mini": {"token_limit": 5000000, "requests_limit": 5000},
    }
    model_mapping = {
        " GPT-3.5 ": "gpt-3.5-turbo",
        " GPT-4o mini ": "gpt-4o-mini",
        " GPT-4o ": "gpt-4o",
    }
    model = model_mapping[gpt_model]
    return (
        model,
        model_limits[model]["token_limit"],
        model_limits[model]["requests_limit"],
    )


# Set the system and user prompts based on the customization option selected
def set_prompts(
    customization_option,
    company_entry,
    system_prompt_entry,
    user_prompt_entry,
    user_prompt_entry2,
):
    if customization_option == "Default":
        system_prompt = "Classify the sentiment of the following Text in one word from this list [Positive, Neutral, Negative]."
        user_prompt = "Text:"
        user_prompt2 = "Sentiment:"
    elif customization_option == "Company":
        company = company_entry
        system_prompt = f"Classify the sentiment of the following Text toward {company} in one word from this list [Positive, Neutral, Negative]."
        user_prompt = "Text:"
        user_prompt2 = "Sentiment:"
    elif customization_option == "Multi-Company":
        # Placeholder for company name (uses .format to replace bracketed text via string matching)
        system_prompt = "Classify the sentiment of the following Text{toward_company} in one word from this list [Positive, Neutral, Negative]."
        user_prompt = "Text:"
        user_prompt2 = "Sentiment:"
    elif customization_option == "Custom":
        system_prompt = system_prompt_entry.strip()
        user_prompt = user_prompt_entry.strip()
        user_prompt2 = user_prompt_entry2.strip()
    return system_prompt, user_prompt, user_prompt2


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
    user_prompt_entry2,
    gpt_model,
    bw_checkbox_var,
    logprob_checkbox_var,
    company_column=None,
    multi_company_entry=None,
    separate_company_analysis=False,
):
    if not input_file or not output_file:
        messagebox.showerror(
            "Error", "Please provide both input and output file paths."
        )
        return
    output_file_extension = os.path.splitext(output_file)[1]
    if output_file_extension != ".xlsx":
        log_message("Output file must be a .xlsx file.")
        messagebox.showerror("Error", "Output file must be a .xlsx file.")
        return
    if not os.path.exists(input_file):
        log_message(f"Error: The file '{os.path.basename(input_file)}' does not exist.")
        messagebox.showerror(
            "Error",
            f"The file '{os.path.basename(input_file)}' does not exist.",
        )
        return
    input_file_extension = os.path.splitext(input_file)[1]
    if input_file_extension != ".xlsx":
        log_message("Input file must be a .xlsx file.")
        messagebox.showerror("Error", "Input file must be a .xlsx file.")
        return

    model, batch_token_limit, batch_requests_limit = select_model(gpt_model)
    system_prompt, user_prompt, user_prompt2 = set_prompts(
        customization_option,
        company_entry,
        system_prompt_entry,
        user_prompt_entry,
        user_prompt_entry2,
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
                user_prompt2,
                model,
                batch_token_limit,
                batch_requests_limit,
                bw_checkbox_var,
                logprob_checkbox_var,
                customization_option,
                company_column,
                multi_company_entry,
                separate_company_analysis,
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
    user_prompt2,
    model,
    batch_token_limit,
    batch_requests_limit,
    bw_checkbox_var,
    logprob_checkbox_var,
    customization_option,
    company_column,
    multi_company_entry,
    separate_company_analysis,
):
    log_message(f"-------\nReading file: '{os.path.basename(input_file)}'...")
    # Read the first 20 rows
    df = pd.read_excel(input_file, header=None, nrows=20)

    # Check for 'Full Text' or 'Content' in first 20 rows
    if "Full Text" in df.iloc[:20].values:
        full_text_row = df.iloc[:20].isin(["Full Text"]).any(axis=1).idxmax()
        log_message("'Full Text' column found. Processing the full file...")
    elif "Content" in df.iloc[:20].values:
        full_text_row = df.iloc[:20].isin(["Content"]).any(axis=1).idxmax()
        log_message("'Content' column found. Processing the full file...")
    else:
        log_message(
            "Error: The input file does not contain the required column 'Full Text' or 'Content'."
        )
        messagebox.showerror(
            "Error",
            "The input file does not contain the required column 'Full Text' or 'Content'.",
        )
        enable_button()
        return

    # read the full file, skipping rows above the column names
    df = pd.read_excel(input_file, header=full_text_row)

    if "Content" in df.columns and "Full Text" not in df.columns:
        df.rename(columns={"Content": "Full Text"}, inplace=True)

    if bw_checkbox_var:
        if "Query Id" not in df.columns or "Resource Id" not in df.columns:
            error_message = "The input file does not contain the required BW columns 'Query Id' or 'Resource Id'."
            log_message("Error: " + error_message)
            messagebox.showerror("Error", error_message)
            enable_button()
            return

    if "Sentiment" not in df.columns:
        df["Sentiment"] = ""

    if logprob_checkbox_var:
        probs_bool = True
        if "Probs" not in df.columns:
            df["Probs"] = ""
        cols = df.columns.tolist()
        sentiment_index = cols.index("Sentiment")
        cols = cols[: sentiment_index + 1] + ["Probs"] + cols[sentiment_index + 1 : -1]
        df = df[cols]
    else:
        probs_bool = False

    if customization_option == "Multi-Company":
        if not multi_company_entry:
            error_message = "No companies were specified for multi-company analysis."
            log_message("Error: " + error_message)
            messagebox.showerror("Error", error_message)
            enable_button()
            return
        if not company_column:
            error_message = "No company column was specified for multi-company analysis."
            log_message("Error: " + error_message)
            messagebox.showerror("Error", error_message)
            enable_button()
            return
        if company_column not in df.columns:
            error_message = f"The specified company column name '{company_column}' does not exist in the input file."
            log_message(error_message)
            messagebox.showerror("Error", error_message)
            enable_button()
            return

        df = process_multi_company(df, company_column, multi_company_entry, log_message, separate_company_analysis)
        if df is None:  # User chose not to proceed
            log_message("Analysis cancelled by user.")
            enable_button()
            return

    log_message(f"Starting sentiment analysis with {model}...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    df, start_time = loop.run_until_complete(
        process_tweets_in_batches(
            df,
            update_progress_gui,
            log_message,
            system_prompt,
            user_prompt,
            user_prompt2,
            model,
            probs_bool,
            batch_token_limit,
            batch_requests_limit,
            customization_option,
        )
    )
    loop.close()
    
    if customization_option == "Multi-Company" and separate_company_analysis:
        df = merge_separate_company_results(df, bw_checkbox_var)

    if bw_checkbox_var:
        log_message(f"-------\nUpdating sentiment values in Brandwatch...")
        update_bw_sentiment(df, log_message)

    log_message(f"Saving results to excel...")
    df.drop(columns=["Token Count"], inplace=True)
    update_progress_gui(98)

    df.to_excel(output_file, index=False)
    update_progress_gui(100)
    log_message(f"Sentiment analysis results saved to {output_file}.")
    messagebox.showinfo("Success", "Sentiment analysis completed successfully.")

    elapsed_time = time.time() - start_time
    remaining_time = max(30 - elapsed_time, 0)  
    if remaining_time > 0:
        log_message(
            f"Waiting {int(remaining_time)} more seconds before enabling the Run button..."
        )
        time.sleep(remaining_time)
        log_message("Cooldown complete, Run button enabled.")

    enable_button()
    return


"""BRANDWATCH UPLOAD-ONLY CONNECTOR FUNCTIONS"""


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
                disable_button,
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
    disable_button,
):

    log_message(f"Reading file: '{os.path.basename(input_file)}'...")

    df = pd.read_excel(input_file, header=None)

    full_text_row = (
        df.iloc[:20]
        .apply(lambda row: row.astype(str).str.contains("Full Text").any(), axis=1)
        .idxmax()
    )

    if full_text_row is None:
        log_message(
            "Error: The input file does not contain the required column 'Full Text'."
        )
        messagebox.showerror(
            "Error",
            "The input file does not contain the required column 'Full Text'.",
        )
        enable_button()
        return

    # Drop the rows above the 'Full Text' row and set the 'Full Text' row as the header
    df.columns = df.iloc[full_text_row]
    df = df.iloc[(full_text_row + 1) :].reset_index(drop=True)

    log_message("'Full Text' column found.")

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
    update_bw_sentiment(df, log_message)
    update_progress_gui(98)
    update_progress_gui(100)
    messagebox.showinfo("Success", "Brandwatch upload completed successfully.")
    enable_button()
    return
