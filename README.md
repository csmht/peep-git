# peep - Git 活动监视工具

一个用于监视本地 Git 提交和推送活动的工具,通过全局 Git hook 捕获所有操作,并提供 Web 界面展示统计数据。

## 功能特性

- ✅ **自动扫描**: 一键扫描系统中所有 Git 仓库,自动安装监控 hook
- ✅ **仓库管理**: Web 界面管理所有监控仓库,支持批量操作
- ✅ **全局监视**: 通过 Git hook 自动捕获所有仓库的 commit 和 push 操作
  - **post-commit** hook - 在提交后捕获提交事件
  - **pre-push** hook - 在推送前捕获推送事件
- ✅ **数据可视化**: 使用图表展示提交趋势、仓库分布、分支活跃度
- ✅ **详细记录**: 记录每次操作的详细信息(时间、仓库、分支、消息、作者等)
- ✅ **双存储**: SQLite + JSON 双模式存储,数据更安全
- ✅ **统计分析**: 提供多维度统计数据(按日期、仓库、分支)
- ✅ **数据导出**: 支持 CSV 和 JSON 格式导出
- ✅ **Web 界面**: 美观易用的仪表盘界面

## 技术栈

- **后端**: Python 3.7+ + Flask
- **前端**: HTML + CSS + JavaScript + Chart.js
- **数据库**: SQLite
- **存储**: JSON + SQLite 双模式

## 系统要求

- **Python**: 3.7 或更高版本(推荐 3.8+)
- **Git**: 任意版本(用于 hook 功能)
- **操作系统**: Windows、Linux 或 macOS

### 检查 Python 版本

在安装前,请确认您的 Python 版本:

**Windows:**
```bash
python --version
```

**Linux/Mac:**
```bash
python3 --version
```

如果版本低于 3.7,请先升级 Python:
- **Windows**: 访问 https://www.python.org/downloads/ 下载安装
- **macOS**: 使用 Homebrew: `brew install python3`
- **Linux**: 使用系统包管理器或 pyenv

## 安装步骤

### 1. 克隆或下载项目

```bash
cd C:\Users\Liang\Desktop\Work\gitSee
```

### 2. 运行安装脚本

**Windows:**
```bash
python setup.py
```

**Linux/Mac:**
```bash
python3 setup.py
```

安装脚本将自动:
- ✓ 检查 Python 版本是否符合要求
- ✓ 创建必要的目录结构
- ✓ 初始化 SQLite 数据库
- ✓ 配置 Git 全局模板目录
- ✓ 复制 hook 脚本
- ✓ 安装 Python 依赖

**注意**: 如果 Python 版本不符合要求(低于 3.7),安装脚本会提示您并中止安装。请先升级 Python 后再运行安装脚本。

### 3. 为已有仓库启用 hook

```bash
cd your-existing-repo
git init  # 重新初始化,应用全局模板
```

## 使用方法

### 启动 Web 服务

**Windows:**
```bash
start_server.bat
```

**Linux/Mac:**
```bash
chmod +x start_server.sh
./start_server.sh
```

或手动启动:
```bash
python backend/app.py
```

### 访问 Web 界面

打开浏览器访问: `http://localhost:5000`

GitSee 提供三个主要页面:

1. **仪表盘** (`/`) - 查看整体统计和图表
2. **详细记录** (`/details`) - 查看所有 Git 操作记录
3. **仓库管理** (`/repositories`) - 管理监控的仓库

## 仓库管理

GitSee 提供了强大的仓库管理功能,让您可以轻松管理所有 Git 仓库的监控。

### 方式一:自动扫描(推荐)

1. 访问 `http://localhost:5000/repositories`
2. 点击 **"🔍 扫描 Git 仓库"** 按钮
3. 选择扫描选项:
   - **扫描目录**: 留空则扫描常见目录(用户主目录、桌面、文档等),或手动指定目录(用分号分隔)
   - **扫描深度**: 控制递归扫描的深度(默认 4 层)
4. 点击 **"开始扫描"**
5. 扫描完成后,选择要添加的仓库

扫描会自动发现:
- 用户主目录下的所有 Git 仓库
- 桌面、文档、项目目录中的仓库
- 自动排除系统目录和虚拟环境

### 方式二:手动添加

1. 在仓库管理页面,找到 **"手动添加仓库"** 表单
2. 输入 Git 仓库的完整路径
3. 点击 **"添加"** 按钮

例如:
- Windows: `C:\Users\YourName\projects\my-repo`
- Linux/Mac: `/home/username/projects/my-repo`

### 管理监控仓库

在仓库管理页面,您可以:

- **查看仓库列表**: 所有被监控的仓库以卡片形式展示
- **查看仓库信息**:
  - 仓库名称和路径
  - 监控状态(已监控/未监控)
  - 提交数和推送数统计
  - 最后活动时间
  - 当前分支
  - 远程仓库 URL

- **安装/卸载 Hook**:
  - 点击 **"安装 Hook"** 为仓库启用监控
  - 点击 **"卸载 Hook"** 停止监控仓库

- **删除仓库**: 从监控列表中移除仓库(不会删除实际文件)

### 正常使用

安装完成后,所有 Git 操作(commit/push)将自动被捕获并记录,无需手动干预。

只需正常使用 Git:

```bash
git add .
git commit -m "your commit message"
git push
```

这些操作都会被自动记录到 GitSee 数据库中。

## 项目结构

