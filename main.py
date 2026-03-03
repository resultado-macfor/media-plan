import streamlit as st
import google.generativeai as genai
import os
from datetime import datetime
import json
import time

# Configuração inicial
st.set_page_config(
    layout="wide",
    page_title="Planejador Estratégico de Mídias - IA",
    page_icon="🎯"
)

# Inicializar Gemini
gemini_api_key = os.getenv("GEM_API_KEY")
genai.configure(api_key=gemini_api_key)
modelo = genai.GenerativeModel("gemini-2.5-flash")

# [Toda a base de conhecimento TIPOS_CAMPANHA, ETAPAS_FUNIL, KPIS_POR_ETAPA, 
#  PLATAFORMA_OBJETIVOS, BENCHMARKS_BR, TEMPLATES_ALOCACAO_BUDGET, 
#  get_funnel_context() permanecem IGUAIS ao código anterior]
# (mantido por brevidade - copiar do código anterior)

# ============================================================================
# FUNÇÕES DE GERAÇÃO COM SUPORTE A REFINAMENTO
# ============================================================================

def gerar_insights_iniciais(cliente, orcamento, objetivos, contexto, canais_preferencia, 
                           instrucoes_refinamento=None, versao_anterior=None):
    """Primeira etapa - análise inicial estratégica com suporte a refinamento"""
    
    if instrucoes_refinamento and versao_anterior:
        # Modo refinamento - ajustar versão existente
        prompt = f"""
Você é um Estrategista de Mídias Sênior. Abaixo está uma versão anterior da análise inicial para {cliente}.
O usuário pediu ajustes específicos. MANTENHA a estrutura geral do documento, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR DA ANÁLISE:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO DO USUÁRIO:**
{instrucoes_refinamento}

**INFORMAÇÕES DO CLIENTE (para contexto):**
- Cliente: {cliente}
- Orçamento Total: R$ {orcamento:,.2f}
- Objetivos Principais: {objetivos}
- Contexto: {contexto}

Retorne a versão COMPLETA da análise, mas aplicando apenas os refinamentos solicitados, 
mantendo a mesma estrutura de seções e todo o conteúdo não solicitado inalterado.
"""
    else:
        # Modo inicial
        prompt = f"""
Você é um Estrategista de Mídias Sênior com profundo conhecimento acadêmico e prático. 
Sua missão é fazer uma ANÁLISE INICIAL ESTRATÉGICA que será a base de todo o planejamento, 
utilizando frameworks consagrados (Binet & Field, Byron Sharp, McKinsey CDJ, STDC).

**Informações do Cliente:**
- Cliente: {cliente}
- Orçamento Total: R$ {orcamento:,.2f}
- Objetivos Principais: {objetivos}
- Contexto/Desafios: {contexto}
- Canais de Interesse: {canais_preferencia if canais_preferencia else "A IA deve definir os melhores canais"}

**BASE DE CONHECIMENTO ESTRATÉGICO (utilize estes conceitos):**

**Frameworks Teóricos:**
- **Binet & Field (60/40)**: Construção de marca (60%) é emocional, amplo alcance, efeitos em 6+ meses. Ativação (40%) é racional, segmentada, efeitos imediatos. A divisão ótima varia por contexto.
- **Byron Sharp (How Brands Grow)**: Crescimento vem de novos compradores, não fidelização. Priorizar ALCANCE sobre frequência. Ativos distintivos de marca > posicionamento diferenciado.
- **McKinsey CDJ**: Touchpoints na avaliação ativa são 2-3x mais influentes. Loop de fidelidade permite recompra direta.
- **STDC (Kaushik)**: See (maior audiência qualificada), Think (avaliação ativa), Do (transação), Care (clientes existentes).

**Benchmarks Brasil (incorpore nas análises):**
- CPM Meta Ads: R$8-25 (70-94% abaixo da média global - oportunidade única)
- CPC Meta: R$0.30-3.00 (média $0.38 - 66% abaixo global)
- WhatsApp: 93,7% penetração, 55% conversão, 6x mais que e-commerce
- Redes sociais: 53% do investimento digital
- Instagram: 92% dos usuários de internet

**Forneça uma análise em formato narrativo com:**

1. **ENTENDIMENTO DO NEGÓCIO**: O que você compreende sobre o cliente e seus desafios

2. **POTENCIAL DO ORÇAMENTO**: Análise realista do que pode ser alcançado com R$ {orcamento:,.2f} no contexto brasileiro

3. **PRIMEIRAS IMPRESSÕES ESTRATÉGICAS**: Direcionamentos iniciais baseados nos objetivos

4. **PERGUNTAS ESTRATÉGICAS**: O que mais precisamos considerar para aprofundar o planejamento?
"""
    response = modelo.generate_content(prompt)
    return response.text

