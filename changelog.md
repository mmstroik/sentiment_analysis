# Changelog
### 2024-09-04
* 09:18 PM EST - fix IndexError when reading new BW xlsx files by adding <cellStyleXfs> to styles.xml
* 09:06 PM EST - add logging for async api calls
* 09:06 PM EST - wrap main function in thread in a try except block

### 2024-09-03
* 01:45 AM EST - add tooltip and update instructions
* 01:05 AM EST - update instruction

### 2024-09-02
* 10:43 PM EST - add progress bar updates to bw upload
* 04:18 PM EST - add support for zip files with csvs (for BW data downloads)
* 03:19 PM EST - add default input file type that shows both xlsx and csvs
* 02:15 PM EST - Fix bugs and improve error handling in file operations and config

### 2024-08-31
* 01:32 AM EST - refactor. including dataclass for input variables and file_operations module

### 2024-08-30
* 07:53 PM EST - add cursorignore
* 07:53 PM EST - removing build folder from being tracked

### 2024-08-10
* 12:49 AM EST - allow <|endoftext special token

### 2024-08-08
* 05:04 PM EST - fix addTags bug

### 2024-08-07
* 01:40 PM EST - save file before brandwatch upload
* 01:40 PM EST - fix csv header finding bug

### 2024-08-06
* 07:04 PM EST - update csv support and logging, update bw upload only functions
* 01:03 AM EST - preliminary csv support

### 2024-08-01
* 09:17 PM EST - update instructions and 4o-mini is default
* 07:49 PM EST - add multi-company support for input file format from BW 'Data Download' files

### 2024-07-30
* 07:16 PM EST - fix addTags issue on mentions with no company

### 2024-07-24
* 06:20 PM EST - spacing in customization buttons (stripped when sent as arg)
* 06:05 PM EST - fix no default model selected
* 03:22 AM EST - dynamic tokenizer choice
* 12:30 AM EST - update rate limits and remove gpt 4 turbo

### 2024-07-22
* 02:33 AM EST - temp to 0.3
* 01:21 AM EST - new model and rate limits

### 2024-07-21
* 11:30 PM EST - fix big where non-multi-company modes don't work due to non-defaulted company argument in api call function

### 2024-07-18
* 01:02 AM EST - reorganize main into class and functions

### 2024-07-17
* 09:30 PM EST - refactor and keep original index when merging
* 08:57 PM EST - fix same index for duplicate company rows causing same sentiment tag for all companies in a mention

### 2024-07-16
* 11:44 PM EST - analysis (and BW tagging) for each company in each mention works
* 09:02 PM EST - small messagebox change
* 04:14 PM EST - adjust enable button timer
* 03:13 PM EST - gui and button enable timer adjustement
* 11:30 AM EST - adjust GUI
* 11:28 AM EST - fix missing parameters and add prompt placeholder and alter token calculation. tested. works.
* 02:35 AM EST - pre-test implementation

### 2024-07-15
* 09:44 PM EST - rate limit timer to 30 sec

### 2024-07-12
* 10:10 PM EST - add try except clause to each api call attempt to set errors as "Error" for reprocessing
* 10:31 AM EST - fix quorum ("Content") column support
* 10:14 AM EST - Merge branch 'master' of https://github.com/mmstroik/sentiment_analysis
* 10:14 AM EST - adding user prompt 2 (text before response) customization

### 2024-07-08
* 08:04 PM EST - update rate limits (level 4)

### 2024-06-17
* 01:17 PM EST - fix incorrect check for full text row

### 2024-06-15
* 02:04 PM EST - fix no full text column error not working and add support for 'Content' column header

### 2024-06-10
* 10:06 PM EST - fix blank cell freeze

### 2024-06-06
* 05:58 PM EST - adjusted post button timer

### 2024-05-20
* 07:39 PM EST - gui adjustments

### 2024-05-19
* 03:53 PM EST - progbar padding
* 02:30 PM EST - fix typo
* 02:18 PM EST - improve file processing and column checks

### 2024-05-18
* 04:35 PM EST - trigger check_file_exists from input entry changes
* 04:02 PM EST - adjust instructions box height

### 2024-05-17
* 02:06 AM EST - Merge branch 'notebook'
* 02:04 AM EST - fix log prob column indexing

### 2024-05-14
* 09:02 AM EST - resdesign compress

### 2024-05-13
* 08:37 PM EST - add gpt-4o support
* 08:02 PM EST - Merge branch 'master' of https://github.com/mmstroik/sentiment_analysis
* 08:00 PM EST - tab name

### 2024-05-12
* 03:13 PM EST - feat: bw upload-only support as notebook tab
* 03:09 PM EST - chore: add openpyxl dependency to requirements.txt

### 2024-05-11
* 12:35 PM EST - chore: update pandas dependency to version 2.2.2
* 12:33 PM EST - add ttkbootstrap to -r
* 12:33 PM EST - update requirements.txt

### 2024-05-10
* 05:30 PM EST - testing notebook for bw-only switching
* 10:19 AM EST - move asyncio timer to after gather function in core logic

### 2024-05-09
* 09:55 PM EST - asyncio timer starts after gather function
* 09:55 PM EST - update instruction
* 01:44 PM EST - add exception for invalid output file path/format

### 2024-05-08
* 07:10 PM EST - instructions

### 2024-05-07
* 07:20 PM EST - Merge branch 'redesign'
* 07:16 PM EST - button resize
* 12:39 PM EST - new quad design

### 2024-05-06
* 02:22 AM EST - input file doesnt exist exception