```
gitSee/
├── backend/                          # 后端核心代码
│   ├── models/                       # 数据模型
│   │   ├── database.py              # 数据库操作
│   │   └── storage_manager.py       # 双存储管理
│   ├── routes/                      # 路由
│   │   ├── api.py                   # 统计 API 端点
│   │   ├── repo_management.py      # 仓库管理 API
│   │   └── web.py                   # Web 页面路由
│   ├── services/                    # 服务
│   │   └── statistics.py            # 统计服务
│   ├── utils/                       # 工具模块
│   │   ├── repo_scanner.py         # 仓库扫描工具
│   │   └── hook_installer.py       # Hook 安装工具
│   └── app.py                       # Flask 应用入口
│
├── frontend/                         # 前端资源
│   ├── static/
│   │   ├── css/                     # 样式文件
│   │   ├── js/                      # JavaScript 文件
│   │   └── lib/                     # 第三方库
│   └── templates/                   # HTML 模板
│       ├── base.html                # 基础模板
│       ├── dashboard.html           # 仪表盘页面
│       ├── details.html             # 详细记录页面
│       └── repositories.html        # 仓库管理页面
│
├── hooks_global/                     # 全局 hook 脚本
│   ├── templates/hooks/             # Hook 模板
│   └── scripts/                     # 捕获脚本
│       ├── capture_commit.py        # 捕获 commit 事件
│       └── capture_push.py          # 捕获 push 事件
│
├── utils/                            # 工具脚本
│   └── check_python.py              # Python 环境检查
│
├── data/                            # 数据存储目录
│   ├── gitsee.db                    # SQLite 数据库
│   └── records.json                 # JSON 备份
│
├── logs/                            # 日志目录
│   └── app.log                      # 应用日志
│
├── setup.py                         # 安装脚本
├── config.json                      # 配置文件
├── start_server.bat                 # Windows 启动脚本
├── start_server.sh                  # Linux/Mac 启动脚本
├── requirements.txt                 # Python 依赖
└── README.md                        # 项目文档
```

## API 文档

### 统计数据

```
GET /api/v1/statistics
```

参数:
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)
- `repo_path`: 仓库路径筛选

### 活动列表

```
GET /api/v1/activities
```

参数:
- `page`: 页码(从 1 开始)
- `page_size`: 每页记录数
- `activity_type`: 活动类型(commit/push)
- `repo_path`: 仓库路径筛选

### 趋势数据

```
GET /api/v1/trends
```

参数:
- `period`: 时间周期(day/week/month)
- `repo_path`: 仓库路径筛选
- `days`: 返回最近几天的数据

### 导出数据

```
GET /api/v1/export
```

参数:
- `format`: 导出格式(json/csv)
- `start_date`: 开始日期
- `end_date`: 结束日期

### 手动同步

```
POST /api/v1/sync
```

触发 SQLite 和 JSON 数据同步。

### 仓库管理 API

#### 扫描仓库

```
POST /api/v1/repos/scan
```

请求体:
```json
{
  "directories": ["路径1", "路径2"],  // 可选
  "max_depth": 5  // 可选,默认 4
}
```

#### 添加仓库

```
POST /api/v1/repos/add
```

请求体:
```json
{
  "repo_path": "仓库路径",
  "install_hook": true  // 是否安装 hook
}
```

#### 获取仓库列表

```
GET /api/v1/repos/list?monitored_only=false
```

#### 安装 Hook

```
POST /api/v1/repos/<仓库路径>/install-hook
```

#### 卸载 Hook

```
POST /api/v1/repos/<仓库路径>/uninstall-hook
```

#### 删除仓库

```
DELETE /api/v1/repos/<仓库路径>
```

#### 批量添加仓库

```
POST /api/v1/repos/batch-add
```

请求体:
```json
{
  "repo_paths": ["路径1", "路径2"],
  "install_hooks": true
}
```

## 配置文件

配置文件位于 `config.json`:

```json
{
  "app": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
  },
  "database": {
    "path": "data/gitsee.db",
    "backup_enabled": true,
    "backup_interval": 86400
  },
  "features": {
    "auto_refresh": true,
    "refresh_interval": 30,
    "enable_trends": true,
    "enable_export": true
  }
}
```

## 常见问题

### 1. Git hook 没有触发?

**确认已安装 hook**:
- 为仓库安装 hook 后,会同时安装 `post-commit` 和 `pre-push` 两个 hook
- 检查仓库的 `.git/hooks/` 目录,应该能看到这两个文件

**确认全局模板目录已正确配置**:
- 全局模板目录主要用于新创建的仓库
- 对于已有仓库,需要通过 Web 界面手动安装 hook

**查看 hook 文件**:
```bash
# 检查 hook 是否存在
ls .git/hooks/post-commit
ls .git/hooks/pre-push

# 查看 hook 内容
cat .git/hooks/post-commit
cat .git/hooks/pre-push
```

### 2. Web 服务无法启动?

- 检查端口 5000 是否被占用
- 在 `config.json` 中修改端口配置
- 确认 Python 依赖已安装

### 3. 推送事件没有被记录?

- `pre-push` hook 会在推送**之前**触发,这是正常的
- 即使推送失败,事件也会被记录
- 确认 `pre-push` hook 已正确安装:
  ```bash
  cat .git/hooks/pre-push
  ```
- 检查 hook 脚本是否有执行权限(Linux/Mac):
  ```bash
  chmod +x .git/hooks/pre-push
  ```

### 4. 数据没有显示?

- 确认数据库文件存在: `data/gitsee.db`
- 检查 Git hook 脚本是否有执行权限
- 查看日志文件: `logs/app.log`

## 卸载

### 1. 取消 Git 全局 hook

```bash
git config --global --unset init.templatedir
```

### 2. 删除项目文件

```bash
# 删除项目目录
rm -rf gitSee
```



欢迎提交 Issue 和 Pull Request!

## 联系方式

如有问题,请提交 Issue。