def recomendar_arquitetura_canais(insights_iniciais, objetivos, orcamento, canais_preferencia,
                                  instrucoes_refinamento=None, versao_anterior=None):
    """Segunda etapa - recomendar arquitetura de canais com suporte a refinamento"""
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
Você é um Estrategista de Mídias Sênior. Abaixo está uma versão anterior da arquitetura de canais.
O usuário pediu ajustes específicos. MANTENHA a estrutura geral do documento, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR DA ARQUITETURA:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO DO USUÁRIO:**
{instrucoes_refinamento}

**CONTEXTO (para referência):**
- Objetivos: {objetivos}
- Orçamento: R$ {orcamento:,.2f}

Retorne a versão COMPLETA da arquitetura, aplicando apenas os refinamentos solicitados.
"""
        response = modelo.generate_content(prompt)
        return response.text
    
    # Caso contrário, usar prompt normal (igual ao anterior)
    # ... (código existente)

def definir_estrutura_narrativa(arquitetura_canais, objetivos, cliente, orcamento,
                                instrucoes_refinamento=None, versao_anterior=None):
    """Terceira etapa - estrutura narrativa com refinamento"""
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
Você é um Estrategista de Mídias Sênior. Abaixo está uma versão anterior da estrutura narrativa.
O usuário pediu ajustes específicos. MANTENHA a estrutura geral do documento, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR DA ESTRUTURA:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO DO USUÁRIO:**
{instrucoes_refinamento}

**CONTEXTO:**
- Cliente: {cliente}
- Objetivos: {objetivos}
- Orçamento: R$ {orcamento:,.2f}

Retorne a versão COMPLETA da estrutura, aplicando apenas os refinamentos solicitados.
"""
        response = modelo.generate_content(prompt)
        return response.text
    
    # Caso contrário, prompt normal
    # ... (código existente)

def detalhar_fases(estrutura_escolhida, arquitetura_canais, orcamento, cliente, objetivos,
                   metas_okr=None, instrucoes_refinamento=None, versao_anterior=None):
    """Quarta etapa - detalhamento de fases com OKRs customizáveis"""
    
    # Construir seção de metas de OKR se fornecidas
    metas_texto = ""
    if metas_okr:
        metas_texto = "\n**METAS DE OKR DEFINIDAS PELO USUÁRIO (devem ser incorporadas):**\n"
        for fase, metas in metas_okr.items():
            metas_texto += f"\nFase {fase}:\n"
            for meta in metas:
                metas_texto += f"- {meta}\n"
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
Você é um Estrategista de Mídias Sênior. Abaixo está uma versão anterior do detalhamento das fases.
O usuário pediu ajustes específicos. MANTENHA a estrutura geral do documento, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR DO DETALHAMENTO:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO DO USUÁRIO:**
{instrucoes_refinamento}

{metas_texto}

**CONTEXTO:**
- Cliente: {cliente}
- Objetivos: {objetivos}
- Orçamento: R$ {orcamento:,.2f}

Retorne a versão COMPLETA do detalhamento, aplicando apenas os refinamentos solicitados e incorporando as metas de OKR onde especificado.
"""
        response = modelo.generate_content(prompt)
        return response.text
    
    # Caso contrário, prompt normal com inclusão de metas
    prompt_base = f"""
Com a estrutura narrativa escolhida, agora você precisa DETALHAR CADA FASE da campanha com profundidade estratégica.

**Estrutura Escolhida:**
{estrutura_escolhida}

**Arquitetura de Canais e Alocação:**
{arquitetura_canais}

**Cliente:** {cliente}
**Objetivos:** {objetivos}
**Orçamento Total:** R$ {orcamento:,.2f}

{metas_texto}

