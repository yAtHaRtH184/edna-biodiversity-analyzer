#!/usr/bin/env python3
"""
eDNA Biodiversity Analyzer Web Application
Flask Backend for SIH Problem 42

Author: yAtHaRtH184
Date: 2025-09-08
"""

import os
import json
import logging
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

# Initialize Flask application
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'sih-2025-edna-biodiversity-analyzer-secret'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

class eDNAAnalysisAPI:
    """eDNA Analysis API for BLAST operations"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "edna_analysis"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Mock databases for demo
        self.databases = [
            {
                'name': '16S_ribosomal_RNA',
                'size_gb': 50.2,
                'file_count': 15,
                'extraction_date': '2025-09-08T05:00:00Z',
                'cloud_files': 15
            },
            {
                'name': 'env_nt',
                'size_gb': 120.8,
                'file_count': 25,
                'extraction_date': '2025-09-08T04:30:00Z',
                'cloud_files': 25
            },
            {
                'name': 'nt',
                'size_gb': 500.5,
                'file_count': 80,
                'extraction_date': '2025-09-08T03:00:00Z',
                'cloud_files': 80
            },
            {
                'name': 'refseq_rna',
                'size_gb': 200.3,
                'file_count': 35,
                'extraction_date': '2025-09-08T02:00:00Z',
                'cloud_files': 35
            }
        ]
    
    def get_databases(self):
        """Get available databases"""
        return {
            "status": "success",
            "databases": self.databases,
            "count": len(self.databases)
        }
    
    def simulate_blast_search(self, sequence, db_name, blast_type='blastn', max_hits=10):
        """Simulate BLAST search with mock results"""
        
        # Mock BLAST results for demo
        mock_results = [
            {
                "hit_id": "gi|123456789|ref|NR_123456.1|",
                "description": "Escherichia coli strain K-12 16S ribosomal RNA gene",
                "length": 1542,
                "evalue": 2e-85,
                "score": 312.4,
                "identity": 98,
                "alignment_length": 1520
            },
            {
                "hit_id": "gi|987654321|ref|NR_987654.1|",
                "description": "Bacillus subtilis 16S ribosomal RNA gene, complete sequence",
                "length": 1560,
                "evalue": 5e-78,
                "score": 289.7,
                "identity": 95,
                "alignment_length": 1495
            },
            {
                "hit_id": "gi|456789123|ref|NR_456789.1|",
                "description": "Pseudomonas aeruginosa 16S ribosomal RNA gene",
                "length": 1535,
                "evalue": 1e-72,
                "score": 267.2,
                "identity": 93,
                "alignment_length": 1480
            }
        ]
        
        # Return simulated results
        return {
            "database": db_name,
            "query_length": len(sequence.replace('\n', '').replace('>', '').replace(' ', '')),
            "results": mock_results[:max_hits],
            "timestamp": datetime.now().isoformat()
        }

# Initialize API
analysis_api = eDNAAnalysisAPI()

# Routes
@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@app.route('/api/databases', methods=['GET'])
def get_databases():
    """Get available databases"""
    return jsonify(analysis_api.get_databases())

@app.route('/api/databases/<db_name>', methods=['GET'])
def get_database_info(db_name):
    """Get information about a specific database"""
    for db in analysis_api.databases:
        if db['name'] == db_name:
            return jsonify({
                "status": "success",
                "database": db
            })
    
    return jsonify({
        "status": "error",
        "message": f"Database {db_name} not found"
    }), 404

@app.route('/api/blast/<db_name>', methods=['POST'])
def run_blast(db_name):
    """Run BLAST search against specified database"""
    try:
        data = request.get_json()
        
        if not data or 'sequence' not in data:
            return jsonify({
                "status": "error",
                "message": "Sequence is required"
            }), 400
        
        sequence = data['sequence']
        blast_type = data.get('blast_type', 'blastn')
        max_hits = data.get('max_hits', 10)
        
        # Validate sequence
        clean_sequence = sequence.replace('>', '').replace('\n', '').replace(' ', '')
        if len(clean_sequence) < 10:
            return jsonify({
                "status": "error",
                "message": "Sequence too short (minimum 10 nucleotides)"
            }), 400
        
        # Check if database exists
        db_exists = any(db['name'] == db_name for db in analysis_api.databases)
        if not db_exists:
            return jsonify({
                "status": "error",
                "message": f"Database {db_name} not found"
            }), 404
        
        # Run BLAST search (simulated)
        results = analysis_api.simulate_blast_search(
            sequence=sequence,
            db_name=db_name,
            blast_type=blast_type,
            max_hits=max_hits
        )
        
        app.logger.info(f"BLAST search completed: {db_name}, {len(results['results'])} hits")
        
        return jsonify({
            "status": "success",
            "blast_results": results
        })
        
    except Exception as e:
        app.logger.error(f"BLAST search failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Analysis failed: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "available_databases": len(analysis_api.databases),
        "version": "1.0.0"
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads"""
    try:
        if 'file' not in request.files:
            return jsonify({
                "status": "error",
                "message": "No file provided"
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "status": "error",
                "message": "No file selected"
            }), 400
        
        # Save file
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Read file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        return jsonify({
            "status": "success",
            "filename": filename,
            "content": content,
            "size": len(content)
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Upload failed: {str(e)}"
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    print("🚀 Starting eDNA Biodiversity Analyzer Web Application")
    print("📍 Application will be available at: http://localhost:5000")
    print("🔬 SIH Problem 42 - Environmental DNA Analysis Solution")
    print("👨‍💻 Developed by: yAtHaRtH184")
    print("-" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)