### 2024-05-05
* 11:14 PM EST - unfinished redisigning
* 08:36 PM EST - fix lack of else: condition for logprobs_bool in threading function
* 12:39 AM EST - add probabilities column in output (if checkbox is true)

### 2024-05-04
* 06:51 PM EST - add file overwrite warning message
* 06:49 PM EST - remaining time for button re-enable starts within async loops

### 2024-05-03
* 11:03 PM EST - post processing rate timer
* 11:00 AM EST - ignore spec
* 11:00 AM EST - ignore spec
* 10:55 AM EST - modified:   .gitignore

### 2024-05-02
* 09:31 PM EST - deleted:    dist/Sentiment-Analysis.exe
* 11:15 AM EST - remove icon from gitignore
* 11:13 AM EST - add retry limits and efficient header detection
* 12:25 AM EST - format
* 12:08 AM EST - add retries for transient BW errors

### 2024-05-01
* 11:52 PM EST - update instructions panel

### 2024-04-30
* 09:19 PM EST - ignore temp tkinter files
* 09:04 PM EST - replace column finding with for loop
* 07:19 PM EST - formatting
* 10:30 AM EST - support for headers in rows 9-13
* 03:03 AM EST - toc update
* 02:27 AM EST - Merge pull request #5 from mmstroik/refactor-modules
* 02:27 AM EST - Merge branch 'master' into refactor-modules
* 02:19 AM EST - ignore html md
* 02:18 AM EST - modified:   dist/Sentiment-Analysis.exe
* 02:17 AM EST - finalized refactoring and fixes

### 2024-04-29
* 11:21 PM EST - fix another .get redundancy
* 11:13 PM EST - fix redundant .get usage that was freezing program
* 09:47 AM EST - spec to ignore
* 12:11 AM EST - put build and dist in gitignore for now
* 12:09 AM EST - bs to gitignore
* 12:07 AM EST - new instructions

### 2024-04-28
* 11:33 PM EST - refactor connectors and module to src/
* 08:16 PM EST - update log messages and instrucitons
* 02:01 PM EST - Merge pull request #4 from mmstroik:row10-dyanamictokenizer
* 01:58 PM EST - Merge remote-tracking branch 'origin/master' into row10-dyanamictokenizer
* 12:21 PM EST - fixed token_buffer arg problem in .exe
* 12:19 PM EST - commiting cleaned (master) .exe in order to switch
* 12:18 PM EST - removed token_buffer args
* 12:11 PM EST - cleaning .exe as baseline for bug fixing
* 12:04 PM EST - upgraded libraries
* 11:56 AM EST - read columns in row 10 if not in row 1, calculate exact system and user prompt tokens
* 03:17 AM EST - cleaning .exe
* 03:15 AM EST - Merge branch 'master' of https://github.com/mmstroik/sentiment_analysis
* 03:08 AM EST - Merge pull request #2 from mmstroik/large_bw_api_requests
* 03:06 AM EST - Adjusting other files accordingly
* 03:04 AM EST - Fix BW api errors (added batching). BW updating also sets checked = true

### 2024-04-27
* 05:56 PM EST - unknown (to stash)
* 05:51 PM EST - better logging

### 2024-04-26
* 03:14 AM EST - Merge pull request #1 from mmstroik/bw_integration
* 03:10 AM EST - works with api now

### 2024-04-25
* 07:24 PM EST - BW integration test1

### 2024-04-18
* 10:29 PM EST - moved prog bar up
* 09:26 PM EST - updated rate limits
* 09:25 PM EST - Updated rate limits

### 2024-04-15
* 11:46 PM EST - new api key
* 11:06 PM EST - new api key

### 2024-04-11
* 01:14 PM EST - new file:   requirements.txt

### 2024-04-08
* 06:36 PM EST - .exe uses milo's api key for now
* 06:33 PM EST - using Milo's api key for now

### 2024-04-07
* 08:29 PM EST - modified:   main.py
* 06:02 PM EST - Update README.md
* 05:52 PM EST - modified:   async_core_logic.py 	modified:   main.py
* 05:46 PM EST - refactoring
* 04:48 PM EST - Error reprocessing includes blank sentiment cells as well as "Error" now
* 12:21 PM EST - refactored core logic for modularity
* 10:31 AM EST - Update README.md
* 10:29 AM EST - Updated executable with refactor and error handling fixes
* 10:08 AM EST - new file:   .gitignore 	modified:   README.md
* 09:55 AM EST - Refactor core logic into seperate module
* 09:53 AM EST - modified:   async_core_logic.py 	modified:   main.py
* 09:53 AM EST - modified:   main.py
* 09:51 AM EST - renamed:    core/async_core_logic.py -> async_core_logic.py 	renamed:    SentimentAnalysisMain.py -> main.py
* 09:41 AM EST - deleted:    async_core_logic.py
* 09:40 AM EST - new file:   core/async_core_logic.py 	deleted:    async_core_logic.py
* 09:37 AM EST - new file:   async_core_logic.py
* 09:13 AM EST - modified:   SentimentAnalysisMain.py
* 09:05 AM EST - modified:   SentimentAnalysisMain.py

### 2024-04-06
* 04:40 PM EST - Update README.md
* 04:39 PM EST - Update README.md
* 04:37 PM EST - Update README.md
* 04:32 PM EST - Update README.md
* 01:22 PM EST - Update README.md
* 01:20 PM EST - Update README.md
* 01:06 PM EST - modified:   SentimentAnalysisMain.py

### 2024-04-01
* 07:16 PM EST - modified:   SentimentAnalysisMain.py

### 2024-03-31
* 09:18 PM EST - sentiment_analysis
