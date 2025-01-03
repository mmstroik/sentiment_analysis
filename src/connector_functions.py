import asyncio
import threading
import os
import pandas as pd
from tkinter import messagebox
import time
import copy
import traceback

from .input_config import SentimentAnalysisConfig
from . import (
    async_core_logic,
    file_operations,
    bw_api_handling,
    multi_company_analysis,
)


def handle_error(log_message, enable_button, message: str):
    log_message(f"Error: {message}")
    print(f"\nError Details:\n{traceback.format_exc()}")
    messagebox.showerror("Error", message)
    enable_button()

def setup_sentiment_analysis(
    config: SentimentAnalysisConfig,
    update_progress_gui,
    log_message,
    enable_button,
    disable_button,
):
    try:
        config.output_file = file_operations.check_file_paths(config.input_file, config.output_file)
    except ValueError as e:
        handle_error(log_message, enable_button, str(e))
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
        handle_error(log_message, enable_button, str(e))


def run_sentiment_analysis_thread(
    config: SentimentAnalysisConfig,
    update_progress_gui,
    log_message,
    enable_button,
):
    try:
        log_message(
            f"-------\nReading file: '{os.path.basename(config.input_file)}'..."
        )

        try:
            df = file_operations.read_file(config.input_file, log_message)
        except ValueError as e:
            raise ValueError(f"Error reading file: {str(e)}")

        if "Content" in df.columns and "Full Text" not in df.columns:
            df.rename(columns={"Content": "Full Text"}, inplace=True)

        if config.update_brandwatch:
            if "Query Id" not in df.columns or "Resource Id" not in df.columns:
                error_message = "The input file does not contain the required BW columns 'Query Id' or 'Resource Id'."
                handle_error(log_message, enable_button, error_message)
                return

        if "Sentiment" not in df.columns:
            df["Sentiment"] = ""

        if config.output_probabilities:
            if "Probs" not in df.columns:
                df["Probs"] = ""
            cols = df.columns.tolist()
            sentiment_index = cols.index("Sentiment")
            cols = (
                cols[: sentiment_index + 1] + ["Probs"] + cols[sentiment_index + 1 : -1]
            )
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
                handle_error(log_message, enable_button, str(e))
                return
            if df is None:  # User chose not to proceed
                log_message("Analysis cancelled by user.")
                enable_button()
                return

        if config.use_dual_models:
            df, start_time = run_dual_model_analysis(
                config, df, update_progress_gui, log_message
            )
        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            df, start_time = loop.run_until_complete(
                async_core_logic.batch_processing_handler(
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

        sentiment_counts = df["Sentiment"].value_counts()
        log_message("Sentiment Distribution for output file:")
        for sentiment in ["Positive", "Neutral", "Negative"]:
            count = sentiment_counts.get(sentiment, 0)
            percentage = (count / len(df)) * 100
            log_message(f"{sentiment}: {count} ({percentage:.1f}%)")

        file_operations.write_file(df, config.output_file, log_message)

        if config.update_brandwatch:
            log_message(f"-------\nUpdating sentiment values in Brandwatch...")
            bw_api_handling.update_bw_sentiment(df, update_progress_gui, log_message)
            log_message("Brandwatch upload completed.")

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
        handle_error(log_message, enable_button, str(e))
        return


def run_dual_model_analysis(
    config: SentimentAnalysisConfig,
    df: pd.DataFrame,
    update_progress_gui,
    log_message,
):
    log_message(
        f"Starting dual model analysis with {config.model_display_name} ({config.model_split_percentage}%) and {config.second_model_display_name} ({100-config.model_split_percentage}%)..."
    )
    # Calculate split point
    total_rows = len(df)
    split_index = int(total_rows * (config.model_split_percentage / 100))

    # Randomly shuffle DataFrame and split
    shuffled_df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    df1 = shuffled_df.iloc[:split_index].copy()
    df2 = shuffled_df.iloc[split_index:].copy()

    # Create configs for each model
    config1 = copy.deepcopy(config)
    config2 = copy.deepcopy(config)
    config2.prepare_second_model()
    
    first_model_weight = config.model_split_percentage / 100

    # Process each portion
    log_message(f"Processing {len(df1)} mentions with {config.model_name}...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    df1, start_time1 = loop.run_until_complete(
        async_core_logic.batch_processing_handler(
            config1,
            df1,
            lambda x: update_progress_gui(x * first_model_weight),
            log_message,
        )
    )
    loop.close()
        
    log_message(f"Processing {len(df2)} mentions with {config2.model_name}...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    df2, start_time2 = loop.run_until_complete(
        async_core_logic.batch_processing_handler(
            config2,
            df2,
            lambda x: update_progress_gui(60 * first_model_weight + x * (1 - first_model_weight)),
            log_message,
        )
    )
    loop.close()

    # Merge results back together
    result_df = pd.concat([df1, df2])
    # Restore original order
    result_df = result_df.reindex(df.index)

    return result_df, start_time2
