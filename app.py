from flask import Flask, request, jsonify
import re
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

NOMES_COMUNS = set([
    'kelvyn', 'renan', 'barboza', 'alves',
    'joão', 'maria', 'josé', 'ana', 'carlos', 'paulo', 'pedro', 'lucas',
    'marcos', 'antônio', 'antonio', 'francisco', 'luiz', 'luis', 'fernando',
    'roberto', 'ricardo', 'eduardo', 'marcelo', 'andré', 'andre', 'rafael',
    'felipe', 'bruno', 'rodrigo', 'gustavo', 'daniel', 'leonardo', 'thiago',
    'tiago', 'fabio', 'fábio', 'diego', 'alexandre', 'renato', 'sandra',
    'patricia', 'patrícia', 'camila', 'juliana', 'amanda', 'beatriz', 'carla',
    'vanessa', 'mariana', 'larissa', 'isabela', 'fernanda', 'raquel',
    'silva', 'santos', 'oliveira', 'souza', 'pereira', 'lima', 'costa',
    'ferreira', 'rodrigues', 'almeida', 'nascimento', 'araujo', 'barbosa',
    'cardoso', 'carvalho', 'castro', 'dias', 'gomes', 'martins', 'ribeiro',
    'machado', 'moraes', 'teixeira', 'cavalcanti', 'freitas', 'gonçalves',
    'andrade', 'azevedo', 'barros', 'borges', 'campos', 'correia',
    'cunha', 'duarte', 'fernandes', 'figueiredo', 'fonseca', 'guimarães',
    'leite', 'lopes', 'maciel', 'marques', 'medeiros', 'mendes',
    'miranda', 'monteiro', 'moreira', 'moura', 'neves', 'nunes', 'paiva',
    'pinto', 'ramos', 'reis', 'rocha', 'sales', 'santiago', 'soares', 'torres',
    'vieira', 'xavier',
])

# ✅ CORRIGIDO: Removidos os look-behinds com largura variável
PATTERNS = {
    'CPF': r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}',
    'CNPJ': r'\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}',
    'RG': r'\d{1,2}\.?\d{3}\.?\d{3}-?[\dxX]?',
    'TELEFONE': r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}',
    'CEP': r'\d{5}-?\d{3}',
    'EMAIL': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'PLACA': r'[A-Z]{3}[-\s]?\d{4}',
    
    # ✅ CORRIGIDO: Sem look-behind, apenas captura o número
    'AGENCIA': r'agência\s+(\d{1,4}-?\d?)',
    'CONTA': r'conta\s*(corrente|poupança)?\s+(\d{4,8}-?\d{0,2})',
}

@app.route('/')
def home():
    return jsonify({"status": "online", "service": "Anonymizer API", "version": "3.1"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def detectar_e_anonimizar_nomes(texto):
    palavras = re.split(r'(\s+)', texto)
    mapping = {}
    nome_atual = []
    nome_indices = []
    counter = 1
    
    for i, palavra in enumerate(palavras):
        palavra_limpa = palavra.strip().lower().strip(',.!?;:()[]{}"\'')
        
        if palavra_limpa and palavra_limpa in NOMES_COMUNS:
            nome_atual.append(palavra)
            nome_indices.append(i)
        else:
            if len(nome_atual) >= 2:
                nome_original = ''.join(nome_atual)
                placeholder = f'[NOME_{counter}]'
                mapping[placeholder] = nome_original
                
                for idx in sorted(nome_indices, reverse=True):
                    palavras[idx] = ''
                
                palavras[nome_indices[0]] = placeholder + (' ' if len(nome_indices) > 1 else '')
                counter += 1
            
            nome_atual = []
            nome_indices = []
    
    if len(nome_atual) >= 2:
        nome_original = ''.join(nome_atual)
        placeholder = f'[NOME_{counter}]'
        mapping[placeholder] = nome_original
        
        for idx in sorted(nome_indices, reverse=True):
            palavras[idx] = ''
        palavras[nome_indices[0]] = placeholder
    
    return ''.join(palavras), mapping

@app.route('/anonymize', methods=['POST'])
def anonymize():
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({"success": False, "error": "Texto vazio"}), 400
        
        full_mapping = {}
        full_counters = {}
        
        # 1. Proteger datas
        datas = []
        def proteger_data(m):
            datas.append(m.group(0))
            return f'__DATA_{len(datas)-1}__'
        text = re.sub(r'\d{2}[\/\-]\d{2}[\/\-]\d{4}', proteger_data, text)
        
        # 2. Anonimizar nomes
        text, nome_mapping = detectar_e_anonimizar_nomes(text)
        full_mapping.update(nome_mapping)
        full_counters['NOME'] = len(nome_mapping)
        
        # 3. Anonimizar padrões
        for entity_type, pattern in PATTERNS.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            
            for match in reversed(matches):
                original = match.group(0)
                
                # ✅ CORRIGIDO: Para AGENCIA e CONTA, pegar apenas o número do grupo de captura
                if entity_type == 'AGENCIA' and match.lastindex and match.lastindex >= 1:
                    original = match.group(1)  # Pega só o número
                    start, end = match.span(1)
                elif entity_type == 'CONTA' and match.lastindex and match.lastindex >= 2:
                    original = match.group(2)  # Pega só o número da conta
                    start, end = match.span(2)
                else:
                    start, end = match.span()
                
                if entity_type not in full_counters:
                    full_counters[entity_type] = 1
                else:
                    full_counters[entity_type] += 1
                
                placeholder = f'[{entity_type}_{full_counters[entity_type]}]'
                full_mapping[placeholder] = original
                
                text = text[:start] + placeholder + text[end:]
        
        # 4. Restaurar datas
        for i, data in enumerate(datas):
            text = text.replace(f'__DATA_{i}__', data)
        
        total = len(full_mapping)
        app.logger.info(f'✅ {total} dados anonimizados')
        
        return jsonify({
            "success": True,
            "anonymized_text": text,
            "mapping": full_mapping,
            "count": total
        })
        
    except Exception as e:
        app.logger.error(f'❌ Erro: {str(e)}')
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/deanonymize', methods=['POST'])
def deanonymize():
    try:
        data = request.get_json()
        text = data.get('text', '')
        mapping = data.get('mapping', {})
        
        for placeholder in sorted(mapping.keys(), key=len, reverse=True):
            text = text.replace(placeholder, mapping[placeholder])
        
        return jsonify({"success": True, "original_text": text})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
