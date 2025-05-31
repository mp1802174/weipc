This project is applying for free VPS resource support from ZMTO.COM, thank you.

**Project Name:** WeChatOA_Aggregation
**Main Technology Stack:** Python
**Main Libraries:** DrissionPage, lxml, requests, tqdm, datasketch, Pillow

## File Analysis Details

### Root Directory (woa/)

**requirements.txt**
- **Main Function/Purpose:** Lists the Python libraries and their versions required for the project to run.
- **Key Components:**
  - DrissionPage: Used for web automation and data extraction.
  - lxml: Used for XML and HTML parsing.
  - requests: Used for sending HTTP requests.
  - tqdm: Used for displaying progress bars.
  - datasketch: Used for MinHash LSH algorithm for text deduplication.
- **Main Dependencies:** No internal project dependencies.

**main.py**
- **Main Function/Purpose:** The main entry script of the project, responsible for coordinating the entire article crawling, deduplication, and Markdown generation workflow.
- **Key Components:**
  - Loads WeChat official account information and crawled article information from name2fakeid.json and message_info.json.
  - Iterates through the configured official account list (name2fakeid_dict).
  - If an official account is newly added, retrieves its fakeid.
  - Checks if updates are needed for that official account's articles (based on last crawl time).
  - Calls WechatRequest.fakeid2message_update() to update article list.
  - Updates message_info.json.
  - Calls minHashLSH.write_vector() for article deduplication.
  - Calls message2md() and single_message2md() to generate Markdown files.
- **Main Dependencies:** tqdm, request_.wechat_request.WechatRequest, util.message2md.message2md, util.message2md.single_message2md, util.util.handle_json, util.filter_duplication.minHashLSH.

**README.md**
- **Main Function/Purpose:** Provides basic project introduction, feature list (TODO), environment configuration instructions (token/cookie acquisition), MinHash experiment records, and references to similar projects.
- **Key Components:** Project overview, feature highlights, usage guide.
- **Main Dependencies:** None.

**daily_update.sh**
- **Main Function/Purpose:** Shell script for periodically executing crawler tasks, likely for automated daily updates.
- **Key Components:** Script commands (specific content not reviewed, but typically includes commands to execute main.py).
- **Main Dependencies:** Depends on correct execution of main.py.

### util/ Directory

**util.py**
- **Main Function/Purpose:** Contains common utility functions for the project.
- **Key Components:**
  - headers: Defines common HTTP request headers.
  - message_is_delete(): Checks if a WeChat article has been deleted by the publisher.
  - update_message_info(): Self-check function that updates message_info.json file, removing deleted articles.
  - handle_json(): Encapsulates JSON file reading and safe writing operations (using temporary files to avoid data loss from write interruptions).
  - check_text_ratio(): Detects the ratio of English text and symbols in text.
- **Main Dependencies:** pathlib, shutil, tqdm, json, requests, lxml.etree.

**filter_duplication.py**
- **Main Function/Purpose:** Implements article deduplication logic, primarily using MinHash LSH algorithm.
- **Key Components:**
  - url2text(): Extracts main text content from given URLs, attempts to handle different HTML structures and process deleted or request error cases.
  - calc_duplicate_rate1(): Calculates duplicate word ratio between two text lists.
  - calc_duplicate_rate_max(): Combines calc_duplicate_rate1 and sentence_bleu to calculate maximum duplication rate.
  - get_filtered_message(): (Appears to be early version or auxiliary function) Performs preliminary filtering based on title similarity and content duplication rate calculation.
  - generate_title_head(): (Appears to be early version or auxiliary function) Generates statistics based on article titles.
  - UpstashVector (class): (Deprecated) A class that attempted to use Upstash Vector DB for vector similarity search deduplication.
  - minHashLSH (class): Core deduplication class.
    - __init__(): Initializes MinHashLSH object, loads processed article IDs and MinHash signature cache.
    - write_vector(): Iterates through articles, generates MinHash signatures for new articles, queries LSH index to find similar articles, and determines duplication based on Jaccard similarity and rules, updates deduplication information.
    - is_delete(): Checks if content returned from url2text indicates article deletion.
    - split_text(): Splits text into word lists for MinHash calculation.
    - __enter__, __exit__: Implements context management protocol, ensures MinHash signatures and deduplication information are saved on exit.
