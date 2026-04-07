#!/usr/bin/env python3
"""
OpenRouter Weekly Rankings Fetcher
获取OpenRouter周榜数据作为AI产业链信号
"""

import json
import re
from playwright.sync_api import sync_playwright
from datetime import datetime
from pathlib import Path

# 主要厂商映射（全球+中国）
VENDOR_MAP = {
    # 美国
    'openai': 'OpenAI',
    'anthropic': 'Anthropic', 
    'google': 'Google',
    'x-ai': 'xAI',
    'meta': 'Meta',
    'mistral': 'Mistral',
    'cohere': 'Cohere',
    'nvidia': 'NVIDIA',
    # 中国
    'xiaomi': '小米',
    'qwen': '阿里通义',
    'minimax': 'MiniMax',
    'deepseek': 'DeepSeek',
    'z-ai': '智谱AI',
    'moonshotai': '月之暗面',
    'stepfun': '阶跃星辰',
    'baidu': '百度',
    'bytedance': '字节跳动',
}

def parse_rankings(text):
    """从页面文本解析排名数据"""
    lines = text.split('\n')
    rankings = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 匹配排名数字行
        if re.match(r'^\d+\.$', line):
            rank = int(line.replace('.', ''))
            
            if i + 1 < len(lines):
                model = lines[i + 1].strip()
                
                if i + 2 < len(lines) and lines[i + 2].strip() == 'by':
                    if i + 3 < len(lines):
                        vendor = lines[i + 3].strip()
                        
                        tokens = 'N/A'
                        change = 'N/A'
                        if i + 4 < len(lines):
                            token_line = lines[i + 4].strip()
                            token_match = re.match(r'([\d.]+[TB])\s+tokens', token_line)
                            if token_match:
                                tokens = token_match.group(1)
                            
                            if i + 5 < len(lines):
                                change_line = lines[i + 5].strip()
                                if re.match(r'^[\d\-]+%$', change_line) or change_line in ['new']:
                                    change = change_line
                        
                        is_chinese = vendor.lower() in ['xiaomi', 'qwen', 'minimax', 'deepseek', 'z-ai', 'moonshotai', 'stepfun', 'baidu', 'bytedance']
                        
                        rankings.append({
                            'rank': rank,
                            'model': model,
                            'vendor': vendor,
                            'vendor_cn': VENDOR_MAP.get(vendor.lower(), vendor),
                            'is_chinese': is_chinese,
                            'tokens': tokens,
                            'change': change
                        })
                        
                        i += 5
                        continue
        
        i += 1
    
    # 去重并排序
    seen = set()
    unique = []
    for r in rankings:
        key = f"{r['rank']}-{r['model']}-{r['vendor']}"
        if key not in seen:
            seen.add(key)
            unique.append(r)
    
    return sorted(unique, key=lambda x: x['rank'])

