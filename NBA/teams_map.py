from PIL import Image, ImageDraw, ImageFont
import os
import matplotlib.font_manager as fm

# 阿里扎效力过的球队及时间顺序（2004-2022）
ariza_teams = [
    {"team": "New York Knicks", "years": "2004-2006"},
    {"team": "Orlando Magic", "years": "2006-2007"},
    {"team": "Los Angeles Lakers", "years": "2007-2009"},
    {"team": "Houston Rockets", "years": "2009-2010"},
    {"team": "New Orleans Pelicans", "years": "2010-2012"},
    {"team": "Washington Wizards", "years": "2012-2014"},
    {"team": "Houston Rockets", "years": "2014-2018"},
    {"team": "Phoenix Suns", "years": "2018-2019"},
    {"team": "Washington Wizards", "years": "2019-2020"},
    {"team": "Portland Trail Blazers", "years": "2020-2021"},
    {"team": "Miami Heat", "years": "2020-2021"},
    {"team": "Los Angeles Lakers", "years": "2021-2022"}
]

# 创建输出图像（使用RGBA模式支持透明度）
width = 1000  # 设置宽度为1000px
height = 800  # 保持高度不变
img = Image.new('RGBA', (width, height), color=(255, 255, 255, 255))  # 白色背景
draw = ImageDraw.Draw(img)

# 加载字体
try:
    font = ImageFont.truetype("arial.ttf", 24)
except:
    font = ImageFont.load_default()

# 计算每个logo的位置
logo_size = 100
border_width = 2  # 边框宽度
spacing = 150
start_x = 100
start_y = 100  # 起始y坐标
logos_per_row = 6  # 每行最多6个logo

# 加载并绘制每个球队logo
for i, team_info in enumerate(ariza_teams):
    team = team_info["team"]
    
    # 计算当前logo的位置
    row = i // logos_per_row
    col = i % logos_per_row
    x_pos = start_x + col * spacing
    y_pos = start_y + row * (logo_size + 100)  # 增加行间距
    
    # 查找logo文件
    logo_path = None
    for ext in ['.png', '.svg', '.jpg']:
        possible_path = os.path.join("nba_logos", team.replace(" ", "_") + ext)
        if os.path.exists(possible_path):
            logo_path = possible_path
            break
    
    if logo_path:
        try:
            # 打开并调整logo大小，保持透明度
            logo = Image.open(logo_path).convert("RGBA")
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # 创建圆形遮罩
            mask = Image.new("L", (logo_size, logo_size), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, logo_size, logo_size), fill=255)
            
            # 创建白色背景
            background = Image.new('RGBA', (logo_size, logo_size), (255, 255, 255, 255))
            background.paste(logo, (0, 0), mask)
            
            # 绘制灰色边框
            border = Image.new('RGBA', (logo_size + border_width*2, logo_size + border_width*2), (200, 200, 200, 255))
            border_draw = ImageDraw.Draw(border)
            border_draw.ellipse((0, 0, logo_size + border_width*2, logo_size + border_width*2), fill=(200, 200, 200, 255))
            
            # 将logo粘贴到带边框的背景上
            border.paste(background, (border_width, border_width), background)
            
            # 粘贴到主图像
            img.paste(border, (x_pos - border_width, y_pos - logo_size//2 - border_width), border)
            
            # 如果不是最后一个球队，绘制箭头
            if i < len(ariza_teams) - 1:
                next_row = (i + 1) // logos_per_row
                next_col = (i + 1) % logos_per_row
                
                if row == next_row:  # 同一行
                    # 水平箭头
                    arrow_start = (x_pos + logo_size + 10, y_pos)
                    arrow_end = (x_pos + spacing - 10, y_pos)
                    
                    # 绘制红色箭头主体
                    draw.line([arrow_start, arrow_end], fill=(255, 0, 0), width=3)
                    
                    # 绘制红色箭头头部
                    arrow_head_length = 15
                    arrow_head_width = 8
                    draw.polygon([
                        (arrow_end[0] - arrow_head_length, arrow_end[1] - arrow_head_width),
                        (arrow_end[0], arrow_end[1]),
                        (arrow_end[0] - arrow_head_length, arrow_end[1] + arrow_head_width)
                    ], fill=(255, 0, 0))
                else:  # 换行
                    # 垂直箭头（从右到左）
                    arrow_start = (x_pos + logo_size//2, y_pos + logo_size//2)
                    arrow_end = (x_pos + logo_size//2, y_pos + logo_size//2 + 50)
                    
                    # 绘制红色箭头主体
                    draw.line([arrow_start, arrow_end], fill=(255, 0, 0), width=3)
                    
                    # 绘制红色箭头头部
                    arrow_head_length = 15
                    arrow_head_width = 8
                    draw.polygon([
                        (arrow_end[0] - arrow_head_width, arrow_end[1] - arrow_head_length),
                        (arrow_end[0], arrow_end[1]),
                        (arrow_end[0] + arrow_head_width, arrow_end[1] - arrow_head_length)
                    ], fill=(255, 0, 0))
                
        except Exception as e:
            print(f"无法处理 {team} 的logo: {str(e)}")
    else:
        print(f"未找到 {team} 的logo文件")

# 保存结果（使用PNG格式以保持透明度）
output_path = "ariza_career_timeline.png"
img.save(output_path, "PNG")
print(f"时间轴图已保存到 {output_path}")

# 显示结果（可选）
img.show()