# Sentiment Analysis Tool Changelog

## 2025

### 2025-01-03

* Merge branch 'core-logic-refactor'
* add newlines
* init refactor
* commit submodule commit (from key merge)
* Merge branch 'gemini'
* commit new submodule hash
* add deepseek tokenizer support
* adjust and consolidate gui to have "Other" model dropdown including deepseekv3
* add: log sentiment values for entire df at the end

## 2024


### 2024-12-15

* delete gemini md docs
* add gemini models to gui and config. also, alter model display name variable names and add spacer for advanced options frame width
* fix lack of await for async calculate tokens call and incorrect token counting endpoint
* add token counting buffer (+2) for gemini
* add token counting logic for gemini using api
* add if else to call correct api based on model name
* stash gemini changes (token counting, config, and gui updates still needed)

### 2024-12-12

* change submodule import
* fix: change submodule name to avoid numpy conflict
* fix: for zip inputs, temp dir cleanup wasn't working due to extracted csv being in a nested dir
* fix: due to the per-request progress bar updating feature, implemented by replacing asyncio.gather with as_completed, sentiment values were getting assigned to rows based on the order they complete, causing random sentiment assignment. the fix creates a mapping between futures and their original indicies and uses asyncio.wait instead of as_completed

### 2024-12-11

* fix inconsistent temp file cleanup
* add azure secrets (wrong branch but whatev)

### 2024-12-07

* Merge branch 'category-templates'

### 2024-12-05

* add error handling for adding tag to mention that already has tag with the same name

### 2024-12-04

* Add TCP connection settings and timeouts to prevent semaphore errors in BW API calls
* add no extension or path in output file support for gui overwrite warning label functionality

### 2024-12-03

* edit gui: Advanced Options label is now a button that toggles the advanced frame. changed spacer height in advanced frame to be more dynamic and accurate based on notebook padding and labelframe text height offset
* output file name defaults to input file path if no path and .csv if no extension

### 2024-12-01

* update gui: convert advanced options notebook to labelframe, add theme selector in advanced frame, add titlebar color adjustement based on theme, center on screen based on max frame size, convert scrollbar text frames to ttk and use custom scrollbar hiding, refactor modules to src/gui_utils

### 2024-11-27

* update gui, including advanced options collapsing frame

### 2024-11-25

* add per request progress bar updating with asyncio as_completed and scale progress depending on if update_brandwatch is enabled
* improved progress bar percentage calculations
* fix response time logging discrepency for bw api requests. remove semaphor. improve error handling
* add reset button for advanced options vars
* feat: add dual model advanced option with split % input. + gui updates (advanced options are a notebook now)
* add error handling function
* update gui

### 2024-11-21

* update changelog

### 2024-11-12

* add openpyxl to requirements (independent import needed for pyinstaller)
* add better logging for partial api call failures
* fix bug preventing retries on partial failures in bw api call chunks

### 2024-11-11

* center advanced frame content vertically
* format
* add max completion token slider
* fix lack of advanced_frame instatiation
* fix naming conflicts
* change max_tokens to max_completion_tokens due to deprecation
* merge master into advanced-frame-simple
* update gui padding
* add try except block for api response logging
* update secrets submodule
* move icon to themes
* add cursorrules to .gitignore
* remove cursorrules and update readme and changelog
* add asynchronous calls to BW API
* convert imports from absolute to relative
* import api keys from secrets
* update requirements.txt and config files
* add portable custom themes
* add secrets submodule
* update cursorrules

### 2024-11-07

* refactor bw logger into metrics module
* fix metrics path and lack of button disabling
* add better BW api logging and metrics analysis button
* improve Brandwatch debug logging
* add BW API debug logging
* Add temp file cleanup for ZIP extraction and update gitignore
* change csv to default output
* fix: handle company column names containing dashes in multi-company analysis

### 2024-11-05

* fix: better error handling and logging for BW uploading

### 2024-11-03

* fix: add missing update_progress_gui param to BW upload function

### 2024-10-29

* add message warning about BW Upload Only button

### 2024-09-23

* update docs

### 2024-09-04

* update instructions
* remove timestamps
* add changelog
* fix IndexError when reading new BW xlsx files by adding <cellStyleXfs> to styles.xml
* add logging for async api calls
* wrap main function in thread in a try except block

### 2024-09-03

* add tooltip and update instructions
* update instruction

### 2024-09-02

* add progress bar updates to bw upload
* add support for zip files with csvs (for BW data downloads)
* add default input file type that shows both xlsx and csvs
* Fix bugs and improve error handling in file operations and config

### 2024-08-31

* refactor. including dataclass for input variables and file_operations module

### 2024-08-30

* add cursorignore

### 2024-08-10

* allow <|endoftext special token

### 2024-08-08

* fix addTags bug

### 2024-08-07

* save file before brandwatch upload
* fix csv header finding bug

### 2024-08-06

* update csv support and logging, update bw upload only functions
* preliminary csv support

### 2024-08-01

* update instructions and 4o-mini is default
* add multi-company support for input file format from BW 'Data Download' files

### 2024-07-30

* fix addTags issue on mentions with no company

### 2024-07-24

* spacing in customization buttons (stripped when sent as arg)
* fix no default model selected
* dynamic tokenizer choice
* update rate limits and remove gpt 4 turbo

