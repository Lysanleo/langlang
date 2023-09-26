#!/usr/bin/env bash

if [ $# -ne 1 ]; then
  echo "用法: $0 <文件名>"
  exit 1
fi

filename="$1"

# 检查文件是否存在
if [ ! -e "$filename.ll" ]; then
  echo "文件 '$filename'.ll 不存在."
  exit 1
fi

# 提取文件名（去除扩展名）
basename=$(basename -- "$filename")
name="${basename%.*}"

# 生成并输出即将运行的指令
com_command="./compile.py $name"
link_command="./link-and-run.py $name"
echo "将要运行的指令:"
echo "$com_command"
echo "$link_command"

# 运行指令
$com_command && $link_command