**DIRETRIZES PARA DETALHAMENTO:**

Para CADA FASE identificada na estrutura, forneça um detalhamento completo seguindo este template. 
USE O CONHECIMENTO DE FUNIL PARA CADA ETAPA PREDOMINANTE NA FASE.

---
**FASE [NOME DA FASE]**

**📖 NARRATIVA DA FASE:**

**🎯 ETAPAS DO FUNIL PREDOMINANTES:**

**📊 OKRs E MÉTRICAS DA FASE:**

**Métricas Primárias (devem ser monitoradas como sucesso):**
- [Métrica 1] - Meta: [valor definido pelo usuário ou sugestão da IA] - Justificativa
- [Métrica 2] - Meta: [valor] - Justificativa

**Métricas Secundárias (para diagnóstico):**
- [Métrica 3]
- [Métrica 4]

**⚠️ O QUE NÃO MEDIR NESTA FASE:**

**💰 ALOCAÇÃO DE BUDGET:**
R$ [valor] ([percentual]% do total)

**🎨 ESTRATÉGIA CRIATIVA E CONTEÚDO:**

**Conceito/Temática da fase:**

**Princípios Psicológicos Aplicados:**
- [Princípio 1]
- [Princípio 2]

**Tipos de conteúdo recomendados:**
- [Tipo 1]
- [Tipo 2]

**📱 ATUAÇÃO POR PLATAFORMA:**

**[Plataforma 1]:**
- Tipo de campanha:
- Formato:
- Objetivo específico:
- Benchmark esperado:

**🎯 SEGMENTAÇÃO ESTRATÉGICA:**

**Público-alvo desta fase:**

**Critérios de segmentação:**

**🤝 AÇÕES DE CRM/RELACIONAMENTO:**

**⏱️ TIMING E DURAÇÃO:**

**Duração sugerida:**

**Marcos importantes:**

**🔄 SINERGIA COM OUTRAS FASES:**

---
"""
    response = modelo.generate_content(prompt_base)
    return response.text

def criar_cronograma_narrativo(fases_detalhadas, cliente, orcamento,
                              instrucoes_refinamento=None, versao_anterior=None):
    """Quinta etapa - cronograma com refinamento"""
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
Você é um Estrategista de Mídias Sênior. Abaixo está uma versão anterior do cronograma narrativo.
O usuário pediu ajustes específicos. MANTENHA a estrutura geral do documento, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR DO CRONOGRAMA:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO DO USUÁRIO:**
{instrucoes_refinamento}

**CONTEXTO:**
- Cliente: {cliente}
- Orçamento: R$ {orcamento:,.2f}

Retorne a versão COMPLETA do cronograma, aplicando apenas os refinamentos solicitados.
"""
        response = modelo.generate_content(prompt)
        return response.text
    
    # Caso contrário, prompt normal
    # ... (código existente)

def gerar_recomendacoes_finais(plano_completo, cliente, objetivos,
                              instrucoes_refinamento=None, versao_anterior=None):
    """Sexta etapa - recomendações finais com refinamento"""
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
Você é um Estrategista de Mídias Sênior. Abaixo está uma versão anterior das recomendações finais.
O usuário pediu ajustes específicos. MANTENHA a estrutura geral do documento, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR DAS RECOMENDAÇÕES:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO DO USUÁRIO:**
{instrucoes_refinamento}

**CONTEXTO:**
- Cliente: {cliente}
- Objetivos: {objetivos}

