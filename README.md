This project is applying for free VPS resource support from ZMTO.COM, thank you.


*   **项目名称:**  (WeChatOA_Aggregation)
*  
*   **主要技术栈:** Python
*   **主要库:** DrissionPage, lxml, requests, tqdm, datasketch, Pillow

## 文件分析详情

### 根目录 (`woa/`)

*   **`requirements.txt`**
    *   **主要功能/目的:** 列出项目运行所需的 Python 库及其版本。
    *   **关键组件:**
        *   `DrissionPage`: 用于网页自动化和数据提取。
        *   `lxml`: 用于 XML 和 HTML 解析。
        *   `requests`: 用于发送 HTTP 请求。
        *   `tqdm`: 用于显示进度条。
        *   `datasketch`: 用于 MinHash LSH 算法，进行文本去重。
    *   **主要依赖:** 无项目内部依赖。
*   **`main.py`**
    *   **主要功能/目的:** 项目的主入口脚本，负责协调整个文章爬取、去重和 Markdown 生成流程。
    *   **关键组件:**
        *   从 `name2fakeid.json` 和 `message_info.json` 加载公众号信息和已爬取的文章信息。
        *   遍历配置的公众号列表 (`name2fakeid_dict`)。
        *   如果公众号是新添加的，则获取其 `fakeid`。
        *   检查是否需要更新该公众号的文章 (基于上次爬取时间)。
        *   调用 `WechatRequest.fakeid2message_update()` 更新文章列表。
        *   更新 `message_info.json`。
        *   调用 `minHashLSH.write_vector()` 进行文章去重。
        *   调用 `message2md()` 和 `single_message2md()` 生成 Markdown 文件。
    *   **主要依赖:** `tqdm`, `request_.wechat_request.WechatRequest`, `util.message2md.message2md`, `util.message2md.single_message2md`, `util.util.handle_json`, `util.filter_duplication.minHashLSH`。
*   **`README.md`**
    *   **主要功能/目的:** 提供项目的基本介绍、功能列表 (TODO)、环境配置说明 (token/cookie 获取)、MinHash 实验记录以及参考的类似项目。
    *   **关键组件:** 项目概述、功能特性、使用指南。
    *   **主要依赖:** 无。
*   **`daily_update.sh`**
    *   **主要功能/目的:** shell 脚本，用于定期执行爬虫任务，可能是为了自动化每日更新。
    *   **关键组件:** 脚本命令（具体内容未查看，但通常包含执行 `main.py` 的命令）。
    *   **主要依赖:** 依赖于 `main.py` 的正确执行。

### `util/` 目录

*   **`util.py`**
    *   **主要功能/目的:** 包含项目通用的工具函数。
    *   **关键组件:**
        *   `headers`: 定义通用的 HTTP 请求头。
        *   `message_is_delete()`: 检查微信文章是否已被发布者删除。
        *   `update_message_info()`: 自检函数，更新 `message_info.json` 文件，移除已删除的文章。
        *   `handle_json()`: 封装了 JSON 文件的读取和安全写入操作（通过临时文件避免写入中断导致数据丢失）。
        *   `check_text_ratio()`: 检测文本中英文和符号的占比。
    *   **主要依赖:** `pathlib`, `shutil`, `tqdm`, `json`, `requests`, `lxml.etree`。
*   **`filter_duplication.py`**
    *   **主要功能/目的:** 实现文章去重逻辑，主要使用 MinHash LSH 算法。
    *   **关键组件:**
        *   `url2text()`: 从给定的 URL 提取文章的主要文本内容，尝试处理不同的HTML结构并处理已删除或请求错误的情况。
        *   `calc_duplicate_rate1()`: 计算两个文本列表的重复字数比例。
        *   `calc_duplicate_rate_max()`: 结合 `calc_duplicate_rate1` 和 `sentence_bleu` 计算最大重复率。
        *   `get_filtered_message()`: （似乎是早期版本或辅助函数）基于标题相似性进行初步筛选和内容重复率计算。
        *   `generate_title_head()`: （似乎是早期版本或辅助函数）生成基于文章标题的统计信息。
        *   `UpstashVector` (class): (已弃用) 一个尝试使用 Upstash Vector DB 进行向量相似度搜索去重的类。
        *   `minHashLSH` (class): 核心去重类。
            *   `__init__()`: 初始化 MinHashLSH 对象，加载已处理的文章ID、MinHash签名缓存。
            *   `write_vector()`: 遍历文章，为新文章生成 MinHash 签名，查询 LSH 索引以查找相似文章，并根据 Jaccard 相似度和规则判断是否重复，更新去重信息。
            *   `is_delete()`: 检查从 `url2text` 返回的内容是否表示文章已删除。
            *   `split_text()`: 将文本分割成词语列表，用于 MinHash 计算。
            *   `__enter__`, `__exit__`: 实现上下文管理协议，确保在退出时保存 MinHash 签名和去重信息。
    *   **主要依赖:** `pathlib`, `re`, `pickle`, `sys`, `collections.defaultdict`, `requests`, `lxml.etree`, `tqdm`, `upstash_vector` (可选, 已弃用部分), `nltk.translate.bleu_score`, `datasketch`,  `util.util` (项目内部)。
