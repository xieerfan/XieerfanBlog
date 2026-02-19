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

      // --- 9. Telegram 消息推送接口 (NEW!) ---
      if (pathname === "/api/notify" && request.method === "POST") {
        const data = await request.json();
        
        // 构建发送给 TG 的文本
        let message = `🚀 *收到新传送门讯息*\n\n`;
        message += `*分类:* ${data.type}\n`;
        message += `*联系方式:* ${data.contact}\n`;
        if (data.issueLink) {
          message += `*Issue 链接:* [点击查看](${data.issueLink})\n`;
        }
        message += `\n*内容详情:*\n${data.content}`;

        const tgUrl = `https://api.telegram.org/bot${env.TG_TOKEN}/sendMessage`;
        
        const tgRes = await fetch(tgUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            chat_id: env.TG_CHAT_ID,
            text: message,
            parse_mode: "Markdown"
          })
        });

        if (tgRes.ok) {
          return Response.json({ success: true }, { headers: corsHeaders });
        } else {
          return Response.json({ success: false, error: "TG API Error" }, { status: 500, headers: corsHeaders });
        }
      }

      return new Response("Arch Blog API is Running!", { headers: corsHeaders });

    } catch (err) {
      return new Response(err.stack, { status: 500, headers: corsHeaders });
    }
  },

  // --- 新增：邮件处理逻辑 ---
  async email(message, env) {
    const subject = message.headers.get("subject") || "无主题邮件";
    const from = message.from;
    const to = message.to;

    // 拼一个更帅的 TG 消息
    const tgMessage = 
      `📧 *【xieerfan.com】收到新邮件*\n` +
      `--------------------------\n` +
      `👤 *发件人:* ${from}\n` +
      `🎯 *收件人:* ${to}\n` +
      `📝 *主题:* ${subject}\n` +
      `--------------------------\n` +
      `💡 _提示: 详细内容已转发至你的私人邮箱_`;

    // 调用 Telegram Bot API
    await fetch(`https://api.telegram.org/bot${env.TG_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: env.TG_CHAT_ID,
        text: tgMessage,
        parse_mode: "Markdown"
      })
    });
  }
};