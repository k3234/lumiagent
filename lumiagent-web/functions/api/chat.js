// functions/api/chat.js — Cloudflare Pages Function
// 双模型调度：LongCat (主力) + Agnes AI (备用) + 本地降级
// 访问路径: POST /api/chat
// 安全措施：速率限制 + 输入校验 + CORS 白名单 + 请求体限制

const SYSTEM_PROMPT = '你是 LumiAgent，一个为老旧设备而生的AI编程调度器。核心理念是"算力平权"。你擅长编程问题解答，回答简洁精准，详略得当。用中文回答。当代码中使用 Python 时请确保代码正确。';

const MODELS = [
  {
    id: 'longcat',
    name: 'LongCat-2.0',
    url: 'https://api.longcat.chat/openai/v1/chat/completions',
    keyEnv: 'LONGCAT_API_KEY',
  },
  {
    id: 'agnes',
    name: 'gnes-2.0-flash',
    url: 'https://apihub.agnes-ai.com/v1/chat/completions',
    keyEnv: 'AGNES_API_KEY',
  },
];

// 安全配置
const MAX_MSG_LENGTH = 2000;       // 单条消息最大字符数
const MAX_REQUEST_BODY = 4096;     // 请求体最大字节数
const RATE_LIMIT_WINDOW = 60;      // 速率窗口（秒）
const RATE_LIMIT_MAX = 20;         // 每窗口最大请求数
const ALLOWED_ORIGINS = [
  'https://lumiagent.pages.dev',
  'http://localhost:8788',
];

// 简易内存速率限制（单 Worker 实例级别，适合 Demo 规模）
const rateLimitStore = new Map();

function isRateLimited(ip) {
  const now = Math.floor(Date.now() / 1000);
  const key = `${ip}:${Math.floor(now / RATE_LIMIT_WINDOW)}`;
  const count = rateLimitStore.get(key) || 0;
  if (count >= RATE_LIMIT_MAX) return true;
  rateLimitStore.set(key, count + 1);
  // 清理过期条目
  if (rateLimitStore.size > 10000) {
    const cutoff = now - RATE_LIMIT_WINDOW;
    for (const [k, v] of rateLimitStore) {
      if (parseInt(k.split(':')[1]) < cutoff) rateLimitStore.delete(k);
    }
  }
  return false;
}

function isOriginAllowed(origin) {
  if (!origin) return true;
  return ALLOWED_ORIGINS.some(allowed => origin === allowed);
}

async function callModel(model, apiKey, userMessage) {
  const res = await fetch(model.url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: model.name,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: userMessage },
      ],
      max_tokens: 1024,
      stream: false,
    }),
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data.choices?.[0]?.message?.content || null;
}

export async function onRequestPost(context) {
  const { request, env } = context;
  const origin = request.headers.get('Origin') || '';
  const clientIP = request.headers.get('CF-Connecting-IP') || 'unknown';

  // CORS — 仅允许白名单来源
  const allowOrigin = isOriginAllowed(origin) ? origin : ALLOWED_ORIGINS[0];

  // 速率限制
  if (isRateLimited(clientIP)) {
    return new Response(JSON.stringify({ error: '请求过于频繁，请稍后再试' }), {
      status: 429,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': allowOrigin,
        'Retry-After': String(RATE_LIMIT_WINDOW),
      },
    });
  }

  // 请求体大小检查
  const contentLength = parseInt(request.headers.get('Content-Length') || '0', 10);
  if (contentLength > MAX_REQUEST_BODY) {
    return new Response(JSON.stringify({ error: '请求体过大' }), {
      status: 413,
      headers: corsHeaders(allowOrigin),
    });
  }

  try {
    const { message } = await request.json();
    const msg = (message || '').trim();

    // 输入长度限制
    if (msg.length > MAX_MSG_LENGTH) {
      return new Response(JSON.stringify({ error: `消息过长，最多 ${MAX_MSG_LENGTH} 字符` }), {
        status: 400,
        headers: corsHeaders(allowOrigin),
      });
    }

    // 输入内容过滤 — 拒绝纯脚本/注入尝试
    if (/<script[\s>]/i.test(msg) || /javascript:/i.test(msg)) {
      return new Response(JSON.stringify({ error: '输入内容不合规' }), {
        status: 400,
        headers: corsHeaders(allowOrigin),
      });
    }

    // /help — 不消耗 API Token
    if (msg.toLowerCase() === '/help') {
      return json({
        role: 'assistant',
        content: [
          '==================================================',
          '  LumiAgent — 为老旧设备而生的AI编程调度器',
          '==================================================',
          '  核心理念：算力平权，让所有设备平等获得AI编程辅助',
          '  核心创新：休息机制 — 任务完成后卸载模型释放内存',
          '',
          '  使用方法：',
          '    - 直接输入编程问题，获取AI回答',
          '    - 输入 /help 查看此帮助',
          '    - 输入 /model 查看当前模型调度状态',
          '    - 输入 exit / quit / 退出 结束会话',
          '',
          '  双模型调度：LongCat-2.0 (主力) + gnes-2.0-flash (备用)',
          '  调度铁律：优先云端主力 → 云端备用 → 本地降级',
          '',
          '  GitHub: https://github.com/k3234/lumiagent',
          '==================================================',
        ].join('\n'),
        model: 'system',
      }, 200, allowOrigin);
    }

    // /model — 显示调度状态
    if (msg.toLowerCase() === '/model') {
      return json({
        role: 'assistant',
        content: [
          '双模型调度状态：',
          '',
          '  主力模型: LongCat-2.0 (api.longcat.chat)',
          '  备用模型: gnes-2.0-flash (apihub.agnes-ai.com)',
          '',
          '  调度策略: 优先调用主力模型',
          '  回退机制: 主力不可用 → 自动切换备用',
          '  最终降级: 双方不可用 → 本地模拟回复',
        ].join('\n'),
        model: 'system',
      }, 200, allowOrigin);
    }

    // exit / quit / 退出
    if (['exit', 'quit', '退出'].includes(msg.toLowerCase())) {
      return json({ role: 'assistant', content: '👋 再见！设备休息一下~', model: 'system' }, 200, allowOrigin);
    }

    // 空消息
    if (!msg) {
      return json({ role: 'assistant', content: '', model: 'system', action: 'skip' }, 200, allowOrigin);
    }

    // === 双模型调度：主力 → 备用 → 降级 ===
    for (const model of MODELS) {
      const apiKey = env[model.keyEnv];
      if (!apiKey) continue;
      try {
        const content = await callModel(model, apiKey, msg);
        if (content) {
          return json({ role: 'assistant', content, model: model.name }, 200, allowOrigin);
        }
      } catch (e) {
        continue;
      }
    }

    // 全部失败 → 本地降级
    return json({
      role: 'assistant',
      content: '[云端模型暂时不可用，已自动降级为本地模式]\n\n我当前运行在受限模式下，功能有限。请稍后重试以获取完整的AI回答。',
      model: 'local-fallback',
    }, 200, allowOrigin);

  } catch (err) {
    return json({
      role: 'assistant',
      content: '错误：请求处理时发生未知问题',
      model: 'error',
    }, 500, allowOrigin);
  }
}

// CORS preflight handler
export async function onRequestOptions(context) {
  const origin = context.request.headers.get('Origin') || '';
  const allowOrigin = isOriginAllowed(origin) ? origin : ALLOWED_ORIGINS[0];
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': allowOrigin,
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400',
    },
  });
}

function corsHeaders(allowOrigin) {
  return {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': allowOrigin,
  };
}

function json(body, status = 200, allowOrigin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: corsHeaders(allowOrigin),
  });
}
