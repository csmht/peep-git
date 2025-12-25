/**
 * API 调用封装
 */

const API_BASE = '/api/v1';

class GitSeeAPI {
    /**
     * 获取统计数据
     */
    async getStatistics(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const response = await fetch(`${API_BASE}/statistics?${queryString}`);
        return await response.json();
    }

    /**
     * 获取活动列表
     */
    async getActivities(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const response = await fetch(`${API_BASE}/activities?${queryString}`);
        return await response.json();
    }

    /**
     * 获取趋势数据
     */
    async getTrends(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const response = await fetch(`${API_BASE}/trends?${queryString}`);
        return await response.json();
    }

    /**
     * 获取热门仓库
     */
    async getTopRepos(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const response = await fetch(`${API_BASE}/repos/top?${queryString}`);
        return await response.json();
    }

    /**
     * 导出数据
     */
    async exportData(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        window.location.href = `${API_BASE}/export?${queryString}`;
    }

    /**
     * 手动同步
     */
    async sync() {
        const response = await fetch(`${API_BASE}/sync`, {
            method: 'POST'
        });
        return await response.json();
    }
}

// 创建全局 API 实例
const api = new GitSeeAPI();

// 工具函数

/**
 * 格式化日期时间
 */
function formatDateTime(timestamp) {
    const date = new Date(timestamp);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

/**
 * 获取仓库名称
 */
function getRepoName(path) {
    if (!path) return '未知仓库';
    const parts = path.split('/');
    return parts[parts.length - 1] || path;
}

/**
 * 截断文本
 */
function truncate(text, length = 50) {
    if (!text) return '-';
    return text.length > length ? text.substring(0, length) + '...' : text;
}

/**
 * 防抖函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
