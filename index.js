export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const { pathname } = url;

    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, HEAD, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // --- 1. R2 图片代理 ---
      if (pathname.startsWith("/img/")) {
        const key = pathname.replace("/img/", "");
        const object = await env.MY_R2.get(key);
        if (!object) return new Response("Object Not Found", { status: 404, headers: corsHeaders });

        const headers = new Headers(corsHeaders);
        object.writeHttpMetadata(headers);
        headers.set("etag", object.httpEtag);
        headers.set("Cache-Control", "public, max-age=604800, immutable");
        return new Response(object.body, { headers });
      }

      // --- 2. 随机背景 API ---
      if (pathname === "/api/random-bg") {
        const num = Math.floor(Math.random() * 5) + 1;
        const imageUrl = `${url.origin}/img/backgrounds/wall${num}.jpg`;
        return Response.json({ url: imageUrl }, { headers: corsHeaders });
      }

      // --- 3. D1：获取用户信息 ---
      if (pathname === "/api/user") {
        const { results } = await env.BLOG_DB.prepare("SELECT * FROM config").all();
        const configMap = Object.fromEntries(results.map(row => [row.key, row.value]));
        if (configMap.avatar) {
          configMap.avatar_url = `${url.origin}/img/${configMap.avatar}`;
        }
        return Response.json(configMap, { headers: corsHeaders });
      }

      // --- 4. D1：文章列表接口 ---
      if (pathname === "/api/posts") {
        const { results } = await env.BLOG_DB.prepare(`
          SELECT 
            id, title, category, post_type, language, 
            is_open_source, project_name, thumb_url, date,
            SUBSTR(content, 1, 50) as summary 
          FROM posts 
          ORDER BY date DESC
        `).all();
        return Response.json(results, { headers: corsHeaders });
      }

      // --- 5. D1：文章详情接口 ---
      if (pathname.startsWith("/api/posts/")) {
        const id = pathname.split("/").pop();
        const post = await env.BLOG_DB.prepare("SELECT * FROM posts WHERE id = ?")
          .bind(id)
          .first();
        if (!post) return new Response("Post Not Found", { status: 404, headers: corsHeaders });
        return Response.json(post, { headers: corsHeaders });
      }

      // --- 6. Wiki 结构接口 ---
      if (pathname === "/api/wiki/tree") {
        const { results } = await env.WIKI_DB.prepare("SELECT * FROM wiki_nodes ORDER BY sort_order ASC").all();
        return Response.json(results, { headers: corsHeaders });
      }

      // --- 7. Wiki 内容接口 ---
      if (pathname.startsWith("/api/wiki/content/")) {
        const nodeId = pathname.split("/").pop();
        const data = await env.WIKI_DB.prepare("SELECT * FROM wiki_contents WHERE node_id = ?")
          .bind(nodeId)
          .first();
        return Response.json(data || { content: "### 🚧 暂无内容\n该节点还没有写入任何魔法笔记喵。" }, { headers: corsHeaders });
      }

      // --- 8. Wiki 全文搜索接口 ---
      if (pathname === "/api/wiki/search") {
        const query = url.searchParams.get("q");
        const { results } = await env.WIKI_DB.prepare(`
          SELECT n.id, n.title, SUBSTR(c.content, 1, 50) as snippet 
          FROM wiki_nodes n
          LEFT JOIN wiki_contents c ON n.id = c.node_id
          WHERE n.title LIKE ? OR c.content LIKE ?
          LIMIT 10
        `).bind(`%${query}%`, `%${query}%`).all();
        return Response.json(results, { headers: corsHeaders });
      }

      // --- 9. Telegram 消息推送接口 ---
      if (pathname === "/api/notify" && request.method === "POST") {
        const data = await request.json();
        let message = `🚀 *收到新传送门讯息*\n\n`;
        message += `*分类:* ${data.type}\n`;
        message += `*联系方式:* ${data.contact}\n`;
        if (data.issueLink) {
          message += `*Issue 链接:* [点击查看](${data.issueLink})\n`;
        }
        message += `\n*内容详情:*\n${data.content}`;

        const tgRes = await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/sendMessage`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ chat_id: env.TG_CHAT_ID, text: message, parse_mode: "Markdown" })
        });
        return Response.json({ success: tgRes.ok }, { headers: corsHeaders });
      }

      /// --- 10. D1：邮件留言板读取接口 (Portal Hub) ---
      if (pathname === "/api/messages") {
        const { results } = await env.BLOG_DB.prepare(`
          SELECT nickname, subject, content, date 
          FROM mail_messages 
          ORDER BY id DESC 
          LIMIT 50
        `).all();
        return Response.json(results, { headers: corsHeaders });
      }

// --- 11. 独立自动化接口：发送 R2 附件邮件 ---
      if (pathname === "/api/dh") {
        const token = url.searchParams.get("token");
        
        // 1. 校验 Token
        if (token !== env.DH_TOKEN) {
          return new Response("Forbidden: Invalid Token", { status: 403, headers: corsHeaders });
        }

        try {
          // 2. 从 R2 提取 Xieerfan.zip
          const zipObject = await env.MY_R2.get("Xieerfan.zip");
          if (!zipObject) {
            return new Response("Error: Xieerfan.zip not found in R2", { status: 404, headers: corsHeaders });
          }

          // 3. 将 ZIP 转为 Base64
          const zipBuffer = await zipObject.arrayBuffer();
          const base64Content = btoa(String.fromCharCode(...new Uint8Array(zipBuffer)));

          // 4. 获取变量：收件人和正文内容
          const recipient = String(env.MY_EMAIL || "").trim();
          // 如果环境变量里没写内容，就给个默认文字防止空白
          const htmlContent = String(env.DH_HTML_CONTENT || "<h2>DH 自动传送门</h2><p>附件已成功从 R2 提取并发送。</p>").trim();
          
          if (!recipient || !recipient.includes("@")) {
            return new Response("Error: MY_EMAIL is not set in CF Env", { status: 500, headers: corsHeaders });
          }

          // 5. 调用 Resend 发送
          const resendRes = await fetch("https://api.resend.com/emails", {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${env.RESEND_KEY}`,
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              from: "ArchBlog Bot <bot@xieerfan.com>",
              to: recipient, // 使用变量
              subject: `[DH 激活] 附件传送: Xieerfan.zip`,
              html: htmlContent, // 使用变量
              attachments: [
                {
                  filename: "Xieerfan.zip",
                  content: base64Content
                }
              ]
            })
          });

          const result = await resendRes.json();

          if (resendRes.ok) {
            return Response.json({ 
              success: true, 
              to: recipient,
              message: "已读取环境变量并完成发送！" 
            }, { headers: corsHeaders });
          } else {
            throw new Error(JSON.stringify(result));
          }

        } catch (err) {
          return new Response("DH Error: " + err.message, { status: 500, headers: corsHeaders });
        }
      }

      return new Response("Arch Blog API Hub is Running!", { headers: corsHeaders });

    } catch (err) {
      return new Response(err.stack, { status: 500, headers: corsHeaders });
    }
  },

