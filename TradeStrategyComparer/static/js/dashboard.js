// Dashboard JavaScript for real-time updates
class SimulationDashboard {
    constructor() {
        this.updateInterval = 2000; // Update every 2 seconds
        this.chart = null;
        this.intervalId = null;
        this.init();
    }

    init() {
        this.initChart();
        this.startUpdates();
    }

    initChart() {
        const ctx = document.getElementById('real-time-chart');
        if (!ctx) return;

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'TWAP Bot Output',
                        data: [],
                        borderColor: '#00ff88',
                        backgroundColor: 'rgba(0, 255, 136, 0.1)',
                        tension: 0.2,
                        fill: false
                    },
                    {
                        label: 'Smart Bot Output',
                        data: [],
                        borderColor: '#ff6b6b',
                        backgroundColor: 'rgba(255, 107, 107, 0.1)',
                        tension: 0.2,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Cumulative Output Over Time',
                        color: '#ffffff'
                    },
                    legend: {
                        labels: {
                            color: '#ffffff'
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time',
                            color: '#ffffff'
                        },
                        ticks: {
                            color: '#cccccc'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Output Amount',
                            color: '#ffffff'
                        },
                        ticks: {
                            color: '#cccccc',
                            callback: function(value) {
                                return value.toFixed(4);
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    startUpdates() {
        this.updateStatus();
        this.intervalId = setInterval(() => {
            this.updateStatus();
        }, this.updateInterval);
    }

    stopUpdates() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    async updateStatus() {
        try {
            const response = await fetch('/api/simulation_status');
            const data = await response.json();

            if (!response.ok) {
                console.error('Error fetching status:', data.error);
                return;
            }

            this.updateUI(data);
        } catch (error) {
            console.error('Error updating status:', error);
        }
    }

    updateUI(data) {
        // Update status indicator
        const statusIcon = document.getElementById('status-icon');
        const statusText = document.getElementById('status-text');
        
        if (statusIcon && statusText) {
            if (data.running) {
                statusIcon.className = 'fas fa-circle fa-2x text-success';
                statusText.textContent = 'Running';
            } else {
                statusIcon.className = 'fas fa-circle fa-2x text-secondary';
                statusText.textContent = 'Stopped';
            }
        }

        // Update elapsed time
        const elapsedTime = document.getElementById('elapsed-time');
        if (elapsedTime) {
            const minutes = Math.floor(data.elapsed_minutes);
            const seconds = Math.floor((data.elapsed_minutes - minutes) * 60);
            elapsedTime.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }

        // Update progress
        const progressPercent = Math.min(100, data.progress_percent || 0);
        const progressElement = document.getElementById('progress-percent');
        const progressBar = document.getElementById('progress-bar');
        
        if (progressElement) {
            progressElement.textContent = `${progressPercent.toFixed(1)}%`;
        }
        
        if (progressBar) {
            progressBar.style.width = `${progressPercent}%`;
            progressBar.textContent = `${progressPercent.toFixed(1)}%`;
            
            // Update progress bar color based on completion
            progressBar.className = 'progress-bar progress-bar-striped';
            if (data.running) {
                progressBar.classList.add('progress-bar-animated');
            }
            if (progressPercent >= 100) {
                progressBar.classList.add('bg-success');
            }
        }

        // Update total trades
        const totalTrades = document.getElementById('total-trades');
        if (totalTrades && data.twap_stats && data.smart_stats) {
            const total = (data.twap_stats.total_trades || 0) + (data.smart_stats.total_trades || 0);
            totalTrades.textContent = total.toString();
        }

        // Update TWAP bot stats
        if (data.twap_stats) {
            this.updateElement('twap-trades', data.twap_stats.total_trades || 0);
            this.updateElement('twap-input', (data.twap_stats.total_input_traded || 0).toFixed(2));
            this.updateElement('twap-output', (data.twap_stats.total_output_received || 0).toFixed(2));
            this.updateElement('twap-slippage', (data.twap_stats.average_slippage || 0).toFixed(3) + '%');
        }

        // Update Smart bot stats
        if (data.smart_stats) {
            this.updateElement('smart-trades', data.smart_stats.total_trades || 0);
            this.updateElement('smart-input', (data.smart_stats.total_input_traded || 0).toFixed(2));
            this.updateElement('smart-output', (data.smart_stats.total_output_received || 0).toFixed(2));
            this.updateElement('smart-slippage', (data.smart_stats.average_slippage || 0).toFixed(3) + '%');
            this.updateElement('smart-execution-rate', (data.smart_stats.execution_rate || 0).toFixed(2) + '%');
        }

        // Update chart if running
        if (data.running && this.chart) {
            this.updateChart(data);
        }

        // Stop updates if simulation is complete
        if (!data.running && data.progress_percent >= 100) {
            this.stopUpdates();
        }
    }

    updateElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    updateChart(data) {
        if (!this.chart || !data.twap_stats || !data.smart_stats) return;

        const currentTime = new Date().toLocaleTimeString();
        const maxDataPoints = 20; // Keep last 20 data points

        // Add new data point
        this.chart.data.labels.push(currentTime);
        this.chart.data.datasets[0].data.push(data.twap_stats.total_output_received || 0);
        this.chart.data.datasets[1].data.push(data.smart_stats.total_output_received || 0);

        // Remove old data points if too many
        if (this.chart.data.labels.length > maxDataPoints) {
            this.chart.data.labels.shift();
            this.chart.data.datasets[0].data.shift();
            this.chart.data.datasets[1].data.shift();
        }

        this.chart.update('none'); // Update without animation for performance
    }

    destroy() {
        this.stopUpdates();
        if (this.chart) {
            this.chart.destroy();
        }
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.dashboard = new SimulationDashboard();
});

// Clean up when page unloads
window.addEventListener('beforeunload', function() {
    if (window.dashboard) {
        window.dashboard.destroy();
    }
});