*   **`message2md.py`**
    *   **主要功能/目的:** 将处理和去重后的文章信息转换成 Markdown 格式文件，用于博客发布。
    *   **关键组件:**
        *   `get_valid_message()`: 从 `message_info.json` 中筛选出有效文章（未删除、未高度重复），并按日期和博主名进行分组。
        *   `message2md()`: 生成两个主要的 Markdown 文件：
            *   `微信公众号聚合平台_按时间区分.md`: 将近半年的文章按日期逆序列出。
            *   `微信公众号聚合平台_按公众号区分.md`: 将近半年的文章按公众号名称列出。
        *   `single_message2md()`: 为近15天的文章生成单独的 Markdown 文件，包含封面图和文章内容（用于站内搜索）。
            *   下载并处理文章封面图 (裁剪、缩放)。
            *   为每篇文章生成独立的 `.md` 文件，包含 Hexo 的 front-matter (标题, 日期, 封面图, 标签等)。
            *   清理文章内容中的特殊字符和 HTML 标签，以适应 Markdown 和 Nunjucks 模板。
            *   删除本地多余的 Markdown 文件和封面图片。
    *   **主要依赖:** `os`, `re`, `sys`, `pathlib`, `datetime`, `requests`, `tqdm`, `PIL.Image`, `collections.defaultdict`, `util.util` (项目内部)。

### `request_/` 目录

*   **`wechat_request.py`**
    *   **主要功能/目的:** 封装了与微信公众号平台交互的请求逻辑。
    *   **关键组件:**
        *   `jstime2realtime()`: 将 JavaScript 时间戳转换为标准日期时间字符串。
        *   `time_delta()`: 计算两个时间字符串之间的时间差。
        *   `time_now()`: 获取当前格式化的日期时间字符串。
        *   `WechatRequest` (class):
            *   `__init__()`: 初始化请求所需的 `headers`, `cookie`, 和 `token` (从 `id_info.json` 加载)。
            *   `name2fakeid()`: 根据公众号名称搜索并返回其 `fakeid`。
            *   `fakeid2message_update()`: 根据 `fakeid` 获取该公众号发布的最新文章列表，会与已存在的文章ID进行比较，避免重复获取。
            *   `login()`: 使用 `DrissionPage` 模拟登录微信公众平台，自动获取 `token` 和 `cookie`，并保存到 `id_info.json`。
            *   `session_is_overdue()`: 检查 API 返回的错误信息，判断 session 或 token 是否过期，如果过期则调用 `login()` 重新登录。处理请求频率控制错误。
            *   `sort_messages()`: (似乎未使用或为辅助函数) 对 `message_info.json` 中的文章按创建时间排序。
    *   **主要依赖:** `requests`, `json`, `lxml.etree`, `time`, `datetime`, `DrissionPage` (用于 `login`), `util.util` (项目内部)。

### `data/` 目录

*   **主要功能/目的:** 存储项目运行过程中产生的 JSON 数据文件和生成的 Markdown 文件。
*   **关键文件 (推测，基于代码分析):**
    *   `name2fakeid.json`: 存储公众号名称到 `fakeid` 的映射。
    *   `message_info.json`: 存储每个公众号已爬取的文章信息 (标题, 链接, 创建时间, ID) 和最新爬取时间。
    *   `id_info.json`: 存储微信公众号平台的 `token` 和 `cookie`。
    *   `issues_message.json`: 存储文章处理过程中的问题信息，如已删除文章ID (`is_delete`)，MinHash去重结果 (`dup_minhash`)。
    *   `message_detail_text.json`: 缓存已获取的文章详细文本内容，键为文章ID。
    *   `minhash_dict.pickle`: 缓存文章的 MinHash 签名，用于加速去重过程。
    *   `微信公众号聚合平台_按时间区分.md`: 生成的按时间聚合的 Markdown 文件。
    *   `微信公众号聚合平台_按公众号区分.md`: 生成的按公众号聚合的 Markdown 文件。
    *   其他单独的文章 Markdown 文件 (ID.md)。

### `figures/` 目录

*   **主要功能/目的:** 存储项目相关的图片，例如 `README.md` 中引用的预览图 `blog_preview.png`。

### `.git/` 目录

*   **主要功能/目的:** Git 版本控制系统目录，存储项目的版本历史和元数据。

## 总结备注

*   该项目旨在聚合多个微信公众号的文章，进行去重处理后，生成 Markdown 文件，方便用户阅读和部署到个人博客系统（如 Hexo）。
*   核心流程包括：配置公众号、爬取文章、使用 MinHash LSH 去重、生成聚合及单个文章的 Markdown 文件。
*   具有自动登录获取 `token` 和 `cookie` 的功能，以应对会话过期问题。
*   数据持久化主要通过 JSON 文件实现。
*   `daily_update.sh` 表明项目支持定时自动更新。 