async email(message, env) {
  const sender = message.from;
  const subject = message.headers.get("subject") || "无主题";
  const raw = await new Response(message.raw).text();

  // --- 1. 简易 MIME 提取逻辑 ---
  function getMessageBody(rawMail) {
    // 优先寻找纯文本部分 (text/plain)，如果没有则找 HTML
    let body = "";
    let encoding = "";
    let charset = "utf-8";

    // 尝试匹配文本块
    const partMatch = rawMail.match(/Content-Type: text\/plain;[\s\S]*?\r?\n\r?\n([\s\S]*?)(?=\r?\n--|$)/i);
    
    if (partMatch) {
      const headerArea = partMatch[0]; // 包含 Content-Transfer-Encoding 的头部
      body = partMatch[1];
      
      // 提取编码方式
      if (/encoding:.*base64/i.test(headerArea)) encoding = "base64";
      else if (/encoding:.*quoted-printable/i.test(headerArea)) encoding = "qp";
      
      // 提取字符集
      if (/charset=.*gb/i.test(headerArea)) charset = "gbk";
    } else {
      // 如果没找到标准块，尝试最原始的切分
      body = rawMail.split(/\r?\n\r?\n/).slice(1).join('\n');
    }

    // --- 2. 解码逻辑 ---
    try {
      if (encoding === "base64") {
        const bin = atob(body.replace(/\s/g, ''));
        return new TextDecoder(charset).decode(Uint8Array.from(bin, c => c.charCodeAt(0)));
      } else if (encoding === "qp") {
        // 解码 Quoted-Printable
        const decodedQP = body.replace(/=\r?\n/g, '').replace(/=([0-9A-F]{2})/gi, (match, hex) => {
          return String.fromCharCode(parseInt(hex, 16));
        });
        return new TextDecoder(charset).decode(Uint8Array.from(decodedQP, c => c.charCodeAt(0)));
      }
      return body; // 默认直接返回
    } catch (e) {
      return "解析失败: " + e.message;
    }
  }

  let cleanContent = getMessageBody(raw);

  // --- 3. 强力清洗 ---
  cleanContent = cleanContent
    .replace(/<[^>]*>?/gm, '') // 删掉 HTML 标签
    .replace(/Content-Type:[\s\S]*?(?=\n\n|$)/gi, '') // 删掉残余 Header
    .replace(/--_Part_.*|--=_Part_.*/g, '') // 删掉边界符
    .slice(0, 500)
    .trim();

    // 判断逻辑
    const isSpecial = subject.includes("[+]");
    let nickname = "匿名小可爱";

    // 如果包含 [+]，尝试提取 [xxx] 里的昵称
    if (isSpecial) {
      const match = subject.match(/\[\+\]\s*\[(.*?)\]/);
      if (match && match[1]) {
        nickname = match[1];
      }
      
      // 写入 D1 数据库
      try {
        await env.BLOG_DB.prepare(
          "INSERT INTO mail_messages (nickname, subject, content, date) VALUES (?, ?, ?, ?)"
        ).bind(nickname, subject, cleanContent, new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })).run();
      } catch (e) {
        console.error("D1 Insert Error:", e);
      }
    }

    // --- 第一步：推送 Telegram ---
    const icon = isSpecial ? "📝" : "📧";
    const tgNotice = isSpecial ? `*【留言板新入驻: ${nickname}】*` : `*【普通来信】*`;
    
    await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: env.TG_CHAT_ID,
        text: `${icon} ${tgNotice}\n👤 来自: ${sender}\n📝 主题: ${subject}\n\n🤖 _已同步至 D1 数据库并自动回信。_`,
        parse_mode: "Markdown"
      })
    });

    // --- 第二步：准备回信 HTML ---
    const replyHtml = isSpecial ? `
      <div style="font-family: sans-serif; max-width: 600px; border: 2px solid #2563eb; border-radius: 10px; padding: 20px;">
        <h2 style="color: #2563eb;">留言成功！✨</h2>
        <p>你好 <strong>${nickname}</strong>，感谢你的留言。</p>
        <p>你的足迹已记录在 <strong>ArchBlog 留言板</strong> 数据库中。</p>
        <p>博主看到后会通过传送门给你回电喵~</p>
      </div>
    ` : `
      <div style="font-family: sans-serif; max-width: 600px; border: 1px solid #eee; border-radius: 10px; padding: 20px;">
        <h2 style="color: #2563eb;">你好喵！👋</h2>
        <p>我是 <strong>Xieerfan 博客助手</strong>。已收到关于“${subject}”的来信。</p>
        <p>博主由于正在折腾代码或打游戏（或者嗝屁了），请耐心等待回复~</p>
      </div>
    `;

    // --- 第三步：发送回信 ---
    await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.RESEND_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        from: "ArchBlog Bot <bot@xieerfan.com>",
        to: [sender],
        subject: isSpecial ? `[Board] Re: ${subject}` : `Re: ${subject}`,
        html: replyHtml
      })
    });
  }
};