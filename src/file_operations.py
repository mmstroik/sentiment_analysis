import os
import pandas as pd
from io import BytesIO
import zipfile


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
    if file_extension == ".zip":
        extracted_file = extract_zip_file(input_file, log_message)
        try:
            df = read_csv_file(extracted_file, log_message)
        finally:
            # Clean up the temporary directory
            temp_dir = os.path.dirname(extracted_file)
            if os.path.exists(extracted_file):
                os.remove(extracted_file)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            log_message("Cleaned up temporary extraction files")
        return df
    elif file_extension == ".csv":
        return read_csv_file(input_file, log_message)
    elif file_extension in [".xlsx", ".xls"]:
        return read_excel_file(input_file, log_message)
    else:
        raise ValueError("Input file must be a .xlsx, .csv, or .zip file.")


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
    try:
        # Try reading the first 20 rows
        df = pd.read_excel(input_file, header=None, nrows=20)
    except IndexError:
        log_message("IndexError encountered. Attempting to modify styles.xml...")
        modified_file = modify_styles_xml(input_file)
        log_message("Modified styles.xml. Attempting to read again...")
        try:
            df = pd.read_excel(modified_file, header=None, nrows=20)
        except Exception as e:
            log_message(f"Error even after modifying styles.xml: {str(e)}")
            raise
    else:
        modified_file = input_file

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

    df = pd.read_excel(modified_file, header=full_text_row)

    return df


def modify_styles_xml(excel_file):
    with zipfile.ZipFile(excel_file, 'r') as zip_ref:
        styles_content = zip_ref.read('xl/styles.xml')
    
    styles_str = styles_content.decode('utf-8')
    if '<cellStyleXfs' not in styles_str:
        insert_pos = styles_str.index('<cellXfs')
        cellStyleXfs = '''<cellStyleXfs count="1">
        <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
    </cellStyleXfs>
    '''
        modified_styles = styles_str[:insert_pos] + cellStyleXfs + styles_str[insert_pos:]
        
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as new_zip:
            for item in zipfile.ZipFile(excel_file, 'r').infolist():
                if item.filename == 'xl/styles.xml':
                    new_zip.writestr(item, modified_styles)
                else:
                    new_zip.writestr(item, zipfile.ZipFile(excel_file, 'r').read(item.filename))
        
        buffer.seek(0)
        return buffer
    return excel_file


def extract_zip_file(zip_path, log_message):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Get the name of the first file in the zip
        file_list = zip_ref.namelist()
        if not file_list:
            raise ValueError("The zip file is empty.")
        
        csv_files = [f for f in file_list if f.lower().endswith('.csv')]
        if not csv_files:
            raise ValueError("No CSV file found in the zip archive.")
        
        csv_file = csv_files[0]
        log_message(f"Extracting {csv_file} from zip archive...")
        
        # Extract to a temporary directory
        temp_dir = os.path.join(os.path.dirname(zip_path), "temp_extracted")
        os.makedirs(temp_dir, exist_ok=True)
        extracted_path = zip_ref.extract(csv_file, temp_dir)
        
        return extracted_path


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
