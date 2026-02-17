<script setup>
import { ref } from 'vue'
import Navbar from '../components/Navbar.vue'

const API_BASE = 'GITHUB-SC'
const formData = ref({ type: '项目问题', contact: '', issueLink: '', content: '' })
const types = ['项目问题', '碎碎念']

const validateContact = () => {
  const c = formData.value.contact
  if (c.includes('@')) return '📧 识别为邮箱'
  if (/^1[3-9]\d{9}$/.test(c)) return '📱 识别为手机号'
  if (/^[1-9][0-9]{4,10}$/.test(c)) return '🐧 识别为 QQ'
  if (c.includes('t.me/')) return '✈️ 识别为 Telegram'
  return '✍️ 请输入有效的联系方式'
}

const handleSend = async () => {
  if (formData.value.type === '项目问题' && !formData.value.issueLink.trim()) {
    alert('🛑 请先提交 GitHub Issue 并在此附上链接喵！')
    return
  }
  if (!formData.value.contact.trim() || !formData.value.content.trim()) {
    alert('⚠️ 请填完整后再发送')
    return
  }
  try {
    const res = await fetch(`${API_BASE}/api/notify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData.value)
    })
    const result = await res.json()
    if (res.ok && result.success) {
      alert('✨ 传送成功！博主应该已经收到通知了喵。')
      formData.value.content = ''; formData.value.issueLink = ''
    }
  } catch (err) { alert('❌ 传送失败！魔法网络可能断了。') }
}
</script>

<template>
  <div class="contact-page">
    <Navbar />
    <div class="slider-bg" :style="{ backgroundImage: `url(${API_BASE}/img/messages.png)` }"></div>

    <div class="content-overlay">
      <div class="glass-card main-portal">
        <h1 class="portal-title">传送门</h1>
        <p class="portal-subtitle">人已死 有事烧纸</p>

        <div class="form-body">
          <div class="form-section">
            <label>联系分类</label>
            <div class="type-slider">
              <div v-for="t in types" :key="t" 
                   :class="['type-item', { active: formData.type === t }]"
                   @click="formData.type = t">{{ t }}</div>
            </div>
          </div>

          <div class="form-section" v-if="formData.type === '项目问题'">
            <label>GitHub Issue 链接 (必填)</label>
            <input type="text" v-model="formData.issueLink" placeholder="请先在 GitHub 提 Issue..." class="input-field warning-border">
          </div>

          <div class="form-section">
            <label>你的联系方式 (邮箱/QQ/TG)</label>
            <input type="text" v-model="formData.contact" placeholder="example@qq.com" class="input-field">
            <span class="validator-tip">{{ validateContact() }}</span>
          </div>

          <div class="form-section">
            <label>内容 - 支持 Markdown</label>
            <textarea v-model="formData.content" placeholder="在这里写入你的信息喵..." class="textarea-field"></textarea>
          </div>

          <button class="send-btn" @click="handleSend">
            <span class="btn-text">🚀 开启传送</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.contact-page { min-height: 100vh; position: relative; overflow-y: auto; background: var(--bg-main); }

/* --- 稍微拉低了背景亮度 --- */
.slider-bg { 
  position: fixed; inset: 0; background: center/cover no-repeat; z-index: 1; 
  filter: brightness(var(--bg-brightness, 0.7)); /* 默认 0.7 够柔和了 */
  transition: filter 0.5s ease;
}

.content-overlay { 
  position: relative; z-index: 2; display: flex; justify-content: center; 
  padding: 120px 20px 60px; min-height: 100vh; 
  background: var(--overlay-bg); /* 通过变量控制遮罩 */
  box-sizing: border-box;
}

.main-portal {
  width: 100%; max-width: 620px; padding: 45px; 
  background: var(--card-bg); backdrop-filter: blur(25px);
  border: 1px solid var(--border-color); border-radius: 35px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.1);
}

.portal-title { color: var(--mtf-pink); font-size: 2.4rem; font-weight: 800; letter-spacing: 1px; }
.portal-subtitle { color: var(--text-dim); margin: 5px 0 35px; font-size: 0.95rem; }

.form-section { margin-bottom: 25px; text-align: left; }
.form-section label { color: var(--mtf-blue); font-weight: bold; font-size: 0.85rem; display: block; margin-bottom: 10px; }

.type-slider { display: flex; gap: 12px; }
.type-item { 
  padding: 10px 24px; border-radius: 15px; 
  background: var(--input-bg); border: 1px solid var(--border-color); 
  color: var(--text-main); cursor: pointer; transition: 0.3s;
}
.type-item.active { 
  background: var(--mtf-lavender); color: #fff; border-color: var(--mtf-lavender); 
  box-shadow: 0 5px 15px rgba(203, 166, 247, 0.4);
}

.input-field, .textarea-field {
  width: 100%; background: var(--input-bg); border: 2px solid var(--border-color);
  border-radius: 16px; padding: 14px 18px; color: var(--text-main); 
  outline: none; transition: 0.3s; box-sizing: border-box;
}
.input-field:focus, .textarea-field:focus { 
  border-color: var(--mtf-blue); background: var(--input-focus-bg);
}
.warning-border { border-style: dashed; border-color: var(--mtf-pink); }
.textarea-field { height: 160px; resize: none; }
.validator-tip { font-size: 0.75rem; color: var(--text-dim); margin-top: 8px; }

.send-btn {
  width: 100%; padding: 18px; border-radius: 18px; border: none;
  background: linear-gradient(135deg, var(--mtf-pink), var(--mtf-lavender));
  color: white; font-size: 1.1rem; font-weight: bold; cursor: pointer; 
  transition: 0.3s; box-shadow: 0 10px 25px rgba(245, 194, 231, 0.4);
}
.send-btn:hover { transform: translateY(-3px); box-shadow: 0 15px 30px rgba(245, 194, 231, 0.5); }

/* --- 变量控制：确保亮暗切换顺滑 --- */
:root {
  --overlay-bg: rgba(255, 255, 255, 0.1);
  --input-bg: rgba(255, 255, 255, 0.5);
  --input-focus-bg: #fff;
  --bg-brightness: 0.75; /* 浅色模式稍微亮一点点 */
}

html.dark {
  --overlay-bg: rgba(0, 0, 0, 0.45);
  --input-bg: rgba(49, 50, 68, 0.7);
  --input-focus-bg: rgba(69, 71, 90, 0.9);
  --bg-brightness: 0.45; /* 深色模式拉低亮度，防止背景图反光刺眼 */
}
</style>