Retorne a versão COMPLETA das recomendações, aplicando apenas os refinamentos solicitados.
"""
        response = modelo.generate_content(prompt)
        return response.text
    
    # Caso contrário, prompt normal
    # ... (código existente)

# ============================================================================
# FUNÇÕES DE INTERFACE PARA REFINAMENTO
# ============================================================================

def render_refinamento_box(etapa_nome, etapa_chave, funcao_gerar, **kwargs):
    """Renderiza caixa de refinamento para qualquer etapa"""
    
    st.markdown("---")
    st.subheader("🔧 Refinar esta etapa")
    
    with st.expander("Clique aqui para fazer ajustes específicos", expanded=False):
        st.markdown(f"**O que você gostaria de ajustar na {etapa_nome}?**")
        st.markdown("Seja específico sobre o que manter e o que mudar. Exemplos:")
        st.markdown("- 'Aumente o orçamento da Fase 2 para 40%'")
        st.markdown("- 'Adicione TikTok como canal na Fase 1'")
        st.markdown("- 'Mude a métrica primária de Alcance para Impressões'")
        st.markdown("- 'O tom está muito técnico, deixe mais executivo'")
        
        instrucao = st.text_area(
            "Instruções de refinamento:",
            key=f"refine_{etapa_chave}",
            height=100,
            placeholder="Descreva os ajustes que você quer..."
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔄 Aplicar Refinamentos", key=f"btn_refine_{etapa_chave}"):
                if instrucao:
                    with st.spinner("Aplicando refinamentos..."):
                        versao_anterior = st.session_state.narrativa_gerada[etapa_chave]
                        kwargs['instrucoes_refinamento'] = instrucao
                        kwargs['versao_anterior'] = versao_anterior
                        
                        nova_versao = funcao_gerar(**kwargs)
                        st.session_state.narrativa_gerada[etapa_chave] = nova_versao
                        st.rerun()
                else:
                    st.warning("Por favor, descreva os ajustes que deseja.")
        
        with col2:
            if st.button("↩️ Descartar", key=f"btn_discard_{etapa_chave}"):
                st.rerun()

def render_metas_okr_editor(fases_detalhadas):
    """Renderiza editor de metas OKR para cada fase"""
    
    st.markdown("---")
    st.subheader("🎯 Definir Metas de OKR")
    st.markdown("Para cada fase, defina as metas específicas que você quer alcançar:")
    
    metas_por_fase = {}
    
    # Parse simples para identificar fases (assumindo formato markdown com **FASE**)
    linhas = fases_detalhadas.split('\n')
    fase_atual = None
    fases_encontradas = []
    
    for linha in linhas:
        if '**FASE' in linha.upper() or 'FASE **' in linha:
            # Extrair nome da fase
            import re
            match = re.search(r'\*\*FASE[:\s]*(.*?)\*\*', linha, re.IGNORECASE)
            if match:
                fase_atual = match.group(1).strip()
                fases_encontradas.append(fase_atual)
    
    if not fases_encontradas:
        # Fallback: fases genéricas
        fases_encontradas = ["Fase 1", "Fase 2", "Fase 3"]
    
    for fase in fases_encontradas:
        with st.expander(f"📊 Metas para {fase}", expanded=True):
            st.markdown("**Defina até 3 OKRs para esta fase:**")
            
            metas_fase = []
            for i in range(3):
                col1, col2 = st.columns([3, 1])
                with col1:
                    descricao = st.text_input(
                        f"OKR {i+1}",
                        key=f"okr_desc_{fase}_{i}",
                        placeholder=f"Ex: Aumentar alcance em 20%"
                    )
                with col2:
                    valor = st.text_input(
                        "Meta",
                        key=f"okr_valor_{fase}_{i}",
                        placeholder="Ex: 1.5M"
                    )
                
                if descricao and valor:
                    metas_fase.append(f"{descricao}: {valor}")
            
            if metas_fase:
                metas_por_fase[fase] = metas_fase
    
    return metas_por_fase

# ============================================================================
# INTERFACE STREAMLIT
# ============================================================================

# Título
st.title("🎯 Planejador Estratégico de Mídias com IA")
st.markdown("---")

# Estado da sessão
if 'etapa_atual' not in st.session_state:
    st.session_state.etapa_atual = 1
if 'dados_coletados' not in st.session_state:
    st.session_state.dados_coletados = {}
if 'narrativa_gerada' not in st.session_state:
    st.session_state.narrativa_gerada = {}
if 'plano_final' not in st.session_state:
    st.session_state.plano_final = None
if 'metas_okr' not in st.session_state:
    st.session_state.metas_okr = {}

# Sidebar com progresso
with st.sidebar:
    st.header("📖 Progresso do Plano")
    
    etapas = {
        1: "🎯 Dados Iniciais",
        2: "🔍 Insights Estratégicos",
        3: "📱 Arquitetura de Canais",
        4: "🏗️ Estrutura Narrativa",
        5: "📅 Detalhamento das Fases",
        6: "⏱️ Cronograma",
        7: "✨ Recomendações Finais"
    }
    
    for num, desc in etapas.items():
        if num < st.session_state.etapa_atual:
            st.success(f"✓ {desc}")
        elif num == st.session_state.etapa_atual:
            st.info(f"▶ {desc}")
        else:
            st.write(f"○ {desc}")
    
    if st.session_state.etapa_atual == 5:
        st.markdown("---")
        st.info("💡 Dica: Use o editor de OKRs abaixo para definir metas específicas para cada fase.")

# ETAPA 1: Coleta de Dados
if st.session_state.etapa_atual == 1:
    st.header("Etapa 1: Dados do Cliente")
    
    with st.form("dados_cliente"):
        col1, col2 = st.columns(2)
        
        with col1:
            cliente = st.text_input("Nome do Cliente/Conta *")
            orcamento = st.number_input("Orçamento Total (R$) *", min_value=0.0, step=1000.0, format="%.2f")
            
        with col2:
            canais = st.multiselect(
                "Canais de Interesse (opcional)",
                list(PLATAFORMA_OBJETIVOS.keys())
            )
        
        objetivos = st.text_area("Objetivos Principais *", height=100,
                                placeholder="Ex: Aumentar vendas em 30%, lançar novo produto, fortalecer marca...")
        
        contexto = st.text_area("Contexto e Desafios *", height=150,
                               placeholder="Conte sobre o momento da marca, concorrência, público-alvo...")
        
        submitted = st.form_submit_button("🚀 Gerar Insights Iniciais")
        
        if submitted and cliente and orcamento and objetivos and contexto:
            with st.spinner("Gerando análise estratégica..."):
                st.session_state.dados_coletados = {
                    'cliente': cliente,
                    'orcamento': orcamento,
                    'objetivos': objetivos,
                    'contexto': contexto,
                    'canais_preferencia': canais
                }
                
                insights = gerar_insights_iniciais(
                    cliente, orcamento, objetivos, contexto,
                    ", ".join(canais) if canais else "A definir"
                )
                st.session_state.narrativa_gerada['insights_iniciais'] = insights
                st.session_state.etapa_atual = 2
                st.rerun()

# ETAPA 2: Insights Iniciais
elif st.session_state.etapa_atual == 2:
    st.header("🔍 Insights Estratégicos Iniciais")
    
    # Exibir conteúdo
    st.markdown(st.session_state.narrativa_gerada['insights_iniciais'])
    
    # Caixa de refinamento
    render_refinamento_box(
        "análise inicial",
        'insights_iniciais',
        gerar_insights_iniciais,
        cliente=st.session_state.dados_coletados['cliente'],
        orcamento=st.session_state.dados_coletados['orcamento'],
        objetivos=st.session_state.dados_coletados['objetivos'],
        contexto=st.session_state.dados_coletados['contexto'],
        canais_preferencia=", ".join(st.session_state.dados_coletados['canais_preferencia']) if st.session_state.dados_coletados['canais_preferencia'] else "A definir"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Avançar para Arquitetura de Canais"):
            with st.spinner("Gerando arquitetura de canais..."):
                arquitetura = recomendar_arquitetura_canais(
                    st.session_state.narrativa_gerada['insights_iniciais'],
                    st.session_state.dados_coletados['objetivos'],
                    st.session_state.dados_coletados['orcamento'],
                    ", ".join(st.session_state.dados_coletados['canais_preferencia']) if st.session_state.dados_coletados['canais_preferencia'] else "Definir"
                )
                st.session_state.narrativa_gerada['arquitetura_canais'] = arquitetura
                st.session_state.etapa_atual = 3
                st.rerun()
    
    with col2:
        if st.button("↩️ Voltar"):
            st.session_state.etapa_atual = 1
            st.rerun()

# ETAPA 3: Arquitetura de Canais
elif st.session_state.etapa_atual == 3:
    st.header("📱 Arquitetura de Canais")
    
    st.markdown(st.session_state.narrativa_gerada['arquitetura_canais'])
    
    render_refinamento_box(
        "arquitetura de canais",
        'arquitetura_canais',
        recomendar_arquitetura_canais,
        insights_iniciais=st.session_state.narrativa_gerada['insights_iniciais'],
        objetivos=st.session_state.dados_coletados['objetivos'],
        orcamento=st.session_state.dados_coletados['orcamento'],
        canais_preferencia=", ".join(st.session_state.dados_coletados['canais_preferencia']) if st.session_state.dados_coletados['canais_preferencia'] else "Definir"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏗️ Avançar para Estrutura Narrativa"):
            with st.spinner("Gerando estrutura narrativa..."):
                estrutura = definir_estrutura_narrativa(
                    st.session_state.narrativa_gerada['arquitetura_canais'],
                    st.session_state.dados_coletados['objetivos'],
                    st.session_state.dados_coletados['cliente'],
                    st.session_state.dados_coletados['orcamento']
                )
                st.session_state.narrativa_gerada['estrutura_plano'] = estrutura
                st.session_state.etapa_atual = 4
                st.rerun()
    
    with col2:
        if st.button("↩️ Voltar"):
            st.session_state.etapa_atual = 2
            st.rerun()

# ETAPA 4: Estrutura Narrativa
elif st.session_state.etapa_atual == 4:
    st.header("🏗️ Estrutura Narrativa do Plano")
    
    st.markdown(st.session_state.narrativa_gerada['estrutura_plano'])
    
    st.markdown("---")
    st.markdown("**Confirme a estrutura escolhida:**")
    
    estrutura_confirmada = st.text_area(
        "Estrutura selecionada (edite se necessário):",
        value=st.session_state.narrativa_gerada['estrutura_plano'],
        height=200
    )
    
    render_refinamento_box(
        "estrutura narrativa",
        'estrutura_plano',
        definir_estrutura_narrativa,
        arquitetura_canais=st.session_state.narrativa_gerada['arquitetura_canais'],
        objetivos=st.session_state.dados_coletados['objetivos'],
        cliente=st.session_state.dados_coletados['cliente'],
        orcamento=st.session_state.dados_coletados['orcamento']
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📅 Avançar para Detalhamento"):
            # Salvar estrutura editada se diferente
            if estrutura_confirmada != st.session_state.narrativa_gerada['estrutura_plano']:
                st.session_state.narrativa_gerada['estrutura_plano'] = estrutura_confirmada
            
            st.session_state.etapa_atual = 5
            st.rerun()
    
    with col2:
        if st.button("↩️ Voltar"):
            st.session_state.etapa_atual = 3
            st.rerun()

# ETAPA 5: Detalhamento das Fases (com editor de OKRs)
elif st.session_state.etapa_atual == 5:
    st.header("📅 Detalhamento das Fases")
    
    # Se não tem fases geradas ainda, gerar
    if 'fases_detalhadas' not in st.session_state.narrativa_gerada:
        with st.spinner("Gerando detalhamento das fases..."):
            # Primeiro, verificar se há metas de OKR definidas
            metas_okr = st.session_state.metas_okr if st.session_state.metas_okr else None
            
            fases = detalhar_fases(
                st.session_state.narrativa_gerada['estrutura_plano'],
                st.session_state.narrativa_gerada['arquitetura_canais'],
                st.session_state.dados_coletados['orcamento'],
                st.session_state.dados_coletados['cliente'],
                st.session_state.dados_coletados['objetivos'],
                metas_okr=metas_okr
            )
            st.session_state.narrativa_gerada['fases_detalhadas'] = fases
    
    # Editor de OKRs (aparece antes do conteúdo para permitir definição)
    with st.expander("🎯 Editor de OKRs - Defina suas metas", expanded=not st.session_state.metas_okr):
        st.markdown("""
        **Defina metas específicas para cada fase.** 
        Estas metas serão incorporadas ao detalhamento das fases.
        """)
        
        metas_okr = render_metas_okr_editor(st.session_state.narrativa_gerada['fases_detalhadas'])
        
        if metas_okr:
            if st.button("💾 Salvar Metas e Regenerar Fases"):
                st.session_state.metas_okr = metas_okr
                with st.spinner("Regenerando fases com suas metas..."):
                    fases = detalhar_fases(
                        st.session_state.narrativa_gerada['estrutura_plano'],
                        st.session_state.narrativa_gerada['arquitetura_canais'],
                        st.session_state.dados_coletados['orcamento'],
                        st.session_state.dados_coletados['cliente'],
                        st.session_state.dados_coletados['objetivos'],
                        metas_okr=metas_okr
                    )
                    st.session_state.narrativa_gerada['fases_detalhadas'] = fases
                    st.rerun()
    
    # Exibir conteúdo
    st.markdown(st.session_state.narrativa_gerada['fases_detalhadas'])
    
    # Caixa de refinamento específica para fases
    render_refinamento_box(
        "detalhamento das fases",
        'fases_detalhadas',
        detalhar_fases,
        estrutura_escolhida=st.session_state.narrativa_gerada['estrutura_plano'],
        arquitetura_canais=st.session_state.narrativa_gerada['arquitetura_canais'],
        orcamento=st.session_state.dados_coletados['orcamento'],
        cliente=st.session_state.dados_coletados['cliente'],
        objetivos=st.session_state.dados_coletados['objetivos'],
        metas_okr=st.session_state.metas_okr
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏱️ Avançar para Cronograma"):
            with st.spinner("Gerando cronograma narrativo..."):
                cronograma = criar_cronograma_narrativo(
                    st.session_state.narrativa_gerada['fases_detalhadas'],
                    st.session_state.dados_coletados['cliente'],
                    st.session_state.dados_coletados['orcamento']
                )
                st.session_state.narrativa_gerada['cronograma'] = cronograma
                st.session_state.etapa_atual = 6
                st.rerun()
    
    with col2:
        if st.button("↩️ Voltar"):
            st.session_state.etapa_atual = 4
            st.rerun()

# ETAPA 6: Cronograma Narrativo
elif st.session_state.etapa_atual == 6:
    st.header("⏱️ Cronograma Narrativo")
    
    st.markdown(st.session_state.narrativa_gerada['cronograma'])
    
    render_refinamento_box(
        "cronograma",
        'cronograma',
        criar_cronograma_narrativo,
        fases_detalhadas=st.session_state.narrativa_gerada['fases_detalhadas'],
        cliente=st.session_state.dados_coletados['cliente'],
        orcamento=st.session_state.dados_coletados['orcamento']
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✨ Avançar para Recomendações Finais"):
            # Compilar plano completo
            plano_completo = f"""
# PLANO ESTRATÉGICO - {st.session_state.dados_coletados['cliente']}

## INSIGHTS INICIAIS
{st.session_state.narrativa_gerada['insights_iniciais']}

## ARQUITETURA DE CANAIS
{st.session_state.narrativa_gerada['arquitetura_canais']}

## ESTRUTURA NARRATIVA
{st.session_state.narrativa_gerada['estrutura_plano']}

## FASES DETALHADAS
{st.session_state.narrativa_gerada['fases_detalhadas']}

## CRONOGRAMA
{st.session_state.narrativa_gerada['cronograma']}
"""
            
            with st.spinner("Gerando recomendações finais..."):
                recomendacoes = gerar_recomendacoes_finais(
                    plano_completo,
                    st.session_state.dados_coletados['cliente'],
                    st.session_state.dados_coletados['objetivos']
                )
                st.session_state.narrativa_gerada['recomendacoes'] = recomendacoes
                st.session_state.plano_final = plano_completo + "\n\n" + recomendacoes
                st.session_state.etapa_atual = 7
                st.rerun()
    
    with col2:
        if st.button("↩️ Voltar"):
            st.session_state.etapa_atual = 5
            st.rerun()

# ETAPA 7: Plano Final
elif st.session_state.etapa_atual == 7:
    st.header("✨ Plano Estratégico Completo")
    
    with st.expander("📋 Ver Plano Completo", expanded=True):
        st.markdown(st.session_state.plano_final)
    
    # Download
    st.download_button(
        label="📥 Baixar Plano (Markdown)",
        data=st.session_state.plano_final,
        file_name=f"plano_{st.session_state.dados_coletados['cliente'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )
    
    st.markdown("---")
    
    # Opção de refinamento final
    with st.expander("🔧 Refinar Plano Completo"):
        st.markdown("""
        **Deseja fazer ajustes finais no plano completo?**
        Descreva os refinamentos e eles serão aplicados a todas as seções relevantes.
        """)
        
        refinamento_final = st.text_area("Instruções de refinamento:", height=100)
        
        if st.button("🔄 Aplicar Refinamentos Finais"):
            if refinamento_final:
                with st.spinner("Aplicando refinamentos finais..."):
                    # Regenerar cada seção com as instruções
                    
                    # Insights
                    insights = gerar_insights_iniciais(
                        st.session_state.dados_coletados['cliente'],
                        st.session_state.dados_coletados['orcamento'],
                        st.session_state.dados_coletados['objetivos'],
                        st.session_state.dados_coletados['contexto'],
                        ", ".join(st.session_state.dados_coletados['canais_preferencia']) if st.session_state.dados_coletados['canais_preferencia'] else "A definir",
                        instrucoes_refinamento=refinamento_final,
                        versao_anterior=st.session_state.narrativa_gerada['insights_iniciais']
                    )
                    st.session_state.narrativa_gerada['insights_iniciais'] = insights
                    
                    # Arquitetura
                    arquitetura = recomendar_arquitetura_canais(
                        insights,
                        st.session_state.dados_coletados['objetivos'],
                        st.session_state.dados_coletados['orcamento'],
                        ", ".join(st.session_state.dados_coletados['canais_preferencia']) if st.session_state.dados_coletados['canais_preferencia'] else "Definir",
                        instrucoes_refinamento=refinamento_final,
                        versao_anterior=st.session_state.narrativa_gerada['arquitetura_canais']
                    )
                    st.session_state.narrativa_gerada['arquitetura_canais'] = arquitetura
                    
                    # Estrutura
                    estrutura = definir_estrutura_narrativa(
                        arquitetura,
                        st.session_state.dados_coletados['objetivos'],
                        st.session_state.dados_coletados['cliente'],
                        st.session_state.dados_coletados['orcamento'],
                        instrucoes_refinamento=refinamento_final,
                        versao_anterior=st.session_state.narrativa_gerada['estrutura_plano']
                    )
                    st.session_state.narrativa_gerada['estrutura_plano'] = estrutura
                    
                    # Fases
                    fases = detalhar_fases(
                        estrutura,
                        arquitetura,
                        st.session_state.dados_coletados['orcamento'],
                        st.session_state.dados_coletados['cliente'],
                        st.session_state.dados_coletados['objetivos'],
                        metas_okr=st.session_state.metas_okr,
                        instrucoes_refinamento=refinamento_final,
                        versao_anterior=st.session_state.narrativa_gerada['fases_detalhadas']
                    )
                    st.session_state.narrativa_gerada['fases_detalhadas'] = fases
                    
                    # Cronograma
                    cronograma = criar_cronograma_narrativo(
                        fases,
                        st.session_state.dados_coletados['cliente'],
                        st.session_state.dados_coletados['orcamento'],
                        instrucoes_refinamento=refinamento_final,
                        versao_anterior=st.session_state.narrativa_gerada['cronograma']
                    )
                    st.session_state.narrativa_gerada['cronograma'] = cronograma
                    
                    # Recompilar plano final
                    plano_completo = f"""
