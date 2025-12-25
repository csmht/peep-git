/**
 * 图表管理器
 * 使用 Chart.js 渲染各种统计图表
 */

class ChartsManager {
    constructor() {
        this.charts = {};
        this.colors = {
            commit: 'rgba(40, 167, 69, 0.8)',
            push: 'rgba(0, 123, 255, 0.8)',
            grid: 'rgba(0, 0, 0, 0.1)'
        };
    }

    /**
     * 初始化趋势图(折线图)
     */
    initTrendChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');

        // 销毁旧图表
        if (this.charts.trend) {
            this.charts.trend.destroy();
        }

        this.charts.trend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [
                    {
                        label: '提交次数',
                        data: data.map(d => d.commits),
                        borderColor: this.colors.commit,
                        backgroundColor: this.colors.commit,
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: '推送次数',
                        data: data.map(d => d.pushes),
                        borderColor: this.colors.push,
                        backgroundColor: this.colors.push,
                        tension: 0.4,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: this.colors.grid
                        }
                    },
                    x: {
                        grid: {
                            color: this.colors.grid
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });
    }

    /**
     * 更新趋势图
     */
    updateTrendChart(data) {
        if (this.charts.trend) {
            this.charts.trend.data.labels = data.map(d => d.date);
            this.charts.trend.data.datasets[0].data = data.map(d => d.commits);
            this.charts.trend.data.datasets[1].data = data.map(d => d.pushes);
            this.charts.trend.update();
        }
    }

    /**
     * 初始化仓库分布图(饼图)
     */
    initRepoChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');

        if (this.charts.repo) {
            this.charts.repo.destroy();
        }

        const labels = data.map(d => getRepoName(d.repo_path));
        const values = data.map(d => d.count);
        const colors = this.generateColors(data.length);

        this.charts.repo = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * 初始化分支活跃度图(横向柱状图)
     */
    initBranchChart(canvasId, data) {
        const ctx = document.getElementById(canvasId).getContext('2d');

        if (this.charts.branch) {
            this.charts.branch.destroy();
        }

        this.charts.branch = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.branch_name),
                datasets: [{
                    label: '活动次数',
                    data: data.map(d => d.count),
                    backgroundColor: this.colors.commit,
                    borderColor: this.colors.commit,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: {
                            color: this.colors.grid
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    /**
     * 生成颜色数组
     */
    generateColors(count) {
        const baseColors = [
            'rgba(102, 126, 234, 0.8)',
            'rgba(118, 75, 162, 0.8)',
            'rgba(40, 167, 69, 0.8)',
            'rgba(0, 123, 255, 0.8)',
            'rgba(255, 193, 7, 0.8)',
            'rgba(220, 53, 69, 0.8)',
            'rgba(23, 162, 184, 0.8)',
            'rgba(111, 66, 193, 0.8)'
        ];

        const colors = [];
        for (let i = 0; i < count; i++) {
            colors.push(baseColors[i % baseColors.length]);
        }
        return colors;
    }

    /**
     * 销毁所有图表
     */
    destroyAll() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// 创建全局图表管理器实例
const chartsManager = new ChartsManager();
