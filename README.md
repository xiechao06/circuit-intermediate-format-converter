# Project Title

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)
- [Contributing](../CONTRIBUTING.md)

## About <a name = "about"></a>

电路中间格式(intermediate format)生成工具。目前仅仅支持从[kicad_sch](https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/index.html)格式生成.

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)

### Installing

```bash
# 如果要通过本地源代码安装方式o
git clone https://github.com/xiechao06/circuit-intermediate-format-converter
cd circuit-intermediate-format-converter
uv tool install .

# 如果直接从远程仓库安装
uv tool install git+https://github.com/xiechao06/circuit-intermediate-format-converter
```

## Usage <a name = "usage"></a>

```bash
# 使用uvx直接从仓库执行
uvx --from git+https://github.com/xiechao06/circuit-intermediate-format-converter cifc --help

# 如果已经在本地安装
uvx cifc --help
```
