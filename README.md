# Sentiment Analysis Tool

## Overview

The Sentiment Analysis Tool is a GUI-based Python application that uses the OpenAI API to analyze the sentiment of text samples (e.g., tweets) stored in an Excel file. It has prompt customization options and integration with the Brandwatch API for updating sentiment and other metadata in BW.

## Table of Contents

- [Installation](#installation)
- [Basic Usage](#basic-usage)
  - [Setup](#setup)
  - [In the Sentiment Analysis Tool window](#in-the-sentiment-analysis-tool-window)
- [Documentation](#documentation)
  - [Prompt Customization](#prompt-customization)
    - [Default](#default)
    - [Company](#company)
    - [Multi-Company](#multi-company)
    - [Custom](#custom)
  - [Brandwatch Integration](#brandwatch-integration)
    - [For Brandwatch exports](#for-brandwatch-exports)
    - [Sentiment Tool BW Settings](#sentiment-tool-bw-settings)
  - [Model Selection](#model-selection)
  - [Rate Limits](#rate-limits)
    - [OpenAI API](#openai-api)
    - [Brandwatch API](#brandwatch-api)
  - [Features Coming Soon](#features-coming-soon)
- [Troubleshooting](#troubleshooting)
- [Changelog](#changelog)

## Installation

1. Clone the repository
2. Install the dependencies in `requirements.txt`
3. Run the app: `python main.py`

## Basic Usage

### Setup

- Ensure that the text samples are stored under a column named "Full Text" or “Content” in the file, which can be a .xlsx or .csv (or .zip containing a .csv)  
  - Brandwatch and Quorum exports will work without having to open the downloaded file first (the column headers can be in any of the first 20 rows)

### In the Sentiment Analysis Tool window

1. Click on the "Browse" button next to "Input File" and select your Excel file containing the text samples.  
   - Note: If the file is saved to a OneDrive folder, close it before running the tool.  
2. Click on the "Browse" button next to "Output File" and choose a location and identifiable filename for the output Excel file.  
3. (Optional): Update sentiment values in [Brandwatch](#brandwatch-integration) (will also mark updated mentions as "Checked"in BW).  
   - Note: Ensure input file contains the columns "Query Id" and "Resource Id" (included by default in BW exports).  
4. (Optional): Choose a [prompt customization](#prompt-customization) option ([Multi-Company](#multi-company) is the most versatile option)
5. (Optional): Choose a specific [model](#model-selection) to use  
6. Click on the "Run Sentiment Analysis" button to start the analysis process. When done, a success message will be displayed, and the output Excel file will be saved to the location you specified.  
   - The process could take anywhere from 5 sec to \>10 min depending on the sample size and length of the text inputs.

## Documentation

### Prompt Customization

#### Default

General sentiment analysis of the text samples

- Base System prompt: “Classify the sentiment of the following Text in one word from this list \[Positive, Neutral, Negative\].”  
- Base User prompt: “Text: "\[text sample\]" \\nSentiment:”

#### Company

Analyze sentiment toward a specific company

- Alters the system prompt to include "toward \[company\]" using the specified company name.  
- Can also be used to analyze sentiment toward a specific topic or trend (e.g., AI).

#### Multi-Company

Dynamically analyze sentiment toward multiple companies from 1 export

- Uses 1\) the **specified list of companies** to use and 2\) the **specified company column** (a brandwatch parent category, such as “Tech Companies”).  
  - Uses the order of the specified company list to determine which company to analyze sentiment toward if multiple companies are mentioned in a post.  
- If the *separate company coding* checkbox is enabled, for each post, it will code sentiment toward *every* (specified) company that is mentioned *separately*.  
  - If Brandwatch update is enabled, it will add a BW tag for each company mentioned in the format “\[Sentiment\] toward \[company\]”

#### Custom

Provide custom system and user prompts

- For accuracy, ensure the word used in the user prompt ("Text:" by default) is singular and matches the word used in the system prompt.  
- E.g., if your system prompt refers to the "...the Tweet.." instead of "...the Text...", change the user prompt to "Tweet:"

### Brandwatch Integration

Brandwatch exports do not need to be opened or altered after downloading before running the tool on that file.

#### For Brandwatch exports

- You likely want to ensure that you filter for posts where the “Checked” value under “Workflow” is “False” (to avoid exporting posts that have already been analyzed).
- For large exports (\~more than 5-10 thousand), I recommend using the “Data Download” option instead of manually exporting 5k at a time.  
  - When the data download is complete, you should choose the “csv” option when downloading the export, as they are much easier for the tool to process (especially when the export is large).  
  - Clicking the “csv” option will download a .zip file with a folder in it with the csv in it — you do *not* need to unzip it or extract the file, just choose the .zip as the input file

#### Sentiment Tool BW Settings

- **Update Sentiment Values**: Allows you to update sentiment values in Brandwatch for the specified mentions.  
  - Requires the input file to also contain the columns "Query Id" and "Resource Id".  
  - This setting will additionally mark the updated mentions as "Checked" in Brandwatch.  
- **Multi-Company (Tagging)**: When using Multi-Company mode AND optionally enabling *separate company analysis,* it will code sentiment toward each company mentioned in every post separately and add a tag for each company with the format “\[Sentiment\] toward \[company\]”
  - Requires the input file to also contain the columns "Query Id" and "Resource Id".  
  - Will still mark the updated mentions as "Checked" *and* update the standard sentiment values in BW based on the specified company list order.

### Model Selection

- **GPT-3.5 (legacy)**: Least accurate but far less neutral than the others
  - More of a gut-level vibe-based analysis, less likely to be neutral on e.g. news headlines hinting at something negative about a company.
  - *Mostly used in order to have consistency (if previous report waves used it).*  
- **GPT-4o mini:** Cheapest and great for large batches of mentions with shorter text samples.  
- **GPT-4o**: Most accurate. Best for smaller sample sizes and longer bodies of text (like Reddit posts or Press Releases from Quorum).  
  - GPT-4o and GPT-4o mini tend to be more neutral, especially if data includes lots of news headlines etc., which can be good or bad depending on the desired results.

### Rate Limits

#### OpenAI API

- The tool will calculate the token counts of each text sample and then process the tweets/samples in batches based on input tokens and the following API rate limits (waiting for **30** seconds between each batch):  
  - 10,000 requests (posts/samples) per minute for all models  
  - 10,000,000 tokens per minute for GPT-3.5-turbo  
  - 10,000,000 tokens per minute for GPT-4o-mini  
  - 2,000,000 tokens per minute for GPT-4o

#### Brandwatch API

- Sentiment values will be sent to Brandwatch in batches of 1361, and the tool will pause for up to 10 minutes if it hits a rate limit  
  - 30 API calls per 10 minutes  
  - 1361 mentions per batch/call

### Features Coming Soon

- [x] ~~Support for Quorum exports (without having to open the file and change column names)~~  
- [x] ~~Automatic per-company sentiment analysis based on a company column and ordered list~~  
      - [x] ~~Option to use mutually exclusive BW tags for each company mentioned and its corresponding sentiment instead of single sentiment values per mention (sentiment analyzed toward each company mentioned in each post separately)~~  
- [ ] Advanced options
      - [x] Temperature, max token limit, top p  
      - [ ] Custom prompts for multi-company analysis  
      - [ ] Non-sentiment category classification  
- [ ] Fine-tuned GPT-4o-mini model on hand coded sentiment data?

## Troubleshooting

## Changelog

[Changelog](https://github.com/mmstroik/sentiment_analysis/blob/master/changelog.md)