- **Main Dependencies:** pathlib, re, pickle, sys, collections.defaultdict, requests, lxml.etree, tqdm, upstash_vector (optional, deprecated part), nltk.translate.bleu_score, datasketch, util.util (internal project).

**message2md.py**
- **Main Function/Purpose:** Converts processed and deduplicated article information into Markdown format files for blog publishing.
- **Key Components:**
  - get_valid_message(): Filters valid articles from message_info.json (not deleted, not highly duplicated), groups by date and blogger name.
  - message2md(): Generates two main Markdown files:
    - 微信公众号聚合平台_按时间区分.md: Lists articles from the past six months in reverse chronological order.
    - 微信公众号聚合平台_按公众号区分.md: Lists articles from the past six months by official account name.
  - single_message2md(): Generates individual Markdown files for articles from the past 15 days, including cover images and article content (for site search).
    - Downloads and processes article cover images (cropping, scaling).
    - Generates independent .md files for each article, including Hexo front-matter (title, date, cover image, tags, etc.).
    - Cleans special characters and HTML tags from article content to adapt to Markdown and Nunjucks templates.
    - Deletes excess local Markdown files and cover images.
- **Main Dependencies:** os, re, sys, pathlib, datetime, requests, tqdm, PIL.Image, collections.defaultdict, util.util (internal project).

### request_/ Directory

**wechat_request.py**
- **Main Function/Purpose:** Encapsulates request logic for interacting with WeChat Official Account platform.
- **Key Components:**
  - jstime2realtime(): Converts JavaScript timestamps to standard datetime strings.
  - time_delta(): Calculates time difference between two time strings.
  - time_now(): Gets current formatted datetime string.
  - WechatRequest (class):
    - __init__(): Initializes required headers, cookies, and tokens (loaded from id_info.json).
    - name2fakeid(): Searches and returns fakeid based on official account name.
    - fakeid2message_update(): Retrieves latest article list published by the official account based on fakeid, compares with existing article IDs to avoid duplicate retrieval.
    - login(): Uses DrissionPage to simulate login to WeChat Official Account platform, automatically obtains tokens and cookies, saves to id_info.json.
    - session_is_overdue(): Checks API return error information, determines if session or token has expired, calls login() to re-login if expired. Handles request frequency control errors.
    - sort_messages(): (Appears unused or auxiliary function) Sorts articles in message_info.json by creation time.
- **Main Dependencies:** requests, json, lxml.etree, time, datetime, DrissionPage (for login), util.util (internal project).

### data/ Directory
- **Main Function/Purpose:** Stores JSON data files generated during project execution and generated Markdown files.
- **Key Files (inferred from code analysis):**
  - name2fakeid.json: Stores mapping from official account names to fakeids.
  - message_info.json: Stores crawled article information for each official account (title, link, creation time, ID) and latest crawl time.
  - id_info.json: Stores WeChat Official Account platform tokens and cookies.
  - issues_message.json: Stores problem information during article processing, such as deleted article IDs (is_delete), MinHash deduplication results (dup_minhash).
  - message_detail_text.json: Caches retrieved detailed article text content, keyed by article ID.
  - minhash_dict.pickle: Caches article MinHash signatures to accelerate deduplication process.
  - 微信公众号聚合平台_按时间区分.md: Generated time-aggregated Markdown file.
  - 微信公众号聚合平台_按公众号区分.md: Generated official account-aggregated Markdown file.
  - Other individual article Markdown files (ID.md).

### figures/ Directory
- **Main Function/Purpose:** Stores project-related images, such as preview images referenced in README.md like blog_preview.png.

### .git/ Directory
- **Main Function/Purpose:** Git version control system directory, stores project version history and metadata.

## Summary Notes

This project aims to aggregate articles from multiple WeChat official accounts, perform deduplication processing, and generate Markdown files for easy reading and deployment to personal blog systems (such as Hexo).

The core workflow includes: configuring official accounts, crawling articles, deduplication using MinHash LSH, and generating aggregated and individual article Markdown files.

Features automatic login to obtain tokens and cookies to handle session expiration issues.

Data persistence is primarily implemented through JSON files.

The daily_update.sh indicates the project supports scheduled automatic updates.

---
来自 Perplexity 的回答: pplx.ai/share
