<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-quotation

_✨ NoneBot Plugin ✨_


<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/MerCuJerry/nonebot-plugin-quotation.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-quotation">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-quotation.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="python">
<a href="https://pypi.python.org/pypi/nonebot-plugin-quotation" rel="nofollow">
    <img alt="pypi download" src="https://img.shields.io/pypi/dm/nonebot-plugin-quotation" style="max-width: 100%;">
</a>
</div>

## 📖 介绍

基于 [nonebot-plugin-alconna](https://github.com/nonebot/plugin-alconna), 适用于 [Nonebot2](https://github.com/nonebot/nonebot2) 的语录插件

## 💿 安装

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-quotation
</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-quotation
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-quotation
</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-quotation
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_quotation"]

</details>

## ⚙️ 配置

### 常规配置项，位于.env文件里

```ini
#受信任的用户id列表，列表内用户可以直接添加语录和审查语录
quotation_trusted_user=[]
```

## 💬 指令

### 指令表
| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|:----:|
| 来点(参数) | 所有人 | 否 | 所有 | 使用时去掉括号 |
| {COMMAND_START}查询语录 | SUPERUSER | 否 | 所有 | 同上 |
| {COMMAND_START}更新语录 | SUPERUSER & 信任用户 | 否 | 所有 | 同上 |
| {COMMAND_START}添加(参数) | 所有人 | 否 | 所有 | 同上 |
| {COMMAND_START}审查语录 | SUPERUSER & 信任用户 | 否 | 所有 | 同上 |
| {COMMAND_START}查询语录别名 | SUPERUSER & 信任用户 | 否 | 所有 | 同上 |
| {COMMAND_START}添加语录别名 | SUPERUSER & 信任用户 | 否 | 所有 | 同上 |
| {COMMAND_START}删除语录别名 | SUPERUSER & 信任用户 | 否 | 所有 | 同上 |