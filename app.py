from flask import Flask, request, jsonify
import re
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Padrões brasileiros para anonimização
PATTERNS = {
    'CPF': r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}',
    'RG': r'\d{1,2}\.?\d{3}\.?\d{3}-?[\dxX]?',
    'TELEFONE': r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}',
    'CEP': r'\d{5}-?\d{3}',
    'EMAIL': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'DATA': r'\d{2}[\/\-]\d{2}[\/\-]\d{4}',
    'PLACA': r'[A-Z]{3}[-\s]?\d{4}',
}

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Anonymizer API",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/anonymize', methods=['POST'])
def anonymize():
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({"success": False, "error": "Texto vazio"}), 400
        
        mapping = {}
        counters = {}
        anonymized = text
        
        # Aplicar cada padrão
        for entity_type, pattern in PATTERNS.items():
            def replace_match(match, etype=entity_type):
                nonlocal counters, mapping
                original = match.group(0)
                
                if etype not in counters:
                    counters[etype] = 1
                else:
                    counters[etype] += 1
                
                placeholder = f"[{etype}_{counters[etype]}]"
                mapping[placeholder] = original
                return placeholder
            
            anonymized = re.sub(pattern, replace_match, anonymized, flags=re.IGNORECASE)
        
        app.logger.info(f"✅ {len(mapping)} dados anonimizados")
        
        return jsonify({
            "success": True,
            "anonymized_text": anonymized,
            "mapping": mapping,
            "count": len(mapping)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/deanonymize', methods=['POST'])
def deanonymize():
    try:
        data = request.get_json()
        text = data.get('text', '')
        mapping = data.get('mapping', {})
        
        for placeholder, original in mapping.items():
            text = text.replace(placeholder, original)
        
        return jsonify({"success": True, "original_text": text})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
