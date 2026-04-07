/**
 * 数字人才市场 - 股票分析 Web API (Node.js)
 * 
 * 提供 REST API 接口，通过调用 Python 版股票分析引擎执行分析
 */

const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = 8000;

// 中间件
app.use(cors());
app.use(express.json());

// 股票分析引擎路径
const PYTHON_PATH = '/usr/bin/python3';
const ANALYZER_PATH = path.join(__dirname, '../../agents/stock_analyst.py');
// src/ 目录是 Python 模块根目录
const SRC_PATH = path.join(__dirname, '../../');  // = /root/projects/openclaw-talent-link/src/

// ============ 工具函数 ============

function runPython(script, args) {
    return new Promise((resolve, reject) => {
        const env = {
            PYTHONPATH: SRC_PATH,
            PATH: process.env.PATH
        };
        const proc = spawn(PYTHON_PATH, [script, ...args], {
            cwd: SRC_PATH,
            env: env
        });
        
        let stdout = '';
        let stderr = '';
        
        proc.stdout.on('data', (data) => { stdout += data.toString(); });
        proc.stderr.on('data', (data) => { stderr += data.toString(); });
        
        proc.on('close', (code) => {
            if (code !== 0) {
                reject(new Error(stderr || `Exit code: ${code}`));
            } else {
                // 过滤掉非JSON行（进度信息）
                const lines = stdout.split('\n');
                const jsonStart = lines.findIndex(l => l.trim().startsWith('{'));
                if (jsonStart >= 0) {
                    const jsonOutput = lines.slice(jsonStart).join('\n').trim();
                    resolve(jsonOutput);
                } else {
                    resolve(stdout.trim());
                }
            }
        });
    });
}

// ============ 路由 ============

// 健康检查
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', time: new Date().toISOString() });
});

// 获取股票摘要（简化版）
app.get('/api/stock/:symbol/summary', async (req, res) => {
    try {
        const { symbol } = req.params;
        const result = await runPython(ANALYZER_PATH, [symbol, '--json']);
        const data = JSON.parse(result);
        
        const m = data.market_data;
        const final = data.final_recommendation;
        
        res.json({
            symbol: m.symbol,
            name: m.name,
            market: m.market,
            price: m.current_price,
            change: m.change_percent,
            action: final.action,
            confidence: final.confidence,
            target: final.target_price,
            stop: final.stop_loss,
        });
    } catch (err) {
        console.error('分析失败:', err.message);
        res.status(500).json({ error: err.message });
    }
});

// 分析单只股票
app.get('/api/stock/:symbol', async (req, res) => {
    try {
        const { symbol } = req.params;
        const { name } = req.query;
        
        const args = name ? [symbol, '--name', name, '--json'] : [symbol, '--json'];
        const result = await runPython(ANALYZER_PATH, args);
        const data = JSON.parse(result);
        
        res.json(data);
    } catch (err) {
        console.error('分析失败:', err.message);
        res.status(500).json({ error: err.message });
    }
});

// POST 分析股票
app.post('/api/stock/analyze', async (req, res) => {
    try {
        const { symbol, name } = req.body;
        
        if (!symbol) {
            return res.status(400).json({ error: 'symbol is required' });
        }
        
        const args = name ? [symbol, '--name', name, '--json'] : [symbol, '--json'];
        const result = await runPython(ANALYZER_PATH, args);
        const data = JSON.parse(result);
        
        res.json(data);
    } catch (err) {
        console.error('分析失败:', err.message);
        res.status(500).json({ error: err.message });
    }
});

// 获取文本报告
app.get('/api/stock/:symbol/text', async (req, res) => {
    try {
        const { symbol } = req.params;
        const result = await runPython(ANALYZER_PATH, [symbol, '--text']);
        res.type('text/plain').send(result);
    } catch (err) {
        console.error('分析失败:', err.message);
        res.status(500).json({ error: err.message });
    }
});

// 服务信息
app.get('/', (req, res) => {
    res.json({
        service: '数字人才市场 - 股票分析API',
        version: '1.0.0',
        endpoints: {
            'GET /api/health': '健康检查',
            'GET /api/stock/:symbol': '分析股票(GET)',
            'POST /api/stock/analyze': '分析股票(POST)',
            'GET /api/stock/:symbol/summary': '简化摘要',
            'GET /api/stock/:symbol/text': '文本格式报告',
        }
    });
});

// ============ 启动 ============

app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 股票分析API服务已启动`);
    console.log(`📍 http://localhost:${PORT}`);
    console.log(`📚 API文档: http://localhost:${PORT}/`);
});
