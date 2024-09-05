import asyncio
import threading
import os
import pandas as pd
from tkinter import messagebox
import time

from src.input_config import SentimentAnalysisConfig
from src import (
    async_core_logic,
    file_operations,
    bw_api_handling,
    multi_company_analysis,
)


def setup_sentiment_analysis(
    config: SentimentAnalysisConfig,
    update_progress_gui,
    log_message,
    enable_button,
    disable_button,
):
    try:
        file_operations.check_file_paths(config.input_file, config.output_file)
    except ValueError as e:
        log_message(f"Error: {str(e)}")
        messagebox.showerror("Error", str(e))
        enable_button()
        return

    disable_button()
    try:
        thread = threading.Thread(
            target=run_sentiment_analysis_thread,
            args=(
                config,
                update_progress_gui,
                log_message,
                enable_button,
            ),
        )
        thread.start()
    except Exception as e:
        log_message(f"An error occurred: {str(e)}")
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        enable_button()


def run_sentiment_analysis_thread(
    config: SentimentAnalysisConfig,
    update_progress_gui,
    log_message,
    enable_button,
):
    try:
        log_message(f"-------\nReading file: '{os.path.basename(config.input_file)}'...")

        try:
            df = file_operations.read_file(config.input_file, log_message)
        except ValueError as e:
            raise ValueError(f"Error reading file: {str(e)}")

        if "Content" in df.columns and "Full Text" not in df.columns:
            df.rename(columns={"Content": "Full Text"}, inplace=True)

        if config.update_brandwatch:
            if "Query Id" not in df.columns or "Resource Id" not in df.columns:
                error_message = "The input file does not contain the required BW columns 'Query Id' or 'Resource Id'."
                log_message("Error: " + error_message)
                messagebox.showerror("Error", error_message)
                enable_button()
                return

        if "Sentiment" not in df.columns:
            df["Sentiment"] = ""

        if config.output_probabilities:
            if "Probs" not in df.columns:
                df["Probs"] = ""
            cols = df.columns.tolist()
            sentiment_index = cols.index("Sentiment")
            cols = cols[: sentiment_index + 1] + ["Probs"] + cols[sentiment_index + 1 : -1]
            df = df[cols]

        if config.customization_option == "Multi-Company":
            try:
                df = multi_company_analysis.setup_multi_company(
                    df, config.company_column, config.multi_company_entry, log_message
                )
                df = multi_company_analysis.process_multi_company(
                    df,
                    config.company_column,
                    config.multi_company_entry,
                    log_message,
                    config.separate_company_analysis,
                )
            except ValueError as e:
                log_message(f"Error: {str(e)}")
                messagebox.showerror("Error", str(e))
                enable_button()
                return
            if df is None:  # User chose not to proceed
                log_message("Analysis cancelled by user.")
                enable_button()
                return

        log_message(f"Starting sentiment analysis with {config.model_name}...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        df, start_time = loop.run_until_complete(
            async_core_logic.process_tweets_in_batches(
                config,
                df,
                update_progress_gui,
                log_message,
            )
        )
        loop.close()

        if (
            config.customization_option == "Multi-Company"
            and config.separate_company_analysis
        ):
            df = multi_company_analysis.merge_separate_company_results(
                df, config.update_brandwatch
            )
            log_message(
                f"Merged expanded seperate company results back into {len(df)} mentions."
            )

        file_operations.write_file(df, config.output_file, log_message)

        if config.update_brandwatch:
            log_message(f"-------\nUpdating sentiment values in Brandwatch...")
            bw_api_handling.update_bw_sentiment(df, update_progress_gui, log_message)

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

    except Exception as e:
        error_message = f"{str(e)}"
        log_message(f"Error: {error_message}")
        messagebox.showerror("Error", f"Error: {error_message}")
        enable_button()
        return
