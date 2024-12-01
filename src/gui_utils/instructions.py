import tkinter as tk
import tkinter.font as tkFont
import webbrowser

from functools import partial

from . import tkmd

def create_instructions(frame):
    
    instructions_font = tkFont.nametofont("TkDefaultFont")
    instructions_font.configure(size=12)
    instructions_label = tk.Label(
        frame, text="Instructions:", font=("Segoe UI", 12)
    )
    instructions_label.pack(fill="x")

    instructions_text_area = tkmd.SimpleMarkdownText(
        frame,
        wrap=tk.WORD,
        padding=0,
        bootstyle="round",
        autohide=True,
        width=55,
        height=33,
        font=instructions_font,
    )
    instructions_text_area.pack(fill=tk.BOTH, expand=True)

    instructions_text = """1. Ensure your input file is a .xlsx or .csv (or .zip containing a .csv) with a "Content" or "Full Text" column (default for BW).
* Note: Works with column headers in any of the first 20 rows (BW exports).

2. Click on the "Browse" button next to "Input File" and select the file containing the mentions.
* Note: If the file is saved to OneDrive/SharePoint, close it before running the tool.

3. Click on the "Browse" button next to "Output File" and create a new filename for the output.

4. (Optional): Update sentiment values in Brandwatch (will also mark updated mentions as "Checked" in BW).
* Requires 'Query Id' and 'Resource Id' columns in input file

5. (Optional) Select a customization option:
* Default: Use the default system and user prompts.
* Company: Specify a single company name.
* Multi-Company: Specify Brandwatch company categories
* Custom: Provide custom system and user prompts

6. (Optional) Select a model:
* GPT-3.5 (Legacy): Less accurate but much less neutral
* GPT-4o mini: Best for larger batches and/or shorter text.
* GPT-4o: Best for smaller batches and/or long text.
        
7. Click "Run Sentiment Analysis. A success message will be displayed when finished.
"""
    instructions_text_area.insert_markdown(instructions_text)

    hyperlink = tkmd.HyperlinkManager(instructions_text_area)
    instructions_text_area.insert(
        "end",
        "Full Documentation/Instructions",
        hyperlink.add(
            partial(
                webbrowser.open,
                "https://docs.google.com/document/d/1R5qPnn5xbGOv3aZk6Cf5egfvrMVJ6TI2v_xg6FiFqp8/edit",
            )
        ),
    )
    instructions_text_area.text.configure(state="disabled")