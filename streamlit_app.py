import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os
import re

class OfferGenerator:
    def __init__(self):
        self.templates = {
            'green': {
                'bg_color': (240, 255, 240),
                'accent_color': (0, 100, 0),
                'text_color': (0, 0, 0)
            },
            'pink': {
                'bg_color': (255, 240, 245),
                'accent_color': (200, 0, 100),
                'text_color': (0, 0, 0)
            }
        }
    
    def create_offer_image(self, offer_type, name, school, year):
        """创建Offer展示图片"""
        config = self.templates[offer_type]
        img = Image.new('RGB', (1200, 800), config['bg_color'])
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("arial.ttf", 72)
            font_medium = ImageFont.truetype("arial.ttf", 48)
            font_small = ImageFont.truetype("arial.ttf", 36)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        if offer_type == 'green':
            draw.text((80, 60), "RAC STUDIO", fill=config['text_color'], font=font_medium)
            draw.text((400, 150), "Congratulations!\nOffer", fill=config['accent_color'], 
                     font=font_large, align='center')
            
            year_text = f"{year} OFFER"
            text_img = Image.new('RGBA', (300, 100), (255, 255, 255, 0))
            text_draw = ImageDraw.Draw(text_img)
            text_draw.text((0, 0), year_text, fill=config['text_color'], font=font_medium)
            rotated = text_img.rotate(90, expand=1)
            img.paste(rotated, (1000, 120), rotated)
            
            draw.text((80, 650), f"TO\n{school}", fill=config['text_color'], font=font_medium)
            
        else:
            draw.text((80, 60), "RAC STUDIO", fill=config['text_color'], font=font_medium)
            draw.text((900, 150), "Congratulations!\nOffer", fill=config['accent_color'], 
                     font=font_large, align='right')
            
            year_text = f"{year} OFFER"
            text_img = Image.new('RGBA', (300, 100), (255, 255, 255, 0))
            text_draw = ImageDraw.Draw(text_img)
            text_draw.text((0, 0), year_text, fill=config['text_color'], font=font_medium)
            rotated = text_img.rotate(90, expand=1)
            img.paste(rotated, (1000, 120), rotated)
            
            draw.text((80, 650), f"TO\n{name}", fill=config['text_color'], font=font_medium)
            
            draw.rectangle([1000, 600, 1120, 720], outline=config['accent_color'], width=2)
            draw.text((1000, 730), "RAC STUDIO", fill=config['accent_color'], font=font_small)
        
        return img

def main():
    st.set_page_config(
        page_title="RAC Offer生成器",
        layout="wide",
        page_icon="🎓"
    )
    
    st.title("✨ RAC Offer展示图生成器")
    
    if 'generator' not in st.session_state:
        st.session_state.generator = OfferGenerator()
    
    with st.sidebar:
        st.header("模板设置")
        offer_type = st.selectbox(
            "选择专业类型",
            ["green", "pink"],
            format_func=lambda x: "交互类专业（绿色）" if x == "green" else "空间类专业（粉色）"
        )
        
        st.header("填写信息")
        name = st.text_input("姓名", "优秀学员")
        school = st.text_input("学校", "爱丁堡大学")
        year = st.text_input("年份", "2025")
    
    if st.button("生成展示图", type="primary"):
        with st.spinner("正在生成图片..."):
            try:
                result_image = st.session_state.generator.create_offer_image(offer_type, name, school, year)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("生成结果")
                    st.image(result_image, use_column_width=True)
                
                with col2:
                    st.subheader("下载")
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                        result_image.save(tmp_file.name, 'PNG')
                        with open(tmp_file.name, 'rb') as file:
                            st.download_button(
                                label="下载展示图",
                                data=file,
                                file_name=f"RAC_Offer_{year}.png",
                                mime="image/png"
                            )
                
            except Exception as e:
                st.error(f"生成失败: {str(e)}")

if __name__ == "__main__":
    main()
