import asyncio
import threading
import os
import pandas as pd
from tkinter import messagebox
import time

from src.async_core_logic import process_tweets_in_batches
from src.bw_api_handling import update_bw_sentiment
from src.multi_company_analysis import process_multi_company, merge_separate_company_results, create_company_column


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
    if output_file_extension != ".xlsx" and output_file_extension != ".csv":
        log_message("Output file must be a .xlsx or .csv file.")
        messagebox.showerror("Error", "Output file must be a .xlsx or .csv file.")
        return
    if not os.path.exists(input_file):
        log_message(f"Error: The file '{os.path.basename(input_file)}' does not exist.")
        messagebox.showerror(
            "Error",
            f"The file '{os.path.basename(input_file)}' does not exist.",
        )
        return
    input_file_extension = os.path.splitext(input_file)[1]

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

    file_extension = os.path.splitext(input_file)[1].lower()

    if file_extension == '.csv':
        df = read_csv_file(input_file, log_message)
    elif file_extension in ['.xlsx', '.xls']:
        df = read_excel_file(input_file, log_message)
    else:
        error_message = "Input file must be a .xlsx or .csv."
        log_message("Error: " + error_message)
        messagebox.showerror("Error", error_message)
        enable_button()
        return

    if df is None:
        error_message = "The input file does not contain the required column 'Full Text' or 'Content'."
        log_message("Error: " + error_message)
        messagebox.showerror("Error", error_message)
        enable_button()
        return

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
            log_message(f"Column '{company_column}' not found. Checking for alternative format...")
            company_mentions = create_company_column(df, company_column, multi_company_entry)
            if company_mentions is None:
                error_message = f"Neither the specified company column '{company_column}' nor the alternative format columns were found in the input file."
                log_message(error_message)
                messagebox.showerror("Error", error_message)
                enable_button()
                return
            df[company_column] = company_mentions
            log_message(f"Created '{company_column}' column from alternative format.")

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
    
    output_file_extension = os.path.splitext(output_file)[1]
    log_message(f"Saving results to a {output_file_extension}...")
    df.drop(columns=["Token Count"], inplace=True)
    if output_file_extension == '.csv':
        df.to_csv(output_file, index=False)
    else:
        df.to_excel(output_file, index=False)
    log_message(f"Sentiment analysis results saved to {output_file}.")
    
    if bw_checkbox_var:
        log_message(f"-------\nUpdating sentiment values in Brandwatch...")
        update_bw_sentiment(df, log_message)
        
    update_progress_gui(100)
    log_message("Sentiment analysis completed successfully.")
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


def read_csv_file(input_file, log_message):
    # Read the first 20 rows to check for metadata
    with open(input_file, 'r', encoding='utf-8') as f:
        first_20_lines = [next(f) for _ in range(20)]

    # Find the header row
    header_row = None
    for i, line in enumerate(first_20_lines):
        if "Full Text" in line or "Content" in line:
            header_row = i
            break
    if header_row is None:
        return None

    log_message(f"Found header row at line {header_row + 1}")

    # Read the CSV file, skipping rows above the header
    log_message(f"Reading the full csv..")
    df = pd.read_csv(input_file, skiprows=header_row)


    return df

def read_excel_file(input_file, log_message):
    # Read the first 20 rows
    df = pd.read_excel(input_file, header=None, nrows=20)

    # Check for 'Full Text' or 'Content' in first 20 rows
    if "Full Text" in df.iloc[:20].values:
        full_text_row = df.iloc[:20].isin(["Full Text"]).any(axis=1).idxmax()
        log_message("'Full Text' column found. Processing the full xlsx...")
    elif "Content" in df.iloc[:20].values:
        full_text_row = df.iloc[:20].isin(["Content"]).any(axis=1).idxmax()
        log_message("'Content' column found. Processing the full xlsx...")
    else:
        return None

    # read the full file, skipping rows above the column names
    df = pd.read_excel(input_file, header=full_text_row)

    return df

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

    log_message(f"Reading file: '{os.path.basename(input_file)}'...")

    file_extension = os.path.splitext(input_file)[1].lower()

    if file_extension == '.csv':
        df = read_csv_file(input_file, log_message)
    elif file_extension in ['.xlsx', '.xls']:
        df = read_excel_file(input_file, log_message)
    else:
        error_message = "Input file must be a .xlsx or .csv file."
        log_message("Error: " + error_message)
        messagebox.showerror("Error", error_message)
        enable_button()
        return

    if df is None:
        error_message = "The input file does not contain the required column 'Full Text'."
        log_message("Error: " + error_message)
        messagebox.showerror("Error", error_message)
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
    update_bw_sentiment(df, log_message)
    update_progress_gui(98)
    update_progress_gui(100)
    messagebox.showinfo("Success", "Brandwatch upload completed successfully.")
    enable_button()
    return
