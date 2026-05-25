from flask import Flask, request, jsonify
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Inicializar Presidio
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Adicionar reconhecedores brasileiros
cpf_recognizer = PatternRecognizer(
    supported_entity="BR_CPF",
    patterns=[Pattern(name="cpf", regex=r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}", score=0.95)],
    context=["cpf", "CPF", "documento"]
)

rg_recognizer = PatternRecognizer(
    supported_entity="BR_RG",
    patterns=[Pattern(name="rg", regex=r"\d{1,2}\.?\d{3}\.?\d{3}-?[\dxX]?", score=0.85)],
    context=["rg", "RG", "identidade"]
)

phone_recognizer = PatternRecognizer(
    supported_entity="BR_PHONE",
    patterns=[Pattern(name="phone", regex=r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}", score=0.9)],
    context=["telefone", "celular", "tel", "whatsapp"]
)

cep_recognizer = PatternRecognizer(
    supported_entity="BR_CEP",
    patterns=[Pattern(name="cep", regex=r"\d{5}-?\d{3}", score=0.85)],
    context=["cep", "CEP", "endereço"]
)

analyzer.registry.add_recognizer(cpf_recognizer)
analyzer.registry.add_recognizer(rg_recognizer)
analyzer.registry.add_recognizer(phone_recognizer)
analyzer.registry.add_recognizer(cep_recognizer)

ENTITIES = [
    "PERSON", "BR_CPF", "BR_RG", "BR_PHONE", "BR_CEP",
    "EMAIL_ADDRESS", "LOCATION", "DATE_TIME", "PHONE_NUMBER"
]

@app.route('/')
def home():
    return """
    <h1>🔒 Presidio Anonymizer API</h1>
    <p>Status: <span style="color:green">Online 24/7</span></p>
    <p>Endpoints:</p>
    <ul>
        <li>POST /anonymize</li>
        <li>POST /deanonymize</li>
        <li>GET /health</li>
    </ul>
    """

@app.route('/health')
def health():
    return jsonify({
        "status": "online",
        "service": "Presidio Anonymizer",
        "uptime": "24/7"
    })

@app.route('/anonymize', methods=['POST'])
def anonymize():
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "Campo 'text' é obrigatório"
            }), 400
        
        text = data['text']
        
        app.logger.info(f"Analisando texto de {len(text)} caracteres")
        
        # Analisar com Presidio
        results = analyzer.analyze(
            text=text,
            entities=ENTITIES,
            language='pt'
        )
        
        # Criar mapeamento
        mapping = {}
        counters = {}
        
        # Ordenar resultados do final para o início (evitar deslocamento de índices)
        results_sorted = sorted(results, key=lambda x: x.start, reverse=True)
        
        # Texto anonimizado (começa como original)
        anonymized_text = text
        
        for result in results_sorted:
            entity_type = result.entity_type
            original_value = text[result.start:result.end]
            
            # Incrementar contador por tipo
            if entity_type not in counters:
                counters[entity_type] = 1
            else:
                counters[entity_type] += 1
            
            # Nomes amigáveis para placeholders
            type_names = {
                "PERSON": "NOME",
                "BR_CPF": "CPF",
                "BR_RG": "RG",
                "BR_PHONE": "TELEFONE",
                "BR_CEP": "CEP",
                "EMAIL_ADDRESS": "EMAIL",
                "LOCATION": "LOCAL",
                "DATE_TIME": "DATA",
                "PHONE_NUMBER": "TELEFONE"
            }
            
            type_name = type_names.get(entity_type, "DADO")
            placeholder = f"[{type_name}_{counters[entity_type]}]"
            
            # Substituir no texto
            anonymized_text = anonymized_text[:result.start] + placeholder + anonymized_text[result.end:]
            
            # Salvar no mapeamento
            mapping[placeholder] = original_value
            
            app.logger.info(f"  ✓ {original_value} → {placeholder}")
        
        app.logger.info(f"✅ Total anonimizado: {len(results)} entidades")
        
        return jsonify({
            "success": True,
            "anonymized_text": anonymized_text,
            "mapping": mapping,
            "count": len(results),
            "entities_found": counters,
            "details": [
                {
                    "type": r.entity_type,
                    "original": text[r.start:r.end],
                    "score": r.score
                }
                for r in results
            ]
        })
        
    except Exception as e:
        app.logger.error(f"Erro: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/deanonymize', methods=['POST'])
def deanonymize():
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "Campos 'text' e 'mapping' são obrigatórios"
            }), 400
        
        text = data['text']
        mapping = data.get('mapping', {})
        
        # Reverter placeholders (do maior para o menor para evitar conflitos)
        for placeholder in sorted(mapping.keys(), key=len, reverse=True):
            text = text.replace(placeholder, mapping[placeholder])
        
        return jsonify({
            "success": True,
            "original_text": text
        })
        
    except Exception as e:
        app.logger.error(f"Erro: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Render usa porta 10000 por padrão
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
