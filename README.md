# Quadrant Digital Sentiment Analysis Tool
## Usage
1. Download/copy the `Sentiment-Analysis.exe` file from the 'App' folder to a local folder on your computer (like Desktop). You can pin the app to your taskbar for convenience.
2. Double-click on the saved `Sentiment-Analysis.exe` file to launch the tool.
3. Prepare your Excel file containing the tweets/text you want to analyze. Ensure that the tweets/text are stored under a column named "Full Text". If you don't have an Excel file ready, you can create a new one with a column named "Full Text" and copy and paste your tweets into that column.
   - You may find it helpful to use the same input file each time and just copy and paste new tweets into the file for analysis.
4. In the Sentiment Analysis Tool window:
   1. Click on the "Browse" button next to "Input File" and select your Excel file containing the tweets.
   2. Click on the "Browse" button next to "Output File" and choose a location and filename for the output Excel file that will contain the sentiment analysis results.
      - Note: Choose a unique (and identifiable) name because the tool will overwrite any existing file with the same name (or produce an error).
   3. (Optional): Choose a customization option
      - Default: Use the default system and user prompts.
      - Company: Specify a company name to analyze sentiment toward that company.
      - Custom: Provide custom *system and **user prompts
   4. (Optional): Choose a specific model to use
      - GPT-3.5 is the default model and is cheap and good for large batches of tweets.
      - GPT-4 is good for smaller sample sizes and large bodies of text (like Press Releases from Quorum) but is 20x more expensive.
   5. Click on the "Run Sentiment Analysis" button to start the analysis process.
5. The tool will calculate batch sizes based on the input tokens per tweet/text and the per-minute API rate limits. It will then process and classify the text in batches, waiting for ~60 seconds between each batch, so it may take a few minutes.
6. Once the analysis is complete, a success message will be displayed, and the output Excel file will be saved to the location you specified.

_*Click reset to restore the default prompt._
_**Change to match your system prompt. E.g., if your system prompt refers to the "Tweet" instead of "Text", change the user prompt to "Tweet:"_
## Troubleshooting
- If you encounter an error message, please ensure that:
  - Your input Excel file is properly formatted with a column named "Full Text" containing the tweets.
  - You have provided valid file paths for both the input and output files.
  - Your input file and output file path are in a location where the tool has read and write permissions.
    - I.e., not the shared Onedrive folder.
  - You have a stable internet connection, as the tool requires access to the OpenAI API.
- Contact Milo for any issues or questions.
