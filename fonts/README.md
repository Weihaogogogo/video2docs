# 字体目录

本项目已自带字体文件，PDF 导出时会自动使用这些字体，无需额外安装。

## 已包含字体

| 字体 | 文件 | 用途 |
|------|------|------|
| Noto Sans SC | `NotoSansSC-Regular.ttf`<br>`NotoSansSC-Bold.ttf` | 正文（中英文） |
| JetBrains Mono | `JetBrainsMono-Regular.ttf`<br>`JetBrainsMono-Bold.ttf` | 代码块 |

## 字体来源

- **Noto Sans SC**: Google Noto 家族中文字体，支持简体中文
  - GitHub: https://github.com/googlefonts/noto-cjk
  - 许可证: SIL Open Font License (OFL)

- **JetBrains Mono**: JetBrains 出品的代码字体
  - GitHub: https://github.com/JetBrains/JetBrainsMono
  - 许可证: SIL Open Font License (OFL)

## 替换字体

如需使用其他字体：

1. 将字体文件（.ttf 或 .otf 格式）放入本目录
2. 修改 `video2docs/pdf_generator.py` 中的字体路径指向新文件
3. 重新运行 PDF 导出

## 注意事项

- 字体文件较大，GitHub 仓库已使用 Git LFS 存储
- 中文字体文件通常较大（约 10-20MB），请确保网络通畅后下载
