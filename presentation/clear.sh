#!/usr/bin/env bash

# 检查是否提供了文件名参数
if [ $# -ne 1 ]; then
  echo "用法: $0 <文件名>"
  exit 1
fi

# 从参数中获取文件名
filename="$1"

# 删除对应的 .s 文件
s_file="$filename.s"
if [ -e "$s_file" ]; then
  rm "$s_file"
  echo "已删除文件 '$s_file'"
else
  echo "文件 '$s_file' 不存在."
fi

# 删除对应的 .exe 文件
exe_file="$filename.exe"
if [ -e "$exe_file" ]; then
  rm "$exe_file"
  echo "已删除文件 '$exe_file'"
else
  echo "文件 '$exe_file' 不存在."
fi