### 2024-07-22

* temp to 0.3
* new model and rate limits

### 2024-07-21

* fix big where non-multi-company modes don't work due to non-defaulted company argument in api call function

### 2024-07-18

* reorganize main into class and functions

### 2024-07-17

* refactor and keep original index when merging
* fix same index for duplicate company rows causing same sentiment tag for all companies in a mention

### 2024-07-16

* analysis (and BW tagging) for each company in each mention works
* small messagebox change
* adjust enable button timer
* gui and button enable timer adjustement
* adjust GUI
* fix missing parameters and add prompt placeholder and alter token calculation. tested. works.
* pre-test implementation

### 2024-07-15

* rate limit timer to 30 sec

### 2024-07-12

* add try except clause to each api call attempt to set errors as "Error" for reprocessing
* fix quorum ("Content") column support
* Merge branch 'master' of https://github.com/mmstroik/sentiment_analysis
* adding user prompt 2 (text before response) customization

### 2024-07-08

* update rate limits (level 4)

### 2024-06-17

* fix incorrect check for full text row

### 2024-06-15

* fix no full text column error not working and add support for 'Content' column header

### 2024-06-10

* fix blank cell freeze

### 2024-06-06

* adjusted post button timer

### 2024-05-20

* gui adjustments

### 2024-05-19

* progbar padding
* fix typo
* improve file processing and column checks

### 2024-05-18

* trigger check_file_exists from input entry changes
* adjust instructions box height

### 2024-05-17

* Merge branch 'notebook'
* fix log prob column indexing

### 2024-05-14

* resdesign compress

### 2024-05-13

* add gpt-4o support
* Merge branch 'master' of https://github.com/mmstroik/sentiment_analysis
* tab name

### 2024-05-12

* feat: bw upload-only support as notebook tab
* chore: add openpyxl dependency to requirements.txt

### 2024-05-11

* chore: update pandas dependency to version 2.2.2
* add ttkbootstrap to -r
* update requirements.txt

### 2024-05-10

* testing notebook for bw-only switching
* move asyncio timer to after gather function in core logic

### 2024-05-09

* asyncio timer starts after gather function
* update instruction
* add exception for invalid output file path/format

### 2024-05-08

* instructions

### 2024-05-07

* Merge branch 'redesign'
* button resize
* new quad design

### 2024-05-06

* input file doesnt exist exception

### 2024-05-05

* unfinished redisigning
* fix lack of else: condition for logprobs_bool in threading function
* add probabilities column in output (if checkbox is true)

### 2024-05-04

* add file overwrite warning message
* remaining time for button re-enable starts within async loops

### 2024-05-03

* post processing rate timer
* ignore spec
* modified:   .gitignore

### 2024-05-02

* remove icon from gitignore
* add retry limits and efficient header detection
* format
* add retries for transient BW errors

### 2024-05-01

* update instructions panel

### 2024-04-30

* ignore temp tkinter files
* replace column finding with for loop
* formatting
* support for headers in rows 9-13
* toc update
* Merge pull request #5 from mmstroik/refactor-modules
* Merge branch 'master' into refactor-modules
* ignore html md
* finalized refactoring and fixes

### 2024-04-29

* fix another .get redundancy
* fix redundant .get usage that was freezing program
* spec to ignore
* put build and dist in gitignore for now
* bs to gitignore
* new instructions

### 2024-04-28

* refactor connectors and module to src/
* update log messages and instrucitons
* Merge pull request #4 from mmstroik:row10-dyanamictokenizer
* Merge remote-tracking branch 'origin/master' into row10-dyanamictokenizer
* removed token_buffer args
* cleaning .exe as baseline for bug fixing
* upgraded libraries
* read columns in row 10 if not in row 1, calculate exact system and user prompt tokens
* Merge pull request #2 from mmstroik/large_bw_api_requests
* Adjusting other files accordingly
* Fix BW api errors (added batching). BW updating also sets checked = true

### 2024-04-27

* better logging

### 2024-04-26

* Merge pull request #1 from mmstroik/bw_integration
* works with api now

### 2024-04-25

* BW integration test1

### 2024-04-18

* moved prog bar up
* updated rate limits
* Updated rate limits

### 2024-04-15

* new api key

### 2024-04-11

* new file:   requirements.txt

### 2024-04-08

* using Milo's api key for now

### 2024-04-07

* modified:   main.py
* Update README.md
* modified:   async_core_logic.py 	modified:   main.py
* refactoring
* Error reprocessing includes blank sentiment cells as well as "Error" now
* refactored core logic for modularity
* Update README.md
* new file:   .gitignore 	modified:   README.md
* Refactor core logic into seperate module
* modified:   async_core_logic.py 	modified:   main.py
* modified:   main.py
* renamed:    core/async_core_logic.py -> async_core_logic.py 	renamed:    SentimentAnalysisMain.py -> main.py
* deleted:    async_core_logic.py
* new file:   core/async_core_logic.py 	deleted:    async_core_logic.py
* new file:   async_core_logic.py
* modified:   SentimentAnalysisMain.py

### 2024-04-06

* Update README.md
* modified:   SentimentAnalysisMain.py

### 2024-04-01

* modified:   SentimentAnalysisMain.py

### 2024-03-31

* sentiment_analysis
