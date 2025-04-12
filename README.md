# ainotion
Put Notion files to Vector DB

docker build -f docker/Dockerfile -t ainotion:latest .   

docker run -it --rm -v $(pwd):/home/work/ ainotion:latest bash

# --user $(id -u):$(id -g) , to avoid detected dubious ownership error
# -v $HOME/.gitconfig:${whoami}/.gitconfig, to make run git config global user.name in the contianer to get global settings.
docker run -it --rm -v $(pwd)/src/git:/home/work/git -v /home/work/sourcecode/:/home/work/sourcecode/ --user $(id -u):$(id -g) -v $HOME/.gitconfig:${whoami}/.gitconfig ainotion:latest bash

# git command
## Count file changes from yesterday's commits
command:
```
git log --since="yesterday" --until="yesterday 23:59" --shortstat \
  | awk '/files changed/{files+=$1; ins+=$4; del+=$6} END{print files" files, +"ins"/-"del" lines"}'
```
result:
```
22 files, +4651/-241 lines
```


## Show detailed commit statistics from two weeks ago
command:
```
git log --all \
        --since="2 weeks ago" --until="yesterday 23:59" \
        --numstat \
        --pretty=format:'@@@%s|%an' --date=iso-strict |
awk '
    BEGIN {
        FS = "[\t ]+"                    # Set both space and tab as delimiters
    }

    # ---------- ① Read new commit header ----------
    /^@@@/ {
        subj  = substr($0,4)
        split(subj, a, "|")
        msg    = a[1]                    # Commit message (key)
        author = a[2]                    # Author

        commits[msg]++                   # Accumulate commit count

        # Maintain author list (deduplicated)
        if (authors[msg] == "") authors[msg] = author
        else if (authors[msg] !~ author) authors[msg] = authors[msg] "," author
        next
    }

    # ---------- ② Read numstat line ----------
    NF==3 && $1 != "-" {
        add[msg] += $1
        del[msg] += $2

        file = $3                        # Third column is file path
        key  = msg SUBSEP file           # Unique key: message + file

        if (!(key in seen)) {            # Deduplicate
            files[msg] = (files[msg] == "" ? file : files[msg] "," file)
            seen[key] = 1
        }
    }

    # ---------- ③ Output ----------
    END {
        for (m in add) {
            printf "%-40s ｜ %2d commits ｜ +%d / -%d | %s ｜ %s \n",
                   m, commits[m], add[m], del[m], authors[m], files[m]
        }
    }'
```
result:
```
db implement                             ｜  1 commits ｜ +19 / -0 | Wilson Li ｜ db/init/init.sql,docker-compose.yml 
testcase                                 ｜  2 commits ｜ +95 / -1 | Wilson Li ｜ notion_articles.py 
json file                                ｜  1 commits ｜ +6816 / -0 | Wilson Li ｜ work_records.json 
new token                                ｜ 13 commits ｜ +178 / -116 | Wilson Li ｜ notion_articles.py 
import                                   ｜  1 commits ｜ +70 / -0 | Wilson Li ｜ weekly_report_generator.py 
fix time                                 ｜ 20 commits ｜ +131 / -156 | Wilson Li ｜ src/extract_weekly_logs.py 
support openai                           ｜  3 commits ｜ +76 / -5 | Wilson Li ｜ docker-compose.yml,src/config_reader.py,src/extract_weekly_logs.py,weekly_report_generator.py 
```
# 使用默认值（昨天到今天）
python src/git/main.py

# 指定时间范围
python src/git/main.py --since "2024-01-01" --until "2024-01-31"

# 使用相对时间
python src/git/main.py --since "1 week ago" --until "yesterday"

# 指定配置文件
python src/git/main.py --config path/to/config.yaml --since "2024-01-01" --until "2024-01-31"

