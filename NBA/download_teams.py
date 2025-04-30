import os
import requests
from bs4 import BeautifulSoup

# 创建保存图片的目录
if not os.path.exists('nba_logos'):
    os.makedirs('nba_logos')

# NBA球队列表及其对应的缩写
nba_teams = {
    'ATL': 'Atlanta Hawks',
    'BOS': 'Boston Celtics',
    'BKN': 'Brooklyn Nets',
    'CHA': 'Charlotte Hornets',
    'CHI': 'Chicago Bulls',
    'CLE': 'Cleveland Cavaliers',
    'DAL': 'Dallas Mavericks',
    'DEN': 'Denver Nuggets',
    'DET': 'Detroit Pistons',
    'GSW': 'Golden State Warriors',
    'HOU': 'Houston Rockets',
    'IND': 'Indiana Pacers',
    'LAC': 'Los Angeles Clippers',
    'LAL': 'Los Angeles Lakers',
    'MEM': 'Memphis Grizzlies',
    'MIA': 'Miami Heat',
    'MIL': 'Milwaukee Bucks',
    'MIN': 'Minnesota Timberwolves',
    'NO': 'New Orleans Pelicans',
    'NYK': 'New York Knicks',
    'OKC': 'Oklahoma City Thunder',
    'ORL': 'Orlando Magic',
    'PHI': 'Philadelphia 76ers',
    'PHX': 'Phoenix Suns',
    'POR': 'Portland Trail Blazers',
    'SAC': 'Sacramento Kings',
    'SAS': 'San Antonio Spurs',
    'TOR': 'Toronto Raptors',
    'UTAH': 'Utah Jazz',
    'WAS': 'Washington Wizards'
}

def download_logos():
    base_url = "https://a.espncdn.com/i/teamlogos/nba/500/{}.png"

    for team_abbr, team_name in nba_teams.items():
        try:
            # 构造图片URL
            logo_url = base_url.format(team_abbr)
            
            # 发送HTTP请求
            response = requests.get(logo_url, stream=True)
            response.raise_for_status()
            
            # 保存图片
            filename = f"nba_logos/{team_name.replace(' ', '_')}.png"
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            
            print(f"下载成功: {team_name} ({team_abbr})")
            
        except Exception as e:
            print(f"下载失败 {team_name} ({team_abbr}): {str(e)}")

if __name__ == "__main__":
    print("开始下载NBA球队队标...")
    download_logos()
    print("下载完成！")