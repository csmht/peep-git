/**
 * 主逻辑文件
 * 处理仪表盘的数据加载和交互
 */

let autoRefreshInterval = null;

/**
 * 加载仪表盘数据
 */
async function loadDashboard() {
    try {
        // 获取筛选条件
        const days = document.getElementById('date-range').value;
        const repoFilter = document.getElementById('repo-filter').value;

        // 构建查询参数
        const params = { days: days };
        if (repoFilter) params.repo_path = repoFilter;

        // 并行加载多个 API
        const [statsResult, trendsResult, reposResult, activitiesResult] = await Promise.all([
            api.getStatistics(params),
            api.getTrends({ period: 'day', days: days, repo_path: repoFilter }),
            api.getTopRepos({ limit: 10, days: days }),
            api.getActivities({ page: 1, page_size: 10, repo_path: repoFilter })
        ]);

        // 更新统计卡片
        if (statsResult.success) {
            updateStatsCards(statsResult.data);
        }

        // 更新趋势图
        if (trendsResult.success) {
            chartsManager.initTrendChart('trend-chart', trendsResult.data.data);
        }

        // 更新仓库分布图
        if (reposResult.success) {
            chartsManager.initRepoChart('repo-chart', reposResult.data);
            updateRepoFilter(reposResult.data);
        }

        // 更新分支图
        if (statsResult.success) {
            chartsManager.initBranchChart('branch-chart', statsResult.data.commits_by_branch);
        }

        // 更新最近活动列表
        if (activitiesResult.success) {
            updateActivitiesList(activitiesResult.data.activities);
        }

    } catch (error) {
        console.error('加载仪表盘数据失败:', error);
    }
}

/**
 * 更新统计卡片
 */
function updateStatsCards(stats) {
    document.getElementById('total-commits').textContent = stats.total_commits || 0;
    document.getElementById('total-pushes').textContent = stats.total_pushes || 0;
    document.getElementById('active-repos').textContent = stats.commits_by_repo?.length || 0;
    document.getElementById('avg-commits').textContent = stats.avg_commits_per_day?.toFixed(1) || '0.0';
}

/**
 * 更新仓库筛选下拉框
 */
function updateRepoFilter(repos) {
    const select = document.getElementById('repo-filter');
    const currentValue = select.value;

    // 保留第一个选项("全部仓库")
    select.innerHTML = '<option value="">全部仓库</option>';

    repos.forEach(repo => {
        const option = document.createElement('option');
        option.value = repo.repo_path;
        option.textContent = repo.repo_name;
        select.appendChild(option);
    });

    // 恢复之前的选择
    select.value = currentValue;
}

/**
 * 更新最近活动列表
 */
function updateActivitiesList(activities) {
    const container = document.getElementById('activities-list');

    if (activities.length === 0) {
        container.innerHTML = '<div class="no-data">暂无活动记录</div>';
        return;
    }

    container.innerHTML = activities.map(activity => `
        <div class="activity-item">
            <div class="activity-info">
                <div class="activity-time">${formatDateTime(activity.timestamp)}</div>
                <div class="activity-repo">${getRepoName(activity.repo_path)}</div>
                <div class="activity-branch">${activity.branch_name}</div>
                ${activity.commit_message ? `<div class="activity-message">${truncate(activity.commit_message, 60)}</div>` : ''}
            </div>
            <span class="activity-badge ${activity.activity_type}">
                ${activity.activity_type === 'commit' ? '提交' : '推送'}
            </span>
        </div>
    `).join('');
}

/**
 * 初始化事件监听器
 */
function initEventListeners() {
    // 日期范围变化
    document.getElementById('date-range').addEventListener('change', () => {
        loadDashboard();
    });

    // 仓库筛选变化
    document.getElementById('repo-filter').addEventListener('change', () => {
        loadDashboard();
    });

    // 刷新按钮
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadDashboard();
    });
}

/**
 * 启动自动刷新
 */
function startAutoRefresh(intervalSeconds = 30) {
    // 清除已有的定时器
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }

    // 设置新的定时器
    autoRefreshInterval = setInterval(() => {
        loadDashboard();
    }, intervalSeconds * 1000);
}

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', () => {
    // 加载初始数据
    loadDashboard();

    // 初始化事件监听器
    initEventListeners();

    // 启动自动刷新(30秒)
    startAutoRefresh(30);

    console.log('GitSee 仪表盘已启动');
});

/**
 * 页面卸载时清理资源
 */
window.addEventListener('beforeunload', () => {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    chartsManager.destroyAll();
});