# PLANO ESTRATÉGICO - {st.session_state.dados_coletados['cliente']}

## INSIGHTS INICIAIS
{insights}

## ARQUITETURA DE CANAIS
{arquitetura}

## ESTRUTURA NARRATIVA
{estrutura}

## FASES DETALHADAS
{fases}

## CRONOGRAMA
{cronograma}
"""
                    
                    recomendacoes = gerar_recomendacoes_finais(
                        plano_completo,
                        st.session_state.dados_coletados['cliente'],
                        st.session_state.dados_coletados['objetivos'],
                        instrucoes_refinamento=refinamento_final,
                        versao_anterior=st.session_state.narrativa_gerada['recomendacoes']
                    )
                    st.session_state.narrativa_gerada['recomendacoes'] = recomendacoes
                    st.session_state.plano_final = plano_completo + "\n\n" + recomendacoes
                    
                    st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Começar Novo Planejamento"):
            for key in ['etapa_atual', 'dados_coletados', 'narrativa_gerada', 'plano_final', 'metas_okr']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        if st.button("↩️ Voltar para Cronograma"):
            st.session_state.etapa_atual = 6
            st.rerun()

# Rodapé
st.markdown("---")
st.markdown("*Planejador Estratégico de Mídias com IA - Baseado em frameworks acadêmicos e dados do mercado brasileiro*")
