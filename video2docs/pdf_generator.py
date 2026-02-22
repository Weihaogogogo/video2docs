"""PDF生成器模块 - 将Markdown转换为PDF"""
import subprocess
import os
from pathlib import Path
from rich.console import Console

# macOS Homebrew 库路径
import platform
if platform.system() == "Darwin":
    os.environ.setdefault("DYLD_LIBRARY_PATH", "/opt/homebrew/lib")

console = Console()


class PDFGenerator:
    """PDF文档生成器"""

    def __init__(self, output_dir: Path):
        """
        初始化生成器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, markdown_path: Path) -> Path:
        """
        将Markdown转换为PDF

        Args:
            markdown_path: Markdown文件路径

        Returns:
            生成的PDF路径
        """
        output_pdf = markdown_path.with_suffix('.pdf')

        console.print(f"[cyan]正在生成 PDF...[/cyan]")

        # 先尝试使用 WeasyPrint
        try:
            return self._generate_weasyprint(markdown_path, output_pdf)
        except ImportError:
            console.print("[yellow]WeasyPrint 未安装，尝试使用 Pandoc...[/yellow]")
        except Exception as e:
            console.print(f"[yellow]WeasyPrint 失败: {str(e)}，尝试 Pandoc...[/yellow]")

        # Fallback 到 Pandoc
        try:
            return self._generate_pandoc(markdown_path, output_pdf)
        except Exception as e:
            console.print(f"[red]Pandoc 生成失败: {str(e)}[/red]")
            return None

        return None

    def _get_local_fonts_css(self) -> str:
        """获取本地字体 CSS"""
        fonts_dir = Path(__file__).parent.parent / "fonts"

        # 字体文件路径
        noto_regular = fonts_dir / "NotoSansSC-Regular.ttf"
        noto_bold = fonts_dir / "NotoSansSC-Bold.ttf"
        jetbrains_regular = fonts_dir / "JetBrainsMono-Regular.ttf"
        jetbrains_bold = fonts_dir / "JetBrainsMono-Bold.ttf"

        return f"""
        @font-face {{
            font-family: 'Noto Sans SC';
            src: local('{noto_regular}'), local('Noto Sans SC');
            font-weight: normal;
            font-style: normal;
        }}
        @font-face {{
            font-family: 'Noto Sans SC';
            src: local('{noto_bold}'), local('Noto Sans SC Bold');
            font-weight: bold;
            font-style: normal;
        }}
        @font-face {{
            font-family: 'JetBrains Mono';
            src: local('{jetbrains_regular}'), local('JetBrains Mono');
            font-weight: normal;
            font-style: normal;
        }}
        @font-face {{
            font-family: 'JetBrains Mono';
            src: local('{jetbrains_bold}'), local('JetBrains Mono Bold');
            font-weight: bold;
            font-style: normal;
        }}
        """

    def _generate_weasyprint(self, markdown_path: Path, output_pdf: Path) -> Path:
        import weasyprint
        from weasyprint import HTML, CSS

        # 读取 Markdown 文件
        md_content = markdown_path.read_text(encoding='utf-8')

        # WeasyPrint 需要 HTML，转换 Markdown 为简单 HTML
        # 由于 WeasyPrint 不直接支持 Markdown，需要先转换
        html_content = self._markdown_to_html(md_content, markdown_path.parent)

        # 生成 PDF
        HTML(string=html_content).write_pdf(output_pdf)

        console.print(f"[green]PDF 生成成功: {output_pdf.name}[/green]")
        return output_pdf

    def _markdown_to_html(self, md_content: str, base_dir: Path) -> str:
        """将 Markdown 转换为 HTML（使用 markdown 库）"""
        import markdown
        import re

        # 使用 markdown 库转换 - 添加更多 extensions
        md = markdown.Markdown(extensions=[
            'extra',        # 表格、代码块等
            'codehilite',   # 代码高亮
            'toc',          # 目录
            'nl2br',        # 换行转 <br>
            'tables',       # 表格
            'fenced_code',  # 代码块
        ])
        html_body = md.convert(md_content)

        # 处理图片路径 - 将相对路径转换为绝对路径
        html_body = re.sub(
            r'<img\s+(?:[^>]*?\s+)?src="(?!http|file://)([^"]+)"',
            lambda m: f'<img src="file://{(base_dir / m.group(1)).resolve()}"',
            html_body
        )

        # 获取本地字体 CSS
        local_fonts_css = self._get_local_fonts_css()

        # CSS 样式 - 紧凑型
        css = f"""
        <style>
            {local_fonts_css}
            @page {{
                margin: 15mm;
                size: A4;
            }}
            body {{
                font-family: "Noto Sans SC", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                font-size: 12pt;
                line-height: 1.5;
                margin: 0;
                padding: 0;
                color: #333;
            }}
            h1 {{ color: #1a1a1a; border-bottom: 2px solid #0066cc; padding-bottom: 8px; margin: 20px 0 15px 0; font-size: 20pt; }}
            h2 {{ color: #2d2d2d; margin-top: 20px; margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 5px; font-size: 16pt; }}
            h3 {{ color: #444; margin-top: 15px; margin-bottom: 10px; font-size: 14pt; }}
            h4, h5, h6 {{ color: #555; margin-top: 12px; margin-bottom: 8px; font-size: 12pt; }}
            img {{ max-width: 100%; height: auto; margin: 10px 0; border-radius: 3px; }}
            pre {{
                background: #f6f8fa;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
                border: 1px solid #e1e4e8;
                font-size: 10pt;
                line-height: 1.4;
            }}
            code {{
                font-family: "JetBrains Mono", "SF Mono", Monaco, Consolas, monospace;
                background: #f6f8fa;
                padding: 1px 4px;
                border-radius: 2px;
                font-size: 10pt;
            }}
            pre code {{ background: none; padding: 0; }}
            blockquote {{
                border-left: 3px solid #0066cc;
                margin: 10px 0;
                padding: 8px 15px;
                background: #f9f9f9;
                color: #555;
            }}
            table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 11pt; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background: #f5f5f5; font-weight: 600; }}
            tr:nth-child(even) {{ background: #fafafa; }}
            ul, ol {{ padding-left: 20px; margin: 8px 0; }}
            ol {{ list-style-type: decimal; }}
            ul {{ list-style-type: disc; }}
            li {{ margin: 3px 0; }}
            li > p {{ margin: 0; }}
            hr {{ border: none; border-top: 1px solid #eee; margin: 15px 0; }}
            a {{ color: #0066cc; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            p {{ margin: 8px 0; text-align: justify; }}
            /* 代码高亮样式 */
            .hll {{ background-color: #ffffcc; }}
            .c {{ color: #6a737d; font-style: italic; }}
            .k {{ color: #d73a49; font-weight: bold; }}
            .o {{ color: #22863a; }}
            .cm {{ color: #6a737d; font-style: italic; }}
            .cp {{ color: #005cc5; }}
            .c1 {{ color: #6a737d; font-style: italic; }}
            .cs {{ color: #6a737d; font-style: italic; }}
            .gd {{ color: #b31d28; background-color: #ffeef0; }}
            .ge {{ font-style: italic; }}
            .gr {{ color: #b31d28; }}
            .gh {{ color: #005cc5; font-weight: bold; }}
            .gi {{ color: #22863a; background-color: #f0fff4; }}
            .go {{ color: #6a737d; }}
            .gp {{ color: #e36209; font-weight: bold; }}
            .gs {{ font-weight: bold; }}
            .gu {{ color: #6f42c1; font-weight: bold; }}
            .gt {{ color: #b31d28; }}
            .w {{ color: #bbbbbb; }}
            .mf {{ color: #005cc5; }}
            .mh {{ color: #005cc5; }}
            .mi {{ color: #005cc5; }}
            .mo {{ color: #005cc5; }}
            .sb {{ color: #032f62; }}
            .sc {{ color: #032f62; }}
            .sd {{ color: #032f62; }}
            .s2 {{ color: #032f62; }}
            .se {{ color: #032f62; font-weight: bold; }}
            .sh {{ color: #032f62; }}
            .si {{ color: #e36209; }}
            .sx {{ color: #032f62; font-weight: bold; }}
            .sr {{ color: #22863a; }}
            .s1 {{ color: #032f62; }}
            .ss {{ color: #005cc5; }}
            .bp {{ color: #005cc5; }}
            .vc {{ color: #005cc5; }}
            .vg {{ color: #005cc5; }}
            .vi {{ color: #005cc5; }}
            .il {{ color: #005cc5; }}
        </style>
        """

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    {css}
</head>
<body>
{html_body}
</body>
</html>"""

    def _generate_pandoc(self, markdown_path: Path, output_pdf: Path) -> Path:
        """使用 Pandoc 生成 PDF"""
        import pypandoc
        pypandoc.ensure_pandoc_installed()

        # 获取字体路径
        fonts_dir = Path(__file__).parent.parent / "fonts"
        noto_regular = fonts_dir / "NotoSansSC-Regular.ttf"
        jetbrains_regular = fonts_dir / "JetBrainsMono-Regular.ttf"

        # 切换到输出目录，确保图片路径正确
        orig_cwd = os.getcwd()
        try:
            os.chdir(markdown_path.parent)

            pypandoc.convert_file(
                str(markdown_path.name),
                'pdf',
                outputfile=str(output_pdf),
                extra_args=[
                    '--resource-path=.:images',
                    '-V', f'mainfont={noto_regular}',
                    '-V', f'monofont={jetbrains_regular}',
                    '-V', 'geometry:margin=15mm',
                    '-V', 'fontsize=11pt',
                    '-V', 'linestretch=1.5',
                ]
            )
        finally:
            os.chdir(orig_cwd)

        console.print(f"[green]PDF 生成成功: {output_pdf.name}[/green]")
        return output_pdf
