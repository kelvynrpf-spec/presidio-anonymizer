from flask import Flask, request, jsonify
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ⚡ CONFIGURAÇÃO LEVE - Apenas português
nlp_config = {
    "nlp_engine_name": "spacy",
    "models": [
        {
            "lang_code": "pt",
            "model_name": "pt_core_news_sm"  # Modelo pequeno (13MB)
        }
    ]
}

# Criar NLP Engine apenas com português
provider = NlpEngineProvider(nlp_configuration=nlp_config)
nlp_engine = provider.create_engine()

# Inicializar Presidio com configuração leve
analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
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

# Apenas entidades que funcionam com modelo português
ENTITIES = [
    "PERSON",        # Nomes (funciona com pt_core_news_sm)
    "LOCATION",      # Locais
    "DATE_TIME",     # Datas
    "BR_CPF",        # CPF
    "BR_RG",         # RG
    "BR_PHONE",      # Telefone
    "BR_CEP",        # CEP
]

@app.route('/')
def home():
    return jsonify({
        "service": "Presidio Anonymizer API",
        "status": "online",
        "memory": "otimizado para 512MB",
        "endpoints": ["/health", "/anonymize", "/deanonymize"]
    })

@app.route('/health')
def health():
    return jsonify({"status": "online", "uptime": "24/7"})

@app.route('/anonymize', methods=['POST'])
def anonymize():
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"success": False, "error": "Campo 'text' é obrigatório"}), 400
        
        text = data['text']
        app.logger.info(f"Analisando texto ({len(text)} caracteres)")
        
        # Analisar com Presidio
        results = analyzer.analyze(
            text=text,
            entities=ENTITIES,
            language='pt'
        )
        
        mapping = {}
        counters = {}
        
        # Ordenar do final para início
        results_sorted = sorted(results, key=lambda x: x.start, reverse=True)
        anonymized_text = text
        
        for result in results_sorted:
            entity_type = result.entity_type
            original_value = text[result.start:result.end]
            
            if entity_type not in counters:
                counters[entity_type] = 1
            else:
                counters[entity_type] += 1
            
            type_names = {
                "PERSON": "NOME",
                "BR_CPF": "CPF",
                "BR_RG": "RG",
                "BR_PHONE": "TELEFONE",
                "BR_CEP": "CEP",
                "LOCATION": "LOCAL",
                "DATE_TIME": "DATA",
            }
            
            type_name = type_names.get(entity_type, "DADO")
            placeholder = f"[{type_name}_{counters[entity_type]}]"
            
            anonymized_text = anonymized_text[:result.start] + placeholder + anonymized_text[result.end:]
            mapping[placeholder] = original_value
        
        app.logger.info(f"✅ {len(results)} entidades anonimizadas")
        
        return jsonify({
            "success": True,
            "anonymized_text": anonymized_text,
            "mapping": mapping,
            "count": len(results),
            "entities_found": counters
        })
        
    except Exception as e:
        app.logger.error(f"Erro: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/deanonymize', methods=['POST'])
def deanonymize():
    try:
        data = request.get_json()
        text = data.get('text', '')
        mapping = data.get('mapping', {})
        
        # Reverter placeholders (do maior para o menor)
        for placeholder in sorted(mapping.keys(), key=len, reverse=True):
            text = text.replace(placeholder, mapping[placeholder])
        
        return jsonify({"success": True, "original_text": text})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 🚀 Inicialização do modelo (carregar na memória)
@app.before_first_request
def load_model():
    """Pré-carrega o modelo português para evitar timeout"""
    try:
        import spacy
        nlp = spacy.load("pt_core_news_sm")
        app.logger.info("✅ Modelo português carregado com sucesso!")
    except Exception as e:
        app.logger.error(f"Erro ao carregar modelo: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
