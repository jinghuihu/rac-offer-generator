import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
import fitz  # PyMuPDF
from paddleocr import PaddleOCR
import os
import tempfile
import re
from typing import Dict, Tuple

# ------------------------------
# 1. 初始化配置（字体、OCR、模板）
# ------------------------------
class OfferGenerator:
    def __init__(self):
        # OCR初始化（支持中英文+数字）
        self.ocr = PaddleOCR(
            use_angle_cls=True, 
            lang='ch', 
            det_db_unclip_ratio=1.6,  # 优化中文识别精度
            rec_char_dict_path='./ppocr_keys_v1.txt'  # 确保包含英文和数字
        )
        
        # 字体配置（优先使用系统字体，避免路径问题）
        self.fonts = {
            'large': ImageFont.truetype("simhei.ttf", 72) if os.path.exists("simhei.ttf") else ImageFont.load_default(size=72),
            'medium': ImageFont.truetype("simhei.ttf", 48) if os.path.exists("simhei.ttf") else ImageFont.load_default(size=48),
            'small': ImageFont.truetype("simhei.ttf", 36) if os.path.exists("simhei.ttf") else ImageFont.load_default(size=36),
            'tiny': ImageFont.truetype("simhei.ttf", 28) if os.path.exists("simhei.ttf") else ImageFont.load_default(size=28)
        }
        
        # 模板配置（严格对应参考图）
        self.templates = {
            # 绿色模板：交互类专业（参考图1、图2）
            'green': {
                'bg_color': (240, 255, 240),  # 浅绿背景
                'accent_color': (0, 100, 0),  # 深绿点缀
                'text_color': (0, 0, 0),      # 黑色文字
                'layout': {
                    'rac_studio': (80, 60),               # 顶部左侧RAC STUDIO
                    'congrats_offer': (400, 150),         # 中间Congratulations/Offer
                    'year_offer': (1000, 120),            # 右侧竖排年份（旋转后位置）
                    'browser_window': (300, 300, 600, 350),# 录取内容截图区域
                    'landscape': (350, 320, 500, 300),    # 蓝天白云山丘插画
                    'to_school': (80, 650),               # 底部TO + 学校
                    'lightning': (80 + 120, 650 + 40)     # 闪电图标位置
                },
                'decoration': [
                    {'type': 'mountain', 'pos': (300, 600), 'size': 200},  # 山脉景观
                    {'type': 'sky', 'pos': (300, 300), 'size': 600}         # 天空背景
                ]
            },
            # 粉色模板：空间类专业（参考图3、图4）
            'pink': {
                'bg_color': (255, 240, 245),  # 浅粉背景
                'accent_color': (200, 0, 100),# 深粉点缀
                'text_color': (0, 0, 0),      # 黑色文字
                'layout': {
                    'rac_studio': (80, 60),               # 顶部左侧RAC STUDIO
                    'congrats_offer': (900, 150),         # 右侧Congratulations/Offer
                    'year_offer': (1000, 120),            # 右侧竖排年份
                    'folder_area': (200, 300, 800, 200),  # 文件夹区域
                    'to_name': (80, 650),                 # 底部TO + 姓名
                    'qr_code': (1000, 600)                # 右下角二维码
                },
                'decoration': [
                    {'type': 'folder', 'pos': (200, 300), 'size': (800, 200)},  # 文件夹装饰
                    {'type': 'qr_border', 'pos': (1000, 600), 'size': 120}       # 二维码边框
                ]
            }
        }

    # ------------------------------
    # 2. 智能提取Offer关键信息（核心！无需人工输入）
    # ------------------------------
    def extract_info(self, file_path: str) -> Dict:
        """从PDF/图片中提取姓名、专业、学校、年份"""
        info = {'name': '', 'program': '', 'school': '', 'year': ''}

        # 处理PDF文件（爱丁堡录取通知书多为PDF）
        if file_path.lower().endswith('.pdf'):
            doc = fitz.open(file_path)
            text = "
".join([page.get_text() for page in doc])
            doc.close()

            # 正则匹配关键信息（适配爱丁堡录取信的固定表述）
            info['name'] = re.search(r'[A-Za-z]\w+同学', text) or re.search(r'[P|L]同学', text)  # 匹配P/L同学
            info['program'] = re.search(r'(MSc \w+ Media|MSc City Planning)', text)  # 匹配专业名称
            info['school'] = re.search(r'(The University of Edinburgh|爱丁堡大学)', text)
            info['year'] = re.search(r'\d{4}', text)  # 匹配年份（如2025/2026）

        # 处理图片文件（如offer截图）
        else:
            result = self.ocr.ocr(file_path, cls=True)
            if result and result[0]:
                full_text = "
".join([line[1][0] for line in result[0]])
                info['name'] = re.search(r'[A-Za-z]\w+同学|[P|L]同学', full_text)
                info['program'] = re.search(r'(MSc \w+ Media|MSc City Planning)', full_text)
                info['school'] = re.search(r'(The University of Edinburgh|爱丁堡大学)', full_text)
                info['year'] = re.search(r'\d{4}', full_text)

        # 处理未识别的情况（默认值）
        info = {k: v.group().strip() if v else '未识别' for k, v in info.items()}
        return info

    # ------------------------------
    # 3. 生成模板背景（带参考图的装饰元素）
    # ------------------------------
    def create_bg(self, offer_type: str) -> Image.Image:
        """根据模板类型生成带装饰的背景"""
        config = self.templates[offer_type]
        bg = Image.new('RGB', (1200, 800), config['bg_color'])
        draw = ImageDraw.Draw(bg)

        # 添加装饰元素（严格对应参考图）
        for deco in config['decoration']:
            if offer_type == 'green':
                if deco['type'] == 'mountain':
                    # 绘制绿色山脉（参考图1的山丘）
                    draw.polygon([
                        deco['pos'][0], deco['pos'][1],
                        deco['pos'][0] + deco['size']//2, deco['pos'][1] - 100,
                        deco['pos'][0] + deco['size'], deco['pos'][1]
                    ], fill=(150, 200, 150))
                elif deco['type'] == 'sky':
                    # 绘制浅蓝天空（参考图1的天空）
                    draw.rectangle([deco['pos'][0], deco['pos'][1], 
                                   deco['pos'][0] + deco['size'], deco['pos'][1] + 200], 
                                  fill=(135, 206, 235))
            else:  # pink模板
                if deco['type'] == 'folder':
                    # 绘制文件夹区域（参考图3的文件夹）
                    draw.rectangle(deco['pos'] + (deco['pos'][0]+deco['size'][0], deco['pos'][1]+deco['size'][1]), 
                                  fill=(255, 250, 240), outline=(200, 180, 180))
                elif deco['type'] == 'qr_border':
                    # 绘制二维码边框（参考图3、4的二维码）
                    draw.rectangle(deco['pos'] + (deco['pos'][0]+deco['size'], deco['pos'][1]+deco['size']), 
                                  outline=config['accent_color'], width=2)

        return bg

    # ------------------------------
    # 4. 生成最终Offer图（布局1:1匹配参考图）
    # ------------------------------
    def generate_offer(self, file_path: str, offer_type: str) -> Image.Image:
        """核心生成函数：提取信息+组合模板"""
        info = self.extract_info(file_path)
        config = self.templates[offer_type]
        bg = self.create_bg(offer_type)
        draw = ImageDraw.Draw(bg)

        try:
            # 加载字体（兼容不同系统）
            font_large = self.fonts['large']
            font_medium = self.fonts['medium']
            font_small = self.fonts['small']
        except:
            # 若字体缺失，使用默认字体
            font_large = ImageFont.load_default(size=72)
            font_medium = ImageFont.load_default(size=48)
            font_small = ImageFont.load_default(size=36)

        # ------------------------------
        # 绿色模板：交互类专业（参考图1、2）
        # ------------------------------
        if offer_type == 'green':
            # 1. 顶部RAC STUDIO
            draw.text(config['layout']['rac_studio'], "RAC STUDIO", 
                     fill=config['text_color'], font=font_medium)
            # 2. 中间Congratulations/Offer
            draw.multiline_text(config['layout']['congrats_offer'], 
                               "Congratulations!
Offer", 
                               fill=config['accent_color'], font=font_large, align='center')
            # 3. 右侧竖排年份（旋转90度）
            year_text = f"{info['year']} OFFER"
            rotated_year = Image.new('RGBA', (300, 100), (0,0,0,0))
            rt_draw = ImageDraw.Draw(rotated_year)
            rt_draw.text((0,0), year_text, fill=config['text_color'], font=font_medium)
            rotated = rotated_year.rotate(90, expand=1)
            bg.paste(rotated, (config['layout']['year_offer'][0] - rotated.width//2, 
                              config['layout']['year_offer'][1] - rotated.height//2), rotated)
            # 4. 录取内容截图区域（参考图2的录取信）
            draw.rectangle(config['layout']['browser_window'], outline=config['accent_color'], width=2)
            # 5. 蓝天白云山丘插画（参考图1的景观）
            draw.rectangle(config['layout']['landscape'], fill=(135, 206, 235))
            draw.polygon([
                config['layout']['landscape'][0], config['layout']['landscape'][3],
                config['layout']['landscape'][0] + config['layout']['landscape'][2]//2, config['layout']['landscape'][1],
                config['layout']['landscape'][0] + config['layout']['landscape'][2], config['layout']['landscape'][3]
            ], fill=(150, 200, 150))
            # 6. 底部TO + 学校 + 闪电图标
            draw.text(config['layout']['to_school'], f"TO
{info['school']}", 
                     fill=config['text_color'], font=font_medium, spacing=10)
            draw.polygon([config['layout']['lightning'][0], config['layout']['lightning'][1],
                         config['layout']['lightning'][0] + 20, config['layout']['lightning'][1],
                         config['layout']['lightning'][0] + 10, config['layout']['lightning'][1] + 20], 
                         fill=config['accent_color'])

        # ------------------------------
        # 粉色模板：空间类专业（参考图3、4）
        # ------------------------------
        else:
            # 1. 顶部RAC STUDIO
            draw.text(config['layout']['rac_studio'], "RAC STUDIO", 
                     fill=config['text_color'], font=font_medium)
            # 2. 右侧Congratulations/Offer
            draw.multiline_text(config['layout']['congrats_offer'], 
                               "Congratulations!
Offer", 
                               fill=config['accent_color'], font=font_large, align='right')
            # 3. 右侧竖排年份
            year_text = f"{info['year']} OFFER"
            rotated_year = Image.new('RGBA', (300, 100), (0,0,0,0))
            rt_draw = ImageDraw.Draw(rotated_year)
            rt_draw.text((0,0), year_text, fill=config['text_color'], font=font_medium)
            rotated = rotated_year.rotate(90, expand=1)
            bg.paste(rotated, (config['layout']['year_offer'][0] - rotated.width//2, 
                              config['layout']['year_offer'][1] - rotated.height//2), rotated)
            # 4. 文件夹区域（参考图3的文件夹）
            draw.rectangle(config['layout']['folder_area'], fill=(255, 250, 240), outline=(200, 180, 180))
            # 5. 底部TO + 姓名
            draw.text(config['layout']['to_name'], f"TO
{info['name']}", 
                     fill=config['text_color'], font=font_medium, spacing=10)
            # 6. 右下角二维码（参考图3、4的二维码）
            draw.rectangle(config['layout']['qr_code'] + (config['layout']['qr_code'][0]+120, config['layout']['qr_code'][1]+120), 
                          outline=config['accent_color'], width=2)
            draw.text((config['layout']['qr_code'][0], config['layout']['qr_code'][1]+130), 
                     "RAC STUDIO", fill=config['accent_color'], font=font_tiny)

        return bg

# ------------------------------
# 5. Streamlit Web界面（一键生成）
# ------------------------------
def main():
    st.set_page_config(
        page_title="RAC Offer生成器", 
        layout="wide", 
        page_icon="🎓",
        menu_items={
            'About': "自动从爱丁堡录取信中提取信息，生成RAC风格Offer展示图"
        }
    )
    
    st.title("✨ RAC Offer展示图一键生成器")
    st.caption("上传爱丁堡录取信（PDF/图片），自动提取信息生成专业展示图")
    
    # 初始化生成器
    if 'generator' not in st.session_state:
        st.session_state.generator = OfferGenerator()
    
    # 侧边栏：选择模板类型
    st.sidebar.header("⚙️ 模板设置")
    offer_type = st.sidebar.selectbox(
        "选择专业类型", 
        ["green", "pink"], 
        format_func=lambda x: "交互类专业（绿色）" if x == "green" else "空间类专业（粉色）"
    )
    
    # 文件上传
    uploaded_files = st.file_uploader(
        "上传爱丁堡录取信", 
        type=['pdf', 'jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        st.subheader("生成结果")
        download_links = []
        
        for idx, file in enumerate(uploaded_files):
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=file.name.split('.')[-1]) as tmp:
                tmp.write(file.getvalue())
                tmp_path = tmp.name
            
            try:
                # 生成Offer图
                result_img = st.session_state.generator.generate_offer(tmp_path, offer_type)
                
                # 显示原文件+生成结果
                col1, col2 = st.columns(2, gap="small")
                with col1:
                    st.subheader(f"原始文件 #{idx+1}")
                    st.image(file, use_column_width=True)
                with col2:
                    st.subheader(f"生成结果 #{idx+1}")
                    st.image(result_img, use_column_width=True)
                
                # 提供下载
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as out:
                    result_img.save(out.name, 'PNG')
                    with open(out.name, 'rb') as f:
                        st.download_button(
                            label=f"⬇️ 下载生成图 #{idx+1}",
                            data=f,
                            file_name=f"RAC_Offer_{idx+1}.png",
                            mime="image/png",
                            key=f"download_{idx}"
                        )
                
                # 清理临时文件
                os.unlink(tmp_path)
                os.unlink(out.name)
            
            except Exception as e:
                st.error(f"处理文件 {file.name} 失败: {str(e)}")
        
        st.success(f"成功处理 {len(uploaded_files)} 个文件！")

if __name__ == "__main__":
    main()

