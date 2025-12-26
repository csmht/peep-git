/**
 * 图表管理器
 * 使用 Chart.js 渲染各种统计图表
 */

class ChartsManager {
    constructor() {
        this.charts = {};
        this.colors = {
            commit: 'rgba(255, 105, 180, 0.8)',
            push: 'rgba(255, 182, 193, 0.8)',
            grid: 'rgba(255, 182, 193, 0.2)',
            text: '#FF1493'
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
                        },
                        ticks: {
                            color: this.colors.text
                        }
                    },
                    x: {
                        grid: {
                            color: this.colors.grid
                        },
                        ticks: {
                            color: this.colors.text
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: this.colors.text
                        }
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

        const labels = data.map(d => d.repo_name);
        const values = data.map(d => d.activity_count);
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
                        position: 'right',
                        labels: {
                            color: this.colors.text
                        }
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
                        },
                        ticks: {
                            color: this.colors.text
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: this.colors.text
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
            'rgba(255, 105, 180, 0.9)',   // 热粉色
            'rgba(255, 182, 193, 0.9)',  // 浅粉色
            'rgba(255, 192, 203, 0.9)',  // 粉红色
            'rgba(219, 112, 147, 0.9)',  // 苍紫罗兰色
            'rgba(255, 20, 147, 0.9)',   // 深粉色
            'rgba(255, 228, 225, 0.9)',  // 薄雾玫瑰色
            'rgba(255, 240, 245, 0.9)',  // 淡紫红色
            'rgba(221, 160, 221, 0.9)',  // 梅红色
            'rgba(238, 130, 238, 0.9)',  // 紫罗兰色
            'rgba(255, 174, 185, 0.9)'   // 浅玫瑰色
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
