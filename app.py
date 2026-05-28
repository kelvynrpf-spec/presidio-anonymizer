from flask import Flask, request, jsonify
import re
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ============================================
# NOMES COMUNS (AMPLIADO)
# ============================================
NOMES_COMUNS = set([
    # Nomes próprios
    'kelvyn', 'renan', 'barboza', 'alves',
    'joão', 'joao', 'maria', 'josé', 'jose', 'ana', 'carlos', 'paulo', 'pedro', 'lucas',
    'marcos', 'antônio', 'antonio', 'francisco', 'luiz', 'luis', 'fernando',
    'roberto', 'ricardo', 'eduardo', 'marcelo', 'andré', 'andre', 'rafael',
    'felipe', 'bruno', 'rodrigo', 'gustavo', 'daniel', 'leonardo', 'thiago',
    'tiago', 'fabio', 'fábio', 'diego', 'alexandre', 'renato', 'sandra',
    'patricia', 'patrícia', 'camila', 'juliana', 'amanda', 'beatriz', 'carla',
    'vanessa', 'mariana', 'larissa', 'isabela', 'fernanda', 'raquel',
    'gabriel', 'gabriela', 'miguel', 'sophia', 'davi', 'alice', 'arthur',
    'laura', 'bernardo', 'valentina', 'heitor', 'helena', 'enzo', 'isabella',
    'theo', 'manuela', 'lorenzo', 'júlia', 'julia', 'nicolas', 'luiza',
    'henry', 'eloá', 'eloa', 'samuel', 'marina', 'vitor', 'giovanna',
    'eduarda', 'emanuel', 'emanuelle', 'benjamin', 'bianca', 'ryan',
    'nicole', 'lucca', 'yasmin', 'caio', 'larissa', 'pietro', 'esther',
    'vitoria', 'vitória', 'agatha', 'ágatha', 'bryan', 'sarah', 'cauã',
    'caua', 'isadora', 'vitor', 'melissa', 'matheus', 'mateus', 'olivia',
    'vinicius', 'vinícius', 'céu', 'ceu', 'noah', 'liz', 'joaquim',
    'isabelly', 'isabely', 'maite', 'maitê', 'levi', 'luna', 'anthony',
    'thomas', 'clara', 'ícaro', 'icaro', 'leticia', 'letícia', 'malu',
    'otávio', 'otavio', 'lara', 'augusto', 'cecilia', 'cecília',
    'ravi', 'aurora', 'benicio', 'benício', 'heloisa', 'heloísa',
    'israel', 'elisa', 'stella', 'rebeca', 'maya', 'antonella',
    'lívia', 'livia', 'alícia', 'alicia', 'emanuely', 'israeli',
    'murilo', 'joaquina', 'adriana', 'adriano', 'alessandra', 'alessandro',
    'alex', 'alexandre', 'alice', 'aline', 'allan', 'amanda', 'ana',
    'anderson', 'andré', 'andre', 'andrea', 'andréia', 'andreia',
    'angela', 'ângela', 'anna', 'antonia', 'antônia', 'antônio', 'antonio',
    'ariane', 'ariana', 'barbara', 'bárbara', 'beatriz', 'bianca',
    'brenda', 'bruna', 'bruno', 'camila', 'camille', 'carina', 'carine',
    'carol', 'carolina', 'caroline', 'cassia', 'cássia', 'cassio', 'cássio',
    'catarina', 'catherine', 'célia', 'celia', 'cesar', 'césar', 'christian',
    'cintia', 'cíntia', 'clara', 'clarice', 'claudia', 'cláudia', 'claudio',
    'cláudio', 'cleber', 'cléber', 'cristian', 'cristiane', 'cristiano',
    'daiana', 'daiane', 'daiara', 'dalila', 'damaris', 'daniel', 'daniela',
    'danielle', 'davi', 'dayane', 'debora', 'débora', 'denise', 'diana',
    'diego', 'diogo', 'douglas', 'eder', 'éder', 'edson', 'eduarda',
    'eduardo', 'elaine', 'elena', 'eliana', 'eliane', 'elias', 'elisa',
    'elisabete', 'elizabeth', 'ellen', 'emanuel', 'emanuele', 'emanuelly',
    'emerson', 'emily', 'eric', 'erica', 'érica', 'erika', 'estefani',
    'estefanie', 'estela', 'ester', 'esther', 'evelyn', 'evandro',
    'fabiana', 'fabiano', 'fabio', 'fábio', 'fabricio', 'fabrício',
    'fatima', 'fátima', 'felipe', 'fernanda', 'fernando', 'flavia',
    'flávia', 'flavio', 'flávio', 'franciele', 'francieli', 'francine',
    'francis', 'francisco', 'gabriel', 'gabriela', 'gabriella', 'gabrielly',
    'geovana', 'geovane', 'gerson', 'gilberto', 'gilmar', 'gilson',
    'giovana', 'giovane', 'giovanna', 'giovanni', 'gisela', 'giselle',
    'guilherme', 'gustavo', 'heitor', 'helena', 'heloisa', 'heloísa',
    'henrique', 'hugo', 'igor', 'ingrid', 'isabel', 'isabela', 'isabella',
    'isabelly', 'isadora', 'isaias', 'isaías', 'israel', 'italo', 'ícaro',
    'jackson', 'jacqueline', 'jairo', 'james', 'janaina', 'janaína',
    'jean', 'jefferson', 'jenifer', 'jennifer', 'jessica', 'jéssica',
    'joana', 'joaquim', 'joel', 'jonas', 'jonathan', 'jorge', 'josé',
    'jose', 'josiane', 'julia', 'júlia', 'juliana', 'juliano', 'julio',
    'júlio', 'junior', 'júnior', 'karen', 'karina', 'karine', 'karla',
    'kathleen', 'katia', 'kátia', 'kelly', 'ketlin', 'kevin', 'laiane',
    'lais', 'laís', 'lara', 'larissa', 'laura', 'leandro', 'leonardo',
    'leticia', 'letícia', 'lidia', 'lídia', 'lilian', 'liliane', 'lorena',
    'lorenzo', 'lourdes', 'luana', 'lucas', 'lucia', 'lúcia', 'luciana',
    'luciano', 'luciene', 'lucilene', 'lucio', 'lúcio', 'luis', 'luiz',
    'luiza', 'luíza', 'luna', 'luzia', 'maicon', 'maira', 'maíra',
    'marcela', 'marcelo', 'marcio', 'márcio', 'marcos', 'marcus',
    'margarete', 'maria', 'mária', 'mariana', 'mariane', 'marilia',
    'marília', 'marina', 'mario', 'mário', 'marisa', 'marlene', 'marta',
    'mateus', 'matheus', 'mauricio', 'maurício', 'mauro', 'melissa',
    'michele', 'michel', 'miguel', 'milena', 'mirela', 'miriam', 'moises',
    'moisés', 'monica', 'mônica', 'murilo', 'naiara', 'natacha', 'natalia',
    'natália', 'nathalia', 'nathália', 'nathan', 'nayara', 'nelson',
    'nicolas', 'nicole', 'nilson', 'noah', 'noemi', 'odair', 'olivia',
    'orlando', 'osmar', 'osvaldo', 'otavio', 'otávio', 'pablo', 'pamela',
    'pâmela', 'patricia', 'patrícia', 'patrick', 'paula', 'paulo',
    'pedro', 'priscila', 'priscilla', 'rafael', 'rafaela', 'raissa',
    'raíssa', 'raphael', 'raquel', 'ravi', 'rebeca', 'regina', 'renan',
    'renata', 'renato', 'ricardo', 'rita', 'roberta', 'roberto', 'rodolfo',
    'rodrigo', 'roger', 'rogério', 'rogerio', 'romario', 'romário',
    'ronaldo', 'rony', 'rosana', 'rosane', 'rosangela', 'rosângela',
    'rose', 'rosemary', 'rosiane', 'rosilene', 'rosimeire', 'rubens',
    'rute', 'ryan', 'samanta', 'samantha', 'samara', 'samuel', 'sandra',
    'sara', 'sarah', 'saulo', 'sebastião', 'sebastiao', 'sergio', 'sérgio',
    'sheila', 'shirley', 'sidney', 'silvana', 'silvia', 'sílvia', 'simone',
    'sofia', 'sophia', 'stefani', 'stefanie', 'stefany', 'stella',
    'stephanie', 'suelen', 'sueli', 'suzana', 'taina', 'tainá', 'tais',
    'taís', 'talita', 'tamara', 'tâmara', 'tania', 'tânia', 'tatiana',
    'tatiely', 'tatiane', 'tayna', 'taysa', 'teresa', 'thais', 'thaís',
    'thales', 'thalia', 'thalia', 'theo', 'thomas', 'tiago', 'tiffany',
    'valdir', 'valentina', 'valeria', 'valéria', 'vanessa', 'vera',
    'veronica', 'verônica', 'victor', 'vinicius', 'vinícius', 'vitor',
    'vitória', 'vitoria', 'vivian', 'viviane', 'wagner', 'walter',
    'wellington', 'wendel', 'wesley', 'wilson', 'yasmin', 'yuri',
    
    # Sobrenomes comuns
    'silva', 'santos', 'oliveira', 'souza', 'pereira', 'lima', 'costa',
    'ferreira', 'rodrigues', 'almeida', 'nascimento', 'araujo', 'barbosa',
    'cardoso', 'carvalho', 'castro', 'dias', 'gomes', 'martins', 'ribeiro',
    'machado', 'moraes', 'teixeira', 'cavalcanti', 'freitas', 'gonçalves',
    'andrade', 'azevedo', 'barros', 'borges', 'campos', 'correia',
    'cunha', 'duarte', 'fernandes', 'figueiredo', 'fonseca', 'guimarães',
    'leite', 'lopes', 'maciel', 'marques', 'medeiros', 'mendes',
    'miranda', 'monteiro', 'moreira', 'moura', 'neves', 'nunes', 'paiva',
    'pinto', 'ramos', 'reis', 'rocha', 'sales', 'santiago', 'soares', 'torres',
    'vieira', 'xavier', 'abreu', 'aguiar', 'albano', 'alcantara', 'alcântara',
    'amaral', 'amorim', 'anchieta', 'aparecido', 'aquino', 'assis', 'baptista',
    'bastos', 'belchior', 'bento', 'bernardes', 'bezerra', 'bonfim', 'botelho',
    'brito', 'caires', 'caldeira', 'camargo', 'candido', 'carmo', 'carneiro',
    'cavalcante', 'chaves', 'coelho', 'conceição', 'conceicao', 'cordoba',
    'coutinho', 'cruz', 'damasceno', 'dantas', 'domingues', 'dutra',
    'esteves', 'evangelista', 'farias', 'faustino', 'felix', 'filho',
    'fontes', 'franco', 'froes', 'furtado', 'galdino', 'galvão', 'galvao',
    'garcia', 'gaspar', 'gimenez', 'guerra', 'henriques', 'jesus',
    'junior', 'lacerda', 'leal', 'lemos', 'lins', 'macedo', 'madeira',
    'magalhães', 'magalhaes', 'maia', 'marinho', 'matos', 'melhor',
    'mello', 'melo', 'mendonça', 'mendonca', 'mesquita', 'modesto',
    'montenegro', 'morais', 'mota', 'navarro', 'neto', 'nogueira',
    'noronha', 'orta', 'paes', 'paranhos', 'passos', 'pastor', 'paz',
    'pedrosa', 'penha', 'peixoto', 'pessoa', 'pimenta', 'pimentel',
    'pinheiro', 'pontes', 'porto', 'prado', 'quaresma', 'queiroz',
    'quirino', 'rego', 'rezende', 'rios', 'salles', 'sanches', 'saraiva',
    'severo', 'simpício', 'simplicio', 'siqueira', 'sobrinho', 'sodré',
    'sodre', 'tavares', 'terra', 'trindade', 'vargas', 'vasconcelos',
    'vasques', 'veloso', 'vianna', 'vidal', 'vilhena', 'zanetti',
])

# ============================================
# ✅ PADRÕES CORRIGIDOS E OTIMIZADOS
# ============================================
PATTERNS = {
    'TELEFONE': r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}',
    'CPF': r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}',
    'CNPJ': r'\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}',
    'CEP': r'\d{5}-?\d{3}',
    'EMAIL': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'PLACA': r'\b[A-Z]{3}[-\s]?\d{4}\b',
    'RG': r'\d{1,2}\.?\d{3}\.?\d{3}-?[\dxX]?',
    'AGENCIA': r'agência\s+(\d{1,4}-?\d?)',
    'CONTA': r'conta\s*(corrente|poupança)?\s+(\d{4,8}-?\d{0,2})',
}

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Anonymizer API",
        "version": "3.2",
        "patterns": list(PATTERNS.keys()),
        "nomes_comuns": len(NOMES_COMUNS)
    })

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
        
        # 1. Proteger datas (não anonimizar)
        datas = []
        def proteger_data(m):
            datas.append(m.group(0))
            return f'__DATA_{len(datas)-1}__'
        text = re.sub(r'\d{2}[\/\-]\d{2}[\/\-]\d{4}', proteger_data, text)
        
        # 2. Anonimizar nomes próprios
        text, nome_mapping = detectar_e_anonimizar_nomes(text)
        full_mapping.update(nome_mapping)
        if nome_mapping:
            full_counters['NOME'] = len(nome_mapping)
        
        # 3. Anonimizar padrões (telefone, CPF, email, etc.)
        for entity_type, pattern in PATTERNS.items():
            try:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                
                for match in reversed(matches):
                    # Para AGENCIA e CONTA, capturar apenas o número (grupo)
                    if entity_type == 'AGENCIA' and match.lastindex and match.lastindex >= 1:
                        original = match.group(1)
                        start, end = match.span(1)
                    elif entity_type == 'CONTA' and match.lastindex and match.lastindex >= 2:
                        original = match.group(2)
                        start, end = match.span(2)
                    else:
                        original = match.group(0)
                        start, end = match.span()
                    
                    # Verificar se este trecho já foi anonimizado
                    if any(placeholder in text[start:end] for placeholder in full_mapping.keys()):
                        continue
                    
                    if entity_type not in full_counters:
                        full_counters[entity_type] = 1
                    else:
                        full_counters[entity_type] += 1
                    
                    placeholder = f'[{entity_type}_{full_counters[entity_type]}]'
                    full_mapping[placeholder] = original
                    
                    text = text[:start] + placeholder + text[end:]
            except Exception as e:
                app.logger.warning(f'⚠️ Erro no padrão {entity_type}: {str(e)}')
                continue
        
        # 4. Restaurar datas
        for i, data in enumerate(datas):
            text = text.replace(f'__DATA_{i}__', data)
        
        total = len(full_mapping)
        app.logger.info(f'✅ {total} dados anonimizados: {list(full_counters.keys())}')
        
        return jsonify({
            "success": True,
            "anonymized_text": text,
            "mapping": full_mapping,
            "count": total,
            "types_found": full_counters
        })
        
    except Exception as e:
        app.logger.error(f'❌ Erro na anonimização: {str(e)}')
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/deanonymize', methods=['POST'])
def deanonymize():
    try:
        data = request.get_json()
        text = data.get('text', '')
        mapping = data.get('mapping', {})
        
        # Ordenar por tamanho (maior primeiro) para evitar substituições parciais
        for placeholder in sorted(mapping.keys(), key=len, reverse=True):
            text = text.replace(placeholder, mapping[placeholder])
        
        return jsonify({"success": True, "original_text": text})
        
    except Exception as e:
        app.logger.error(f'❌ Erro na desanonimização: {str(e)}')
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
