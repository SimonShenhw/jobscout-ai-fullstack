# Deploying to Linode (with Caddy + HTTPS)

[English](#english) | [中文](#中文)

---

## English

This guide walks you through deploying JobScout AI to a Linode VPS with automatic HTTPS via Caddy reverse proxy.

### Prerequisites

- A Linode VPS (recommended: **Linode 4GB / 2 vCPU** — Module A needs 2GB+ for ML model)
- A domain name pointing to your Linode IP
- SSH access to the VPS

### Step 1: VPS Initial Setup

```bash
ssh root@your-linode-ip

# Update system
apt update && apt upgrade -y

# Install Docker + Docker Compose
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin -y

# Create deploy user (don't run containers as root)
adduser deploy
usermod -aG docker deploy
```

### Step 2: Clone & Configure

```bash
su deploy
cd ~
git clone https://github.com/SimonShenhw/jobscout-ai-fullstack.git
cd jobscout-ai-fullstack

# Create .env file
cat > .env <<EOF
GOOGLE_API_KEY=your_google_api_key
SERPAPI_API_KEY=your_serpapi_key
ALLOWED_ORIGINS=https://yourdomain.com
API_KEY=$(openssl rand -hex 32)
RATE_LIMIT=20/minute
EOF

chmod 600 .env
```

### Step 3: Set Up Caddy Reverse Proxy

Caddy automatically obtains and renews HTTPS certificates from Let's Encrypt.

Create `Caddyfile` in the project root:

```caddyfile
yourdomain.com {
    # Frontend (public)
    reverse_proxy frontend:8501

    # Module D API (only this is exposed)
    handle /api/* {
        reverse_proxy module-d:8082
    }
}
```

Add Caddy to `docker-compose.yml`:

```yaml
services:
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - frontend
      - module-d
    restart: unless-stopped

volumes:
  caddy_data:
  caddy_config:
```

**Important: Remove the `ports` mapping from internal services** so they're only accessible via the Docker network:

```yaml
agent1:
  # ports:               ← remove this
  #   - "8080:8080"      ← remove this
  expose:
    - "8080"             # only accessible inside Docker network
```

Apply the same to `agent2`, `module-a`, `agent-b`, and `module-d` (only frontend and caddy need public ports).

### Step 4: Deploy

```bash
docker compose up -d --build
docker compose logs -f  # watch logs
```

Visit `https://yourdomain.com` — Caddy will auto-provision the HTTPS cert.

### Step 5: Firewall

```bash
# (As root)
ufw allow 22/tcp     # SSH
ufw allow 80/tcp     # HTTP (Caddy redirects to HTTPS)
ufw allow 443/tcp    # HTTPS
ufw enable
```

### Monitoring

```bash
# View running containers
docker compose ps

# View logs of a specific service
docker compose logs -f module-d

# Restart a service
docker compose restart agent1

# Update to latest code
git pull
docker compose up -d --build
```

### Security Checklist

- [x] `.env` file has `chmod 600` (only deploy user can read)
- [x] `API_KEY` is set (random 32-byte hex)
- [x] `ALLOWED_ORIGINS` set to your domain (not `*`)
- [x] Internal services use `expose` not `ports` (not publicly accessible)
- [x] UFW firewall enabled
- [x] HTTPS via Caddy
- [ ] (Optional) Fail2ban for SSH brute-force protection

### Cost Estimate

- **Linode 4GB**: ~$24/month
- **Domain**: ~$12/year
- **Gemini API**: pay-per-use (free tier covers small usage)
- **SerpAPI**: $50/month for 5,000 searches (or $0 with their 100/month free tier)

### Troubleshooting

**Module A taking 30s+ to start**: Normal on first run — it downloads the SentenceTransformer model (~90MB).

**Caddy can't get HTTPS cert**: DNS not propagated yet. Wait 5 mins, then `docker compose restart caddy`.

**Out of memory**: Linode 2GB is too small. Upgrade to 4GB. Module A + ChromaDB needs ~1.5GB on its own.

---

## 中文

本文档介绍如何将 JobScout AI 部署到 Linode VPS，并通过 Caddy 反向代理自动获取 HTTPS 证书。

### 前置要求

- Linode VPS（推荐 **Linode 4GB / 2 vCPU**，Module A 的 ML 模型需要至少 2GB 内存）
- 域名（解析到 Linode IP）
- VPS 的 SSH 访问权限

### 步骤 1：VPS 初始化

```bash
ssh root@你的_Linode_IP

# 更新系统
apt update && apt upgrade -y

# 安装 Docker + Docker Compose
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin -y

# 创建部署用户（避免用 root 跑容器）
adduser deploy
usermod -aG docker deploy
```

### 步骤 2：克隆 & 配置

```bash
su deploy
cd ~
git clone https://github.com/SimonShenhw/jobscout-ai-fullstack.git
cd jobscout-ai-fullstack

# 创建 .env 文件
cat > .env <<EOF
GOOGLE_API_KEY=你的_google_api_key
SERPAPI_API_KEY=你的_serpapi_key
ALLOWED_ORIGINS=https://你的域名.com
API_KEY=$(openssl rand -hex 32)
RATE_LIMIT=20/minute
EOF

chmod 600 .env
```

### 步骤 3：配置 Caddy 反向代理

Caddy 会自动从 Let's Encrypt 申请并续期 HTTPS 证书。

在项目根目录创建 `Caddyfile`：

```caddyfile
你的域名.com {
    # 前端（公网可访问）
    reverse_proxy frontend:8501

    # Module D API（唯一暴露的 API）
    handle /api/* {
        reverse_proxy module-d:8082
    }
}
```

在 `docker-compose.yml` 添加 Caddy 服务：

```yaml
services:
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - frontend
      - module-d
    restart: unless-stopped

volumes:
  caddy_data:
  caddy_config:
```

**重要：移除内部服务的 `ports` 映射**，让它们只能通过 Docker 内网访问：

```yaml
agent1:
  # ports:               ← 删除
  #   - "8080:8080"      ← 删除
  expose:
    - "8080"             # 仅 Docker 内网可访问
```

对 `agent2`、`module-a`、`agent-b`、`module-d` 同样处理（只有 frontend 和 caddy 需要公网端口）。

### 步骤 4：部署

```bash
docker compose up -d --build
docker compose logs -f  # 查看日志
```

访问 `https://你的域名.com`，Caddy 会自动签发 HTTPS 证书。

### 步骤 5：防火墙

```bash
# （以 root 身份）
ufw allow 22/tcp     # SSH
ufw allow 80/tcp     # HTTP（Caddy 自动跳 HTTPS）
ufw allow 443/tcp    # HTTPS
ufw enable
```

### 运维命令

```bash
# 查看运行中的容器
docker compose ps

# 查看某个服务的日志
docker compose logs -f module-d

# 重启某个服务
docker compose restart agent1

# 更新到最新代码
git pull
docker compose up -d --build
```

### 安全检查清单

- [x] `.env` 文件设置 `chmod 600`（仅 deploy 用户可读）
- [x] 设置了 `API_KEY`（32 字节随机 hex）
- [x] `ALLOWED_ORIGINS` 设为你的域名（而非 `*`）
- [x] 内部服务使用 `expose` 而非 `ports`（不可公网访问）
- [x] 启用 UFW 防火墙
- [x] 通过 Caddy 启用 HTTPS
- [ ]（可选）Fail2ban 防 SSH 暴力破解

### 成本估算

- **Linode 4GB**: 约 $24/月
- **域名**: 约 $12/年
- **Gemini API**: 按用量计费（免费额度够小流量）
- **SerpAPI**: $50/月 5000 次搜索（或免费档每月 100 次）

### 故障排查

**Module A 启动超过 30s**：首次启动正常，需下载 SentenceTransformer 模型（约 90MB）。

**Caddy 无法签发 HTTPS 证书**：DNS 还未生效，等 5 分钟后 `docker compose restart caddy`。

**内存不足**：Linode 2GB 太小，升级到 4GB。Module A + ChromaDB 单独就需要 ~1.5GB。
