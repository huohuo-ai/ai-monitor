from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

class PDFGenerator:
    def __init__(self, output_path):
        self.output_path = output_path
        self.doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        self.story = []
        self.styles = getSampleStyleSheet()
        self._register_fonts()
        self._setup_styles()
    
    def _register_fonts(self):
        font_paths = [
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/STSong.ttc',
            '/System/Library/Fonts/Helvetica.ttc',
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        ]
        
        self.chinese_font = 'Helvetica'
        self.chinese_bold_font = 'Helvetica-Bold'
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path, subfontIndex=0))
                    pdfmetrics.registerFont(TTFont('ChineseFontBold', font_path, subfontIndex=0))
                    self.chinese_font = 'ChineseFont'
                    self.chinese_bold_font = 'ChineseFontBold'
                    break
                except:
                    continue
    
    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontName=self.chinese_bold_font,
            fontSize=24,
            textColor=colors.HexColor('#0056b3'),
            spaceAfter=30,
            alignment=1
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontName=self.chinese_bold_font,
            fontSize=18,
            textColor=colors.HexColor('#003d7a'),
            spaceAfter=12,
            spaceBefore=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomSubHeading',
            parent=self.styles['Heading3'],
            fontName=self.chinese_bold_font,
            fontSize=14,
            textColor=colors.HexColor('#0056b3'),
            spaceAfter=10,
            spaceBefore=15
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontName=self.chinese_font,
            fontSize=11,
            spaceAfter=6,
            leading=16
        ))
    
    def add_title(self, text):
        self.story.append(Paragraph(text, self.styles['CustomTitle']))
        self.story.append(Spacer(1, 0.2*inch))
    
    def add_heading(self, text):
        self.story.append(Paragraph(text, self.styles['CustomHeading']))
        self.story.append(Spacer(1, 0.1*inch))
    
    def add_sub_heading(self, text):
        self.story.append(Paragraph(text, self.styles['CustomSubHeading']))
        self.story.append(Spacer(1, 0.05*inch))
    
    def add_paragraph(self, text):
        self.story.append(Paragraph(text, self.styles['CustomBody']))
        self.story.append(Spacer(1, 0.05*inch))
    
    def add_table(self, data, headers=None, col_widths=None):
        if headers:
            data = [headers] + data
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0056b3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_bold_font),
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
        ]))
        self.story.append(table)
        self.story.append(Spacer(1, 0.2*inch))
    
    def add_page_break(self):
        self.story.append(PageBreak())
    
    def build(self):
        self.doc.build(self.story)

def generate_test_results_pdf(results, output_path=None):
    if output_path is None:
        output_path = f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    
    pdf = PDFGenerator(output_path)
    
    pdf.add_title('AI模型性能测试报告')
    pdf.add_paragraph(f'生成时间: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}')
    pdf.add_paragraph(f'报告编号: {datetime.now().strftime("%Y%m%d%H%M%S")}')
    
    if isinstance(results, list) and len(results) > 1:
        pdf.add_heading('多模型性能对比')
        
        comparison_data = []
        comparison_headers = ['模型', 'TTFT P90 (ms)', 'Token吞吐', '成功率', '延迟最大值', '延迟P99', '延迟最小值']
        
        for result in results:
            comparison_data.append([
                result['model_provider'],
                f"{result['ttft_stats']['p90']:.2f}",
                f"{result['tokens_throughput_stats']['avg']:.2f}",
                f"{100 - result['error_rate']:.2f}%",
                f"{result['latency_stats']['max']:.2f}",
                f"{result['latency_stats']['p99']:.2f}",
                f"{result['latency_stats']['min']:.2f}"
            ])
        
        pdf.add_table(comparison_data, comparison_headers)
        pdf.add_page_break()
        
        for idx, result in enumerate(results, 1):
            pdf.add_heading(f'模型 {idx} - {result["model_provider"]}')
            
            pdf.add_sub_heading('测试概览')
            overview_data = [
                ['总测试次数', str(result['total_tests'])],
                ['成功次数', str(result['success_count'])],
                ['失败次数', str(result['error_count'])],
                ['错误率', f"{result['error_rate']:.2f}%"]
            ]
            pdf.add_table(overview_data, col_widths=[2.5*inch, 2.5*inch])
            
            pdf.add_sub_heading('延迟性能指标 (ms)')
            latency_stats = result['latency_stats']
            latency_data = [
                ['平均值', f"{latency_stats['avg']:.2f}"],
                ['P90', f"{latency_stats['p90']:.2f}"],
                ['P99', f"{latency_stats['p99']:.2f}"],
                ['最小值', f"{latency_stats['min']:.2f}"],
                ['最大值', f"{latency_stats['max']:.2f}"]
            ]
            pdf.add_table(latency_data, col_widths=[2.5*inch, 2.5*inch])
            
            pdf.add_sub_heading('TTFT指标 (ms)')
            ttft_stats = result['ttft_stats']
            ttft_data = [
                ['平均值', f"{ttft_stats['avg']:.2f}"],
                ['P90', f"{ttft_stats['p90']:.2f}"],
                ['P99', f"{ttft_stats['p99']:.2f}"],
                ['最小值', f"{ttft_stats['min']:.2f}"],
                ['最大值', f"{ttft_stats['max']:.2f}"]
            ]
            pdf.add_table(ttft_data, col_widths=[2.5*inch, 2.5*inch])
            
            pdf.add_sub_heading('Token吞吐指标 (tokens/s)')
            throughput_stats = result['tokens_throughput_stats']
            throughput_data = [
                ['平均值', f"{throughput_stats['avg']:.2f}"],
                ['P90', f"{throughput_stats['p90']:.2f}"],
                ['P99', f"{throughput_stats['p99']:.2f}"],
                ['最小值', f"{throughput_stats['min']:.2f}"],
                ['最大值', f"{throughput_stats['max']:.2f}"]
            ]
            pdf.add_table(throughput_data, col_widths=[2.5*inch, 2.5*inch])
            
            pdf.add_sub_heading('总Token数指标')
            tokens_stats = result['total_tokens_stats']
            tokens_data = [
                ['平均值', f"{tokens_stats['avg']:.2f}"],
                ['P90', f"{tokens_stats['p90']:.2f}"],
                ['P99', f"{tokens_stats['p99']:.2f}"],
                ['最小值', f"{tokens_stats['min']:.2f}"],
                ['最大值', f"{tokens_stats['max']:.2f}"]
            ]
            pdf.add_table(tokens_data, col_widths=[2.5*inch, 2.5*inch])
            
            if idx < len(results):
                pdf.add_page_break()
    else:
        if isinstance(results, list):
            result = results[0]
        else:
            result = results
        
        pdf.add_heading(f'模型性能测试 - {result["model_provider"]}')
        
        pdf.add_sub_heading('测试概览')
        overview_data = [
            ['总测试次数', str(result['total_tests'])],
            ['成功次数', str(result['success_count'])],
            ['失败次数', str(result['error_count'])],
            ['错误率', f"{result['error_rate']:.2f}%"]
        ]
        pdf.add_table(overview_data, col_widths=[2.5*inch, 2.5*inch])
        
        pdf.add_sub_heading('延迟性能指标 (ms)')
        latency_stats = result['latency_stats']
        latency_data = [
            ['平均值', f"{latency_stats['avg']:.2f}"],
            ['P90', f"{latency_stats['p90']:.2f}"],
            ['P99', f"{latency_stats['p99']:.2f}"],
            ['最小值', f"{latency_stats['min']:.2f}"],
            ['最大值', f"{latency_stats['max']:.2f}"]
        ]
        pdf.add_table(latency_data, col_widths=[2.5*inch, 2.5*inch])
        
        pdf.add_sub_heading('TTFT指标 (ms)')
        ttft_stats = result['ttft_stats']
        ttft_data = [
            ['平均值', f"{ttft_stats['avg']:.2f}"],
            ['P90', f"{ttft_stats['p90']:.2f}"],
            ['P99', f"{ttft_stats['p99']:.2f}"],
            ['最小值', f"{ttft_stats['min']:.2f}"],
            ['最大值', f"{ttft_stats['max']:.2f}"]
        ]
        pdf.add_table(ttft_data, col_widths=[2.5*inch, 2.5*inch])
        
        pdf.add_sub_heading('Token吞吐指标 (tokens/s)')
        throughput_stats = result['tokens_throughput_stats']
        throughput_data = [
            ['平均值', f"{throughput_stats['avg']:.2f}"],
            ['P90', f"{throughput_stats['p90']:.2f}"],
            ['P99', f"{throughput_stats['p99']:.2f}"],
            ['最小值', f"{throughput_stats['min']:.2f}"],
            ['最大值', f"{throughput_stats['max']:.2f}"]
        ]
        pdf.add_table(throughput_data, col_widths=[2.5*inch, 2.5*inch])
        
        pdf.add_sub_heading('总Token数指标')
        tokens_stats = result['total_tokens_stats']
        tokens_data = [
            ['平均值', f"{tokens_stats['avg']:.2f}"],
            ['P90', f"{tokens_stats['p90']:.2f}"],
            ['P99', f"{tokens_stats['p99']:.2f}"],
            ['最小值', f"{tokens_stats['min']:.2f}"],
            ['最大值', f"{tokens_stats['max']:.2f}"]
        ]
        pdf.add_table(tokens_data, col_widths=[2.5*inch, 2.5*inch])
    
    pdf.add_page_break()
    pdf.add_heading('报告说明')
    pdf.add_paragraph('本报告由AI模型性能拨测系统自动生成。')
    pdf.add_paragraph('指标说明：')
    pdf.add_paragraph('- TTFT (Time to First Token): 从发送请求到收到第一个token的时间')
    pdf.add_paragraph('- Token吞吐: 每秒生成的token数量')
    pdf.add_paragraph('- 延迟: 从发送请求到收到完整响应的时间')
    pdf.add_paragraph('- P90/P99: 90%/99%的请求延迟低于此值')
    
    pdf.build()
    
    return output_path
