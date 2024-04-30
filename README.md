# Sentiment Analysis Tool

## Overview

The Sentiment Analysis Tool is a GUI-based Python application that uses the OpenAI API to analyze the sentiment of text samples (e.g., tweets) stored in an Excel file. It has prompt customization options and integration with the Brandwatch API for updating BW metadata.

## Table of Contents

- [Basic Usage](#basic-usage)
  - [Setup](#setup)
  - [In the Sentiment Analysis Tool window](#in-the-sentiment-analysis-tool-window)
- [Documentation](#documentation)
  - [Prompt Customization](#prompt-customization)
  - [Model Selection](#model-selection)
  - [Brandwatch Integration](#brandwatch-integration)
- [Troubleshooting](#troubleshooting)

## Basic Usage

### Setup

- Go to `Quadrant Digital Team - Documents/General/SentimentAnalysis/App/` via your file explorer* and double click the `Sentiment-Analysis-Tool` file to launch the tool.
  - *The tool cannot be launched directly from the SharePoint website or Office 365. It can only be launched from SharePoint using your file explorer (via [synced](https://support.microsoft.com/en-us/office/sync-sharepoint-files-and-folders-87a96948-4dd7-43e4-aca1-53f3e18bea9b) library or folder [shortcut](https://support.microsoft.com/en-us/office/add-shortcuts-to-shared-folders-in-onedrive-for-work-or-school-d66b1347-99b7-4470-9360-ffc048d35a33)).
- Ensure that the text samples are stored under a column named "Full Text" in the Excel file.
  - The column names can be 10th row (Brandwatch exports), and the file can contain additional columns
  - If you are using the Brandwatch integration, ensure the file has "Query Id" and "Resource Id" columns.

### In the Sentiment Analysis Tool window

1. Click on the "Browse" button next to "Input File" and select your Excel file containing the text samples.
   - Note: If the file is saved to a OneDrive folder, close it before running the tool.
2. Click on the "Browse" button next to "Output File" and choose a location and identifiable filename for the output Excel file containing the results (and all existing columns from the input file).
3. (Optional): Update sentiment values in Brandwatch (will also mark updated mentions as "Checked"in BW).
    - Note: Ensure input file contains the columns "Query Id" and "Resource Id".
4. (Optional): Choose a customization option
   - Default: Use the default system and user prompts.
   - Company: Specify a company name to analyze sentiment toward that company.
   - Custom: Provide custom *system and **user prompts
5. (Optional): Choose a specific model to use
   - GPT-3.5 is the default model and is cheap and good for large batches of tweets.
   - GPT-4 is good for smaller sample sizes and large bodies of text (like Press Releases from Quorum) but is 20x more expensive.
6. Click on the "Run Sentiment Analysis" button to start the analysis process.
7. Once the analysis is complete, a success message will be displayed, and the output Excel file will be saved to the location you specified.
   - The tool will process the tweets/samples in batches based on input tokens and the API rate limits. It waits for ~60 seconds between each batch, so it could take anywhere from 5 sec to >10 min depending on the sample size and length of the text inputs.

## Documentation

### Prompt Customization

- **Default**: General sentiment analysis of the text samples.
  - System prompt: 'Classify the sentiment of the following Text in one word from this list [Positive, Neutral, Negative].'
  - User prompt: 'Text: "[text sample]" \nSentiment:'
- **Company**: Analyze sentiment toward a specific company.
  - Alters the system prompt to include "toward [company]" using the specified company name.
  - Can also be used to analyze sentiment toward a specific topic or trend (e.g., AI).
- **Custom**: Provide custom system and user prompts.
  - For accuracy, ensure the word used in the user prompt ("Text:" by default) is singular and matches the word used in the system prompt.
    - E.g., if your system prompt refers to the "...the Tweet.." instead of "...the Text...", change the user prompt to "Tweet:"

### Model Selection

- **GPT-3.5** (Default): Cheap and good for large batches of mentions with shorter, less complex text samples.
- **GPT-4**: Best for smaller sample sizes and longer bodies of text (like Reddit posts or Press Releases from Quorum).

### Brandwatch Integration

- **Update Sentiment Values**: Allows you to update sentiment values in Brandwatch for the specified mentions.
  - Requires the input file to contain the columns "Query Id" and "Resource Id".
  - This setting will additionally mark the updated mentions as "Checked" in Brandwatch.

## Troubleshooting

If you encounter a "file permissions" error message:

- If your input file is saved to a folder in your Onedrive (or another cloud drive), ensure that you close the excel window after saving (so that it syncs to the cloud).

If you encounter a different error message, ensure that:

- Your input Excel file is properly formatted with a column named "Full Text" containing the tweets.
- You have provided valid file paths for both the input and output files.
- You have a stable internet connection, as the tool requires access to the OpenAI API.

Contact Milo for any other issues or questions.
