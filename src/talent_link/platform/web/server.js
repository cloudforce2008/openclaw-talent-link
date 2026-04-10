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
const PORT = process.env.PORT || 8000;

// 中间件
app.use(cors());
app.use(express.json());

// 静态文件服务（前端页面）
app.use(express.static(path.join(__dirname, 'public')));

// 直接用绝对路径，避免 __dirname 在 PM2 下解析异常
const PYTHON_PATH = '/usr/bin/python3';
const PROJECT_ROOT = '/root/projects/openclaw-talent-link';
const SRC_PATH = '/root/projects/openclaw-talent-link/src';
const ANALYZER_PATH = '/root/projects/openclaw-talent-link/src/talent_link/agents/stock_analyst.py';
const CHAT_PATH = '/root/projects/openclaw-talent-link/src/talent_link/chat.py';

// ============ 工具函数 ============

function runPython(script, args) {
    return new Promise((resolve, reject) => {
        const env = {
            PYTHONPATH: SRC_PATH,
            PATH: process.env.PATH
        };
        const proc = spawn(PYTHON_PATH, [script, ...args], {
            cwd: PROJECT_ROOT,
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

// ============ 对话式交互 ============

// 对话式聊天接口 - 流式响应，避免超时
app.post('/api/chat', async (req, res) => {
    const { message } = req.body;
    if (!message) return res.status(400).json({ error: 'message is required' });

    // 立即设置流式响应头，避免 OpenClaw 超时
    res.writeHead(200, {
        'Content-Type': 'application/json',
        'Transfer-Encoding': 'chunked',
        'X-Accel-Buffering': 'no',
        'Cache-Control': 'no-cache',
    });

    // 立即发送一个 "thinking" 信号，让客户端知道已收到请求
    res.write(JSON.stringify({ type: 'status', status: 'thinking', message: '正在分析...' }) + '\n');

    try {
        const result = await runPython(CHAT_PATH, [message]);
        const data = JSON.parse(result);

        // 逐块发送，避免大 JSON 被截断
        res.write(JSON.stringify({ type: 'result', ...data }) + '\n');
        res.end();
    } catch (err) {
        console.error('聊天处理失败:', err.message);
        res.write(JSON.stringify({ type: 'error', error: err.message }) + '\n');
        res.end();
    }
});

// ============ 路由 ============
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