def fetch_openrouter_rankings():
    """
    获取OpenRouter周榜数据
    需要Playwright和Chromium
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("🌐 加载OpenRouter Rankings...")
        page.goto("https://openrouter.ai/rankings")
        page.wait_for_timeout(3000)
        
        # 点击Show more加载更多
        for _ in range(4):
            try:
                button = page.locator('text=Show more').first
                if button.is_visible():
                    button.click()
                    page.wait_for_timeout(1500)
            except:
                break
        
        text = page.inner_text('body')
        browser.close()
        
        return parse_rankings(text)

def generate_market_signals(rankings):
    """
    生成市场信号摘要
    用于股票分析产业链数据输入
    """
    # 按厂商汇总（全球）
    vendor_stats = {}
    for r in rankings:
        v = r['vendor']
        if v not in vendor_stats:
            vendor_stats[v] = {
                'count': 0,
                'tokens_t': 0,
                'top_rank': 999,
                'models': [],
                'is_chinese': r.get('is_chinese', False),
                'vendor_cn': r.get('vendor_cn', v)
            }
        
        vendor_stats[v]['count'] += 1
        vendor_stats[v]['models'].append(r['model'])
        
        # 解析tokens
        try:
            val = float(r['tokens'].replace('T', '').replace('B', ''))
            if 'B' in r['tokens']:
                val = val / 1000
            vendor_stats[v]['tokens_t'] += val
        except:
            pass
        
        # 记录最高排名
        if r['rank'] < vendor_stats[v]['top_rank']:
            vendor_stats[v]['top_rank'] = r['rank']
    
    # 生成信号
    signals = {
        'fetch_time': datetime.now().isoformat(),
        'period': 'weekly',
        'source': 'https://openrouter.ai/rankings',
        'summary': {
            'total_models': len(rankings),
            'chinese_models': len([r for r in rankings if r.get('is_chinese')]),
            'us_models': len([r for r in rankings if r['vendor'].lower() in ['openai', 'anthropic', 'google', 'x-ai', 'meta']]),
        },
        'global_leaderboard': [],
        'insights': []
    }
    
    # 全球厂商排名（按Tokens排序）
    sorted_vendors = sorted(
        vendor_stats.items(), 
        key=lambda x: x[1]['tokens_t'], 
        reverse=True
    )
    
    for vendor, stats in sorted_vendors:
        entry = {
            'vendor': vendor,
            'vendor_cn': stats['vendor_cn'],
            'is_chinese': stats['is_chinese'],
            'model_count': stats['count'],
            'total_tokens_t': round(stats['tokens_t'], 2),
            'top_rank': stats['top_rank'],
            'top_models': stats['models'][:3]
        }
        signals['global_leaderboard'].append(entry)
    
    # 生成洞察
    if sorted_vendors:
        top_vendor = sorted_vendors[0]
        signals['insights'].append(
            f"{top_vendor[1]['vendor_cn']} 以 {top_vendor[1]['tokens_t']:.2f}T tokens 领跑周榜"
        )
        
        # 中美对比
        cn_vendors = [v for v in sorted_vendors if v[1]['is_chinese']]
        us_vendors = [v for v in sorted_vendors if v[0] in ['openai', 'anthropic', 'google', 'x-ai', 'meta', 'nvidia']]
        
        if cn_vendors and us_vendors:
            cn_total = sum(v[1]['tokens_t'] for v in cn_vendors)
            us_total = sum(v[1]['tokens_t'] for v in us_vendors)
            signals['insights'].append(
                f"中美对比: 中国 {cn_total:.2f}T vs 美国 {us_total:.2f}T tokens"
            )
        
        # 增长最快
        growing = [r for r in rankings if r['change'] not in ['N/A', 'new', '0%']]
        if growing:
            top_grower = max(growing, key=lambda x: float(x['change'].replace('%', '').replace('+', '')) if x['change'] not in ['N/A', 'new'] else 0)
            signals['insights'].append(
                f"增长最快: {top_grower['vendor_cn']} {top_grower['model']} ({top_grower['change']})"
            )
    
    return signals

def save_to_skill(data_dir=None):
    """
    保存数据到skill目录
    """
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "data"
    else:
        data_dir = Path(data_dir)
    
    data_dir.mkdir(exist_ok=True)
    
    # 获取数据
    rankings = fetch_openrouter_rankings()
    signals = generate_market_signals(rankings)
    
    # 保存完整排名
    rankings_file = data_dir / "openrouter_rankings.json"
    with open(rankings_file, 'w', encoding='utf-8') as f:
        json.dump({
            'fetch_time': datetime.now().isoformat(),
            'period': 'weekly',
            'rankings': rankings
        }, f, ensure_ascii=False, indent=2)
    
    # 保存信号摘要
    signals_file = data_dir / "openrouter_signals.json"
    with open(signals_file, 'w', encoding='utf-8') as f:
        json.dump(signals, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 数据已保存:")
    print(f"  - 完整排名: {rankings_file}")
    print(f"  - 市场信号: {signals_file}")
    
    return signals, rankings

if __name__ == "__main__":
    import sys
    
    # 检查playwright是否可用
    try:
        import playwright
    except ImportError:
        print("❌ 需要安装Playwright: pip install playwright")
        print("   然后运行: playwright install chromium")
        sys.exit(1)
    
    # 获取并保存数据
    signals, rankings = save_to_skill()
    
    # 打印TOP 20模型排名（类似之前的格式）
    print(f"\n{'='*80}")
    print("📊 OpenRouter 周榜 TOP 20")
    print(f"{'='*80}")
    print(f"{'排名':<5} {'厂商':<15} {'模型':<38} {'Tokens':<10} {'变化':<8}")
    print(f"{'-'*80}")
    
    for r in rankings[:20]:
        print(f"{r['rank']:<5} {r['vendor_cn']:<15} {r['model'][:37]:<38} {r['tokens']:<10} {r['change']:<8}")
    
    # 打印厂商排行
    print(f"\n{'='*60}")
    print("📈 厂商排行 (按Tokens)")
    print(f"{'-'*60}")
    print(f"{'排名':<5} {'厂商':<15} {'Tokens':<12} {'模型数':<8} {'最高排名':<8}")
    print(f"{'-'*60}")
    
    for i, v in enumerate(signals['global_leaderboard'][:10], 1):
        print(f"{i:<5} {v['vendor_cn']:<15} {v['total_tokens_t']:<12.2f} {v['model_count']:<8} #{v['top_rank']:<7}")
    
    print(f"\n关键洞察:")
    for insight in signals['insights']:
        print(f"  • {insight}")
