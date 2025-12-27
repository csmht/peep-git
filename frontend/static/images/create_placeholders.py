"""
创建占位图片用于测试
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_gradient_background(width, height, color1, color2, output_path):
    """创建渐变背景图片"""
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)

    # 创建垂直渐变
    for y in range(height):
        r = int(color1[0] + (color2[0] - color1[0]) * y / height)
        g = int(color1[1] + (color2[1] - color1[1]) * y / height)
        b = int(color1[2] + (color2[2] - color1[2]) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 添加文字标识
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()

    text = os.path.basename(output_path).replace('.png', '').replace('.gif', '').upper()
    # 使用 getbbox 获取文字边界框
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(position, text, fill='white', font=font)

    img.save(output_path)
    print(f'[OK] Created: {output_path} ({width}x{height})')

def create_loading_animation(output_path):
    """创建简单的加载动画(单帧)"""
    size = 100
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # 绘制心形
    center_x, center_y = size // 2, size // 2
    heart_size = 30

    # 心形由两个圆和一个三角形组成
    draw.ellipse([center_x - heart_size, center_y - heart_size,
                  center_x, center_y], fill=(255, 105, 180, 255))
    draw.ellipse([center_x, center_y - heart_size,
                  center_x + heart_size, center_y], fill=(255, 105, 180, 255))

    # 三角形部分
    points = [
        (center_x - heart_size, center_y - heart_size // 2),
        (center_x + heart_size, center_y - heart_size // 2),
        (center_x, center_y + heart_size)
    ]
    draw.polygon(points, fill=(255, 105, 180, 255))

    img.save(output_path.replace('.gif', '.png'))
    print(f'[OK] Created: {output_path.replace(".gif", ".png")} (100x100, heart shape)')

def main():
    output_dir = 'frontend/static/images/characters'
    os.makedirs(output_dir, exist_ok=True)

    print('Starting placeholder image creation...\n')

    # 1. Banner background - pink gradient
    create_gradient_background(
        1200, 200,
        (255, 182, 193),  # Light pink
        (255, 105, 180),  # Deep pink
        os.path.join(output_dir, 'banner-bg.png')
    )

    # 2. Loading animation - heart shape
    create_loading_animation(os.path.join(output_dir, 'loading.gif'))

    # 3. Dashboard background - light pink
    create_gradient_background(
        1400, 800,
        (255, 228, 225),  # Misty rose
        (255, 182, 193),  # Light pink
        os.path.join(output_dir, 'dashboard-bg.png')
    )

    print('\nAll placeholder images created successfully!')
    print(f'Images saved to: {output_dir}')

if __name__ == '__main__':
    main()
