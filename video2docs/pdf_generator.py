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
        """将 Markdown 转换为 HTML（简化版）"""
        import re

        html_parts = []
        lines = md_content.split('\n')

        # 简单的 CSS 样式
        css = """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #333; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }
            h2 { color: #555; margin-top: 30px; }
            h3 { color: #666; }
            img { max-width: 100%; height: auto; margin: 10px 0; }
            pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
            code { background: #f0f0f0; padding: 2px 5px; border-radius: 3px; }
            blockquote { border-left: 4px solid #0066cc; margin: 0; padding-left: 15px; color: #666; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background: #f5f5f5; }
        </style>
        """

        html_parts.append(f"<html><head><meta charset='utf-8'>{css}</head><body>")

        in_code_block = False
        for line in lines:
            # 代码块
            if line.startswith('```'):
                if in_code_block:
                    html_parts.append('</code></pre>')
                    in_code_block = False
                else:
                    lang = line[3:].strip()
                    html_parts.append(f'<pre><code class="language-{lang}">')
                    in_code_block = True
                continue

            if in_code_block:
                html_parts.append(line)
                continue

            # 图片
            img_match = re.match(r'!\[(.*?)\]\((.+?)\)', line)
            if img_match:
                alt_text, img_path = img_match.groups()
                # 转换为绝对路径
                if not img_path.startswith('/') and not img_path.startswith('http'):
                    img_abs_path = (base_dir / img_path).resolve()
                    img_path = f"file://{img_abs_path}"
                html_parts.append(f'<p><img src="{img_path}" alt="{alt_text}"></p>')
                continue

            # 标题
            if line.startswith('# '):
                html_parts.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                html_parts.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('### '):
                html_parts.append(f'<h3>{line[4:]}</h3>')
            # 引用
            elif line.startswith('> '):
                html_parts.append(f'<blockquote>{line[2:]}</blockquote>')
            # 列表
            elif line.startswith('- ') or line.startswith('* '):
                html_parts.append(f'<li>{line[2:]}</li>')
            # 分割线
            elif line == '---':
                html_parts.append('<hr>')
            # 段落
            elif line.strip():
                html_parts.append(f'<p>{line}</p>')
            else:
                html_parts.append('<br>')

        html_parts.append('</body></html>')
        return '\n'.join(html_parts)

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
