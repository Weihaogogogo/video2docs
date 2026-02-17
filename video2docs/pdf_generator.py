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

    def _generate_weasyprint(self, markdown_path: Path, output_pdf: Path) -> Path:
        """使用 WeasyPrint 生成 PDF"""
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

        # 使用 markdown 库转换
        md = markdown.Markdown(extensions=[
            'extra',    # 表格、代码块等
            'codehilite', # 代码高亮
            'toc',      # 目录
        ])
        html_body = md.convert(md_content)

        # 处理图片路径 - 将相对路径转换为绝对路径
        html_body = re.sub(
            r'<img\s+(?:[^>]*?\s+)?src="(?!http|file://)([^"]+)"',
            lambda m: f'<img src="file://{(base_dir / m.group(1)).resolve()}"',
            html_body
        )

        # CSS 样式
        css = """
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                margin: 40px;
                line-height: 1.8;
                color: #333;
            }
            h1 { color: #1a1a1a; border-bottom: 3px solid #0066cc; padding-bottom: 10px; }
            h2 { color: #2d2d2d; margin-top: 35px; border-bottom: 1px solid #eee; padding-bottom: 8px; }
            h3 { color: #444; margin-top: 25px; }
            h4, h5, h6 { color: #555; }
            img { max-width: 100%; height: auto; margin: 15px 0; border-radius: 5px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            pre {
                background: #f6f8fa;
                padding: 15px;
                border-radius: 6px;
                overflow-x: auto;
                border: 1px solid #e1e4e8;
            }
            code {
                font-family: "SF Mono", Monaco, Consolas, monospace;
                background: #f6f8fa;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 0.9em;
            }
            pre code { background: none; padding: 0; }
            blockquote {
                border-left: 4px solid #0066cc;
                margin: 15px 0;
                padding: 10px 20px;
                background: #f9f9f9;
                color: #555;
            }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background: #f5f5f5; font-weight: 600; }
            tr:nth-child(even) { background: #fafafa; }
            ul, ol { padding-left: 25px; }
            li { margin: 5px 0; }
            hr { border: none; border-top: 1px solid #eee; margin: 25px 0; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
            /* 代码高亮样式 */
            .hll { background-color: #ffffcc; }
            .c { color: #6a737d; font-style: italic; }
            .k { color: #d73a49; font-weight: bold; }
            .o { color: #22863a; }
            .cm { color: #6a737d; font-style: italic; }
            .cp { color: #005cc5; }
            .c1 { color: #6a737d; font-style: italic; }
            .cs { color: #6a737d; font-style: italic; }
            .gd { color: #b31d28; background-color: #ffeef0; }
            .ge { font-style: italic; }
            .gr { color: #b31d28; }
            .gh { color: #005cc5; font-weight: bold; }
            .gi { color: #22863a; background-color: #f0fff4; }
            .go { color: #6a737d; }
            .gp { color: #e36209; font-weight: bold; }
            .gs { font-weight: bold; }
            .gu { color: #6f42c1; font-weight: bold; }
            .gt { color: #b31d28; }
            .w { color: #bbbbbb; }
            .mf { color: #005cc5; }
            .mh { color: #005cc5; }
            .mi { color: #005cc5; }
            .mo { color: #005cc5; }
            .sb { color: #032f62; }
            .sc { color: #032f62; }
            .sd { color: #032f62; }
            .s2 { color: #032f62; }
            .se { color: #032f62; font-weight: bold; }
            .sh { color: #032f62; }
            .si { color: #e36209; }
            .sx { color: #032f62; font-weight: bold; }
            .sr { color: #22863a; }
            .s1 { color: #032f62; }
            .ss { color: #005cc5; }
            .bp { color: #005cc5; }
            .vc { color: #005cc5; }
            .vg { color: #005cc5; }
            .vi { color: #005cc5; }
            .il { color: #005cc5; }
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
                    '-V', 'mainfont=-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto',
                    '-V', 'geometry:margin=1in',
                ]
            )
        finally:
            os.chdir(orig_cwd)

        console.print(f"[green]PDF 生成成功: {output_pdf.name}[/green]")
        return output_pdf
