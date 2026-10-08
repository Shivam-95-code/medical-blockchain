from flask import Flask, jsonify, request, render_template, send_file
from flask_cors import CORS
from blockchain import Blockchain, Block
import time
import os
import io
import zipfile

app = Flask(__name__)
CORS(app)

blockchain = Blockchain()

patients = {}
patient_counter = 1

def generate_patient_id():
    global patient_counter
    pid = f"PID-{patient_counter:04d}"
    patient_counter += 1
    return pid

# Seed data on startup
def seed_data():
    p1 = generate_patient_id()
    patients[p1] = {"name": "Alice Smith", "age": 30, "gender": "Female", "blood_group": "A+", "contact": "555-0101", "emergency_contact": "555-0102"}
    blockchain.add_block(Block(len(blockchain.chain), time.time(), {
        "patient_id": p1, "patient_name": "Alice Smith", "record_type": "diagnosis",
        "doctor": "Dr. House", "description": "Common cold", "date": "2023-10-01", "department": "General Medicine"
    }, ""))
    
    p2 = generate_patient_id()
    patients[p2] = {"name": "Bob Jones", "age": 45, "gender": "Male", "blood_group": "O-", "contact": "555-0201", "emergency_contact": "555-0202"}
    blockchain.add_block(Block(len(blockchain.chain), time.time(), {
        "patient_id": p2, "patient_name": "Bob Jones", "record_type": "prescription",
        "doctor": "Dr. Strange", "description": "Ibuprofen 400mg", "date": "2023-10-02", "department": "Pharmacy"
    }, ""))

    p3 = generate_patient_id()
    patients[p3] = {"name": "Charlie Brown", "age": 12, "gender": "Male", "blood_group": "B+", "contact": "555-0301", "emergency_contact": "555-0302"}
    blockchain.add_block(Block(len(blockchain.chain), time.time(), {
        "patient_id": p3, "patient_name": "Charlie Brown", "record_type": "vaccination",
        "doctor": "Dr. Seuss", "description": "Flu shot", "date": "2023-10-03", "department": "Pediatrics"
    }, ""))

seed_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/patients/register', methods=['POST'])
def register_patient():
    data = request.get_json()
    required_fields = ['name', 'age', 'gender', 'blood_group', 'contact', 'emergency_contact']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
    pid = generate_patient_id()
    patients[pid] = {k: data[k] for k in required_fields}
    patients[pid]['id'] = pid
    
    return jsonify({"message": "Patient registered successfully", "patient_id": pid}), 201

@app.route('/api/records/add', methods=['POST'])
def add_record():
    data = request.get_json()
    required_fields = ['patient_id', 'record_type', 'doctor', 'description', 'date', 'department']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
    patient_id = data['patient_id']
    if patient_id not in patients:
        return jsonify({"error": "Patient not found"}), 404
        
    record_data = {
        "patient_id": patient_id,
        "patient_name": patients[patient_id]['name'],
        "record_type": data['record_type'],
        "doctor": data['doctor'],
        "description": data['description'],
        "date": data['date'],
        "department": data['department']
    }
    
    new_block = Block(len(blockchain.chain), time.time(), record_data, "")
    blockchain.add_block(new_block)
    
    return jsonify({"message": "Record added to blockchain successfully", "block_index": new_block.index, "block_hash": new_block.hash}), 201

@app.route('/api/records/<patient_id>', methods=['GET'])
def get_records(patient_id):
    if patient_id not in patients:
        return jsonify({"error": "Patient not found"}), 404
    
    records = []
    for block in blockchain.chain[1:]:
        if isinstance(block.data, dict) and block.data.get('patient_id') == patient_id:
            record = block.data.copy()
            record['block_hash'] = block.hash
            record['block_index'] = block.index
            records.append(record)
    
    patient_info = patients[patient_id].copy()
    patient_info['id'] = patient_id
    return jsonify({"patient_id": patient_id, "patient": patient_info, "records": records}), 200

@app.route('/api/blockchain', methods=['GET'])
def get_blockchain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append({
            "index": block.index,
            "timestamp": block.timestamp,
            "data": block.data,
            "previous_hash": block.previous_hash,
            "nonce": block.nonce,
            "hash": block.hash
        })
    return jsonify({"length": len(chain_data), "chain": chain_data}), 200

@app.route('/api/blockchain/validate', methods=['GET'])
def validate_blockchain():
    is_valid = blockchain.is_chain_valid()
    return jsonify({"is_valid": is_valid}), 200

@app.route('/api/patients', methods=['GET'])
def get_patients():
    patient_list = []
    for pid, details in patients.items():
        p = details.copy()
        if 'id' not in p:
            p['id'] = pid
        patient_list.append(p)
    return jsonify({"patients": patient_list}), 200

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_blocks = len(blockchain.chain)
    total_patients = len(patients)
    total_records = total_blocks - 1  # Excluding genesis block
    is_valid = blockchain.is_chain_valid()
    
    return jsonify({
        "total_blocks": total_blocks,
        "total_patients": total_patients,
        "total_records": total_records,
        "chain_valid": is_valid
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
