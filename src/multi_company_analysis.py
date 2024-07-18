import pandas as pd
from tkinter import messagebox


def process_multi_company(df, company_column, multi_company_entry, log_message, separate_company_analysis=False):
    company_list = [company.strip() for company in multi_company_entry.split(",") if company.strip()]

    # Check if all priority companies are present in the dataset
    companies_in_data = set()
    for companies in df[company_column].dropna():
        companies_in_data.update(company.strip() for company in companies.split(','))
    
    missing_companies = [company for company in company_list if company not in companies_in_data]
    
    if missing_companies:
        missing_companies_str = ', '.join(missing_companies)
        message = f"The following companies from your priority list were not found in the dataset:\n\n{missing_companies_str}\n\nDo you want to proceed anyway?"
        proceed = messagebox.askyesno("Companies Not Found", message)
        if not proceed:
            return None

    # Always create the AnalyzedCompany column
    df["AnalyzedCompany"] = ""

    if not separate_company_analysis:
        log_message("Creating multi-company designations based on specified order...")
        # Existing logic for single analysis per mention
        total_analyzed = 0
        for priority_company in company_list:
            mask = (df["AnalyzedCompany"] == "") & (
                df[company_column].apply(
                    lambda x: (
                        priority_company in {company.strip() for company in x.split(",")}
                        if pd.notna(x)
                        else False
                    )
                )
            )
            company_count = mask.sum()
            df.loc[mask, "AnalyzedCompany"] = priority_company
            total_analyzed += company_count
            log_message(f"{company_count} mentions will be analyzed towards {priority_company}")

        unanalyzed_count = len(df) - total_analyzed
        log_message(f"{unanalyzed_count} mentions will be analyzed without a specific company focus.")
    else:
        initial_row_count = len(df)
        expanded_df = []
        
        for original_index, row in df.iterrows():
            companies = set(company.strip() for company in row[company_column].split(',')) if pd.notna(row[company_column]) else set()
            relevant_companies = [company for company in company_list if company in companies]
            
            if relevant_companies:
                row['AnalyzedCompany'] = relevant_companies[0]
                row['OriginalIndex'] = original_index  # Add original index
                expanded_df.append(row)
                for company in relevant_companies[1:]:
                    new_row = row.copy()
                    new_row['AnalyzedCompany'] = company
                    new_row['OriginalIndex'] = original_index
                    expanded_df.append(new_row)
            else:
                row['OriginalIndex'] = original_index  # Add original index
                expanded_df.append(row)
        
        df = pd.DataFrame(expanded_df)
        df.reset_index(drop=True, inplace=True)  # Reset the index to ensure unique indices
        log_message(f"Expanded dataset from {initial_row_count} to {len(df)} rows for separate company analysis.")
        
        # Count mentions per company
        company_counts = df['AnalyzedCompany'].value_counts()
        for company, count in company_counts.items():
            if company:
                log_message(f"{count} mentions will be analyzed towards {company}")
        unanalyzed_count = company_counts.get('', 0)
        log_message(f"{unanalyzed_count} mentions will be analyzed without a specific company focus.")

    return df


def merge_separate_company_results(df, bw_upload=False):
    grouped = df.groupby('OriginalIndex')
    
    merged_rows = []
    for _, group in grouped:
        merged_row = group.iloc[0].copy()  # Take the first row as the base

        primary_sentiment = merged_row['Sentiment']
        primary_company = merged_row['AnalyzedCompany']
        
        if bw_upload:
            # Create tags for Brandwatch upload
            tags = [f"{row['Sentiment']} toward {row['AnalyzedCompany']}" for _, row in group.iterrows() if row['AnalyzedCompany']]
            merged_row['BW_Tags'] = ','.join(tags)
        else:
            # Create a combined sentiment column
            sentiments = [f"{row['Sentiment']} toward {row['AnalyzedCompany']}" for _, row in group.iterrows() if row['AnalyzedCompany']]
            merged_row['Combined_Sentiment'] = ' | '.join(sentiments)
        
        merged_row['Sentiment'] = primary_sentiment
        merged_row['AnalyzedCompany'] = primary_company
        merged_rows.append(merged_row)
    
    result_df = pd.DataFrame(merged_rows)
    result_df.set_index('OriginalIndex', inplace=True)  # Set OriginalIndex as the index
    result_df.sort_index(inplace=True)  # Sort by the original index
    return result_df