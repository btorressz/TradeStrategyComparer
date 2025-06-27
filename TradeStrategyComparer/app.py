import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.middleware.proxy_fix import ProxyFix
import threading
import time
from datetime import datetime
import pandas as pd
from trading_bots import TWAPBot, SmartBot
from jupiter_api import JupiterAPI
from data_logger import DataLogger
from chart_generator import ChartGenerator

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Global variables for simulation state
simulation_running = False
simulation_thread = None
simulation_data = {
    'twap_bot': None,
    'smart_bot': None,
    'data_logger': None,
    'start_time': None,
    'duration_minutes': 60
}

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    """Start the trading simulation"""
    global simulation_running, simulation_thread, simulation_data
    
    if simulation_running:
        flash('Simulation is already running!', 'warning')
        return redirect(url_for('simulation_dashboard'))
    
    try:
        # Get configuration from form
        trade_amount = float(request.form.get('trade_amount', 1.0))
        slippage_threshold = float(request.form.get('slippage_threshold', 0.2))
        duration_minutes = int(request.form.get('duration_minutes', 60))
        trade_direction = request.form.get('trade_direction', 'SOL_TO_USDC')
        
        # Initialize components
        jupiter_api = JupiterAPI()
        data_logger = DataLogger()
        
        # Create bots
        twap_bot = TWAPBot(
            trade_amount=trade_amount,
            interval_minutes=5,
            jupiter_api=jupiter_api,
            data_logger=data_logger,
            trade_direction=trade_direction
        )
        
        smart_bot = SmartBot(
            trade_amount=trade_amount,
            slippage_threshold=slippage_threshold,
            jupiter_api=jupiter_api,
            data_logger=data_logger,
            trade_direction=trade_direction
        )
        
        # Store simulation data
        simulation_data.update({
            'twap_bot': twap_bot,
            'smart_bot': smart_bot,
            'data_logger': data_logger,
            'start_time': datetime.now(),
            'duration_minutes': duration_minutes
        })
        
        # Start simulation in separate thread
        simulation_thread = threading.Thread(target=run_simulation, args=(duration_minutes,))
        simulation_running = True
        simulation_thread.start()
        
        flash('Simulation started successfully!', 'success')
        return redirect(url_for('simulation_dashboard'))
        
    except Exception as e:
        logging.error(f"Error starting simulation: {e}")
        flash(f'Error starting simulation: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/simulation')
def simulation_dashboard():
    """Real-time simulation dashboard"""
    global simulation_running, simulation_data
    
    if not simulation_running and simulation_data['twap_bot'] is None:
        flash('No simulation running. Please start a simulation first.', 'info')
        return redirect(url_for('index'))
    
    return render_template('simulation.html', 
                         simulation_running=simulation_running,
                         simulation_data=simulation_data)

@app.route('/api/simulation_status')
def get_simulation_status():
    """API endpoint for real-time simulation status"""
    global simulation_running, simulation_data
    
    if not simulation_data['twap_bot']:
        return jsonify({'running': False, 'error': 'No simulation initialized'})
    
    try:
        # Calculate elapsed time
        elapsed_minutes = 0
        if simulation_data['start_time']:
            elapsed = datetime.now() - simulation_data['start_time']
            elapsed_minutes = elapsed.total_seconds() / 60
        
        # Get bot statistics
        twap_stats = simulation_data['twap_bot'].get_stats()
        smart_stats = simulation_data['smart_bot'].get_stats()
        
        return jsonify({
            'running': simulation_running,
            'elapsed_minutes': elapsed_minutes,
            'duration_minutes': simulation_data['duration_minutes'],
            'twap_stats': twap_stats,
            'smart_stats': smart_stats,
            'progress_percent': min(100, (elapsed_minutes / simulation_data['duration_minutes']) * 100)
        })
        
    except Exception as e:
        logging.error(f"Error getting simulation status: {e}")
        return jsonify({'running': False, 'error': str(e)})

@app.route('/stop_simulation', methods=['POST'])
def stop_simulation():
    """Stop the running simulation"""
    global simulation_running
    
    if simulation_running:
        simulation_running = False
        flash('Simulation stopped successfully!', 'info')
    else:
        flash('No simulation is currently running.', 'warning')
    
    return redirect(url_for('simulation_dashboard'))

@app.route('/results')
def results():
    """View simulation results and charts"""
    global simulation_data
    
    if not simulation_data['data_logger']:
        flash('No simulation data available. Please run a simulation first.', 'info')
        return redirect(url_for('index'))
    
    try:
        # Generate charts
        chart_generator = ChartGenerator(simulation_data['data_logger'])
        charts = chart_generator.generate_all_charts()
        
        # Get summary statistics
        summary_stats = simulation_data['data_logger'].get_summary_stats()
        
        return render_template('results.html', 
                             charts=charts, 
                             summary_stats=summary_stats)
        
    except Exception as e:
        logging.error(f"Error generating results: {e}")
        flash(f'Error generating results: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/download_csv')
def download_csv():
    """Download simulation data as CSV"""
    global simulation_data
    
    if not simulation_data['data_logger']:
        flash('No simulation data available.', 'error')
        return redirect(url_for('index'))
    
    try:
        csv_path = simulation_data['data_logger'].export_to_csv()
        return send_file(csv_path, as_attachment=True, download_name='trading_simulation_data.csv')
    except Exception as e:
        logging.error(f"Error downloading CSV: {e}")
        flash(f'Error downloading CSV: {str(e)}', 'danger')
        return redirect(url_for('results'))

def run_simulation(duration_minutes):
    """Run the trading simulation for specified duration"""
    global simulation_running, simulation_data
    
    try:
        logging.info(f"Starting simulation for {duration_minutes} minutes")
        
        # Start both bots
        twap_thread = threading.Thread(target=simulation_data['twap_bot'].run)
        smart_thread = threading.Thread(target=simulation_data['smart_bot'].run)
        
        twap_thread.start()
        smart_thread.start()
        
        # Wait for duration or until stopped
        start_time = time.time()
        while simulation_running and (time.time() - start_time) < (duration_minutes * 60):
            time.sleep(1)
        
        # Stop bots
        simulation_data['twap_bot'].stop()
        simulation_data['smart_bot'].stop()
        
        # Wait for threads to finish
        twap_thread.join(timeout=10)
        smart_thread.join(timeout=10)
        
        simulation_running = False
        logging.info("Simulation completed")
        
    except Exception as e:
        logging.error(f"Error in simulation: {e}")
        simulation_running = False

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
