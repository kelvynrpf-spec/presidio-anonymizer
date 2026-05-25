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
    'PLACA': r'[A-Z]{3}[-\s]?\d{4}',
}

# Lista de nomes e sobrenomes comuns brasileiros
NOMES_COMUNS = [
    'kelvyn', 'renan', 'barboza', 'alves',
    'joão', 'maria', 'josé', 'ana', 'carlos', 'paulo', 'pedro', 'lucas',
    'marcos', 'antônio', 'francisco', 'luiz', 'fernando', 'roberto', 'ricardo',
    'eduardo', 'marcelo', 'andré', 'rafael', 'felipe', 'bruno', 'rodrigo',
    'gustavo', 'daniel', 'leonardo', 'thiago', 'fabio', 'diego', 'alexandre',
    'renato', 'sandra', 'patricia', 'camila', 'juliana', 'amanda', 'beatriz',
    'carla', 'vanessa', 'mariana', 'larissa', 'isabela', 'fernanda', 'raquel',
    'adriana', 'alessandra', 'alice', 'aline', 'ana clara', 'ana julia',
    'ana luiza', 'ana paula', 'anderson', 'andréia', 'angela', 'antonia',
    'augusto', 'bárbara', 'bianca', 'brenda', 'caio', 'caroline', 'catarina',
    'cecilia', 'celso', 'cesar', 'clara', 'claudia', 'claudio', 'cristiane',
    'cristina', 'daiane', 'dalva', 'daniela', 'danilo', 'davi', 'denise',
    'douglas', 'edson', 'elaine', 'elias', 'elisangela', 'emanuel', 'emanuelle',
    'emerson', 'enrico', 'erica', 'erika', 'esther', 'evelyn', 'fabiana',
    'fabricio', 'fátima', 'flavia', 'francieli', 'gabriel', 'gabriela',
    'gilberto', 'giovana', 'giovanna', 'gisela', 'guilherme', 'helena',
    'heloisa', 'henrique', 'igor', 'ingrid', 'isabel', 'isabella', 'isadora',
    'italo', 'ivan', 'ivone', 'jacqueline', 'jéssica', 'joana', 'jorge',
    'julia', 'julio', 'karen', 'kelly', 'laura', 'leandro', 'leticia',
    'lilian', 'lorena', 'luana', 'luciana', 'luciano', 'luis', 'luisa',
    'maicon', 'marcelo', 'marcia', 'marcio', 'marcos', 'margarida',
    'marina', 'mario', 'marta', 'mateus', 'mauricio', 'michele', 'miguel',
    'mirela', 'monica', 'murilo', 'natália', 'nathalia', 'nelson', 'nicolas',
    'odair', 'orlando', 'osvaldo', 'otavio', 'pamela', 'patricia', 'paula',
    'priscila', 'rafaela', 'regina', 'renata', 'rogerio', 'romulo', 'ronaldo',
    'rosana', 'rose', 'rosemary', 'sabrina', 'samuel', 'sara', 'sergio',
    'sheila', 'silvana', 'simone', 'sonia', 'stefany', 'susana', 'tainara',
    'tamires', 'tatiane', 'teresa', 'thais', 'tiago', 'valeria', 'vanderlei',
    'vera', 'vicente', 'victor', 'vinicius', 'vivian', 'wagner', 'wesley',
    'william', 'wilson', 'yago', 'yuri',
    # Sobrenomes
    'silva', 'santos', 'oliveira', 'souza', 'pereira', 'lima', 'costa',
    'ferreira', 'rodrigues', 'almeida', 'nascimento', 'araujo', 'barbosa',
    'cardoso', 'carvalho', 'castro', 'dias', 'gomes', 'martins', 'ribeiro',
    'machado', 'moraes', 'teixeira', 'cavalcanti', 'freitas', 'gonçalves',
    'andrade', 'azevedo', 'barros', 'borges', 'campos', 'correia', 'cunha',
    'duarte', 'fernandes', 'figueiredo', 'fonseca', 'guimarães', 'leite',
    'lopes', 'maciel', 'marques', 'medeiros', 'mendes', 'miranda', 'monteiro',
    'moreira', 'moura', 'neves', 'nunes', 'paiva', 'pinto', 'ramos', 'reis',
    'rocha', 'sales', 'santiago', 'soares', 'torres', 'vieira', 'xavier',
    'amorim', 'assunção', 'avila', 'batista', 'belo', 'branco', 'brito',
    'coelho', 'cordeiro', 'coutinho', 'cruz', 'farias', 'galvão',
    'garcia', 'guerra', 'leão', 'lobo', 'madeira', 'maia', 'marinho',
    'melo', 'meneses', 'mesquita', 'morais', 'pacheco',
    'passos', 'peixoto', 'pimenta', 'queiroz', 'rego', 'rosa',
    'tavares', 'teles', 'trindade', 'valente', 'veiga',
    'viana', 'vidal', 'vilela'
]

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Anonymizer API",
        "version": "2.0.0"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def detectar_nomes(texto):
    """Detecta e retorna lista de nomes completos encontrados"""
    palavras = texto.split()
    nomes_encontrados = []
    nome_atual = []
    
    for i, palavra in enumerate(palavras):
        palavra_limpa = palavra.lower().strip(',.!?;:()[]{}"\'')
        
        if palavra_limpa in NOMES_COMUNS:
            nome_atual.append(palavra)
        else:
            if len(nome_atual) >= 2:
                nomes_encontrados.append(' '.join(nome_atual))
            nome_atual = []
    
    # Verificar se sobrou nome no final
    if len(nome_atual) >= 2:
        nomes_encontrados.append(' '.join(nome_atual))
    
    return nomes_encontrados

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
        
        # 1. Anonimizar nomes próprios primeiro
        nomes = detectar_nomes(anonymized)
        for nome in nomes:
            if 'NOME' not in counters:
                counters['NOME'] = 1
            else:
                counters['NOME'] += 1
            
            placeholder = f"[NOME_{counters['NOME']}]"
            mapping[placeholder] = nome
            
            # Substituir nome completo (case insensitive)
            pattern = re.compile(re.escape(nome), re.IGNORECASE)
            anonymized = pattern.sub(placeholder, anonymized)
        
        # 2. Aplicar padrões de documentos
        for entity_type, pattern in PATTERNS.items():
            # Ignorar DATA para preservar no BO
            if entity_type == 'DATA':
                continue
            
            matches = list(re.finditer(pattern, anonymized, re.IGNORECASE))
            
            for match in reversed(matches):
                original = match.group(0)
                
                if entity_type not in counters:
                    counters[entity_type] = 1
                else:
                    counters[entity_type] += 1
                
                placeholder = f"[{entity_type}_{counters[entity_type]}]"
                mapping[placeholder] = original
                
                start, end = match.span()
                anonymized = anonymized[:start] + placeholder + anonymized[end:]
        
        app.logger.info(f"✅ {len(mapping)} dados anonimizados (incluindo nomes)")
        
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
