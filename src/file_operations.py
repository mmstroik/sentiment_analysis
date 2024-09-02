import os
import pandas as pd


def check_file_paths(input_file, output_file):
    if not input_file or not output_file:
        raise ValueError("Please provide both input and output file paths.")
    if not os.path.exists(input_file):
        raise ValueError(f"The file '{os.path.basename(input_file)}' does not exist.")
    output_file_extension = os.path.splitext(output_file)[1]
    if output_file_extension not in [".xlsx", ".csv"]:
        raise ValueError("Output file must be a .xlsx or .csv file.")


def read_file(input_file, log_message):
    file_extension = os.path.splitext(input_file)[1].lower()
    if file_extension == ".csv":
        return read_csv_file(input_file, log_message)
    elif file_extension in [".xlsx", ".xls"]:
        return read_excel_file(input_file, log_message)
    else:
        raise ValueError("Input file must be a .xlsx or .csv.")


def read_csv_file(input_file, log_message):
    # Read the first 20 rows to check for metadata
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            first_20_lines = [next(f) for _ in range(20)]
    except StopIteration:
        raise ValueError("The csv file is empty or has less than 20 lines.")

    # Find the header row
    header_row = None
    for i, line in enumerate(first_20_lines):
        if "Full Text" in line or "Content" in line:
            header_row = i
            break
    if header_row is None:
        raise ValueError(
            "The input file does not contain the required column 'Full Text' or 'Content'."
        )

    log_message(f"Found header row at line {header_row + 1}")

    # Read the CSV file, skipping rows above the header
    log_message(f"Processing the full csv...")
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
        raise ValueError(
            "The input file does not contain the required column 'Full Text' or 'Content'."
        )

    # read the full file, skipping rows above the column names
    df = pd.read_excel(input_file, header=full_text_row)

    return df


def write_file(df, output_file, log_message):
    output_file_extension = os.path.splitext(output_file)[1].lower()
    log_message(f"Saving results to a {output_file_extension}...")
    if "Token Count" in df.columns:
        df.drop(columns=["Token Count"], inplace=True)
    if output_file_extension == ".csv":
        df.to_csv(output_file, index=False)
    elif output_file_extension in [".xlsx", ".xls"]:
        df.to_excel(output_file, index=False)
    else:
        raise ValueError("Output file must be a .xlsx or .csv.")
    log_message(f"Results saved to {output_file}.")
