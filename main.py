import streamlit as st
import google.generativeai as genai
import os
from datetime import datetime
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

# Título e introdução narrativa
st.title("🎯 Planejador Estratégico de Mídias")
st.markdown("""
Bem-vindo ao **Planejador Estratégico de Mídias com IA**. 

Este não é apenas um gerador de planos - é um **consultor estratégico** que vai te guiar através de uma jornada de construção de um plano de mídia completo, onde cada decisão alimenta a próxima, criando uma narrativa coesa e estratégica.

Vamos começar entendendo seu negócio, seus objetivos e seu orçamento. A partir daí, construiremos juntos um plano que conta uma história - a história do seu sucesso.
""")
st.markdown("---")

# Estado da sessão para o storytelling
if 'etapa_atual' not in st.session_state:
    st.session_state.etapa_atual = 1
if 'dados_coletados' not in st.session_state:
    st.session_state.dados_coletados = {}
if 'narrativa_gerada' not in st.session_state:
    st.session_state.narrativa_gerada = {}
if 'plano_final' not in st.session_state:
    st.session_state.plano_final = None

# Funções de geração com narrativa
def gerar_insights_iniciais(cliente, orcamento, objetivos, contexto, canais_preferencia):
    prompt = f"""
    Você é um Estrategista de Mídias Sênior. Com base nas primeiras informações do cliente, faça uma ANÁLISE INICIAL ESTRATÉGICA que será a base de todo o planejamento.
    
    **Informações do Cliente:**
    - Cliente: {cliente}
    - Orçamento Total: R$ {orcamento:,.2f}
    - Objetivos Principais: {objetivos}
    - Contexto/Desafios: {contexto}
    - Canais de Interesse: {canais_preferencia if canais_preferencia else "A IA deve definir os melhores canais"}
    
    Forneça uma análise em formato narrativo com:
    
    1. **ENTENDIMENTO DO NEGÓCIO**: O que você compreende sobre o cliente e seus desafios
    2. **POTENCIAL DO ORÇAMENTO**: Análise realista do que pode ser alcançado com R$ {orcamento:,.2f}
    3. **PRIMEIRAS IMPRESSÕES ESTRATÉGICAS**: Direcionamentos iniciais baseados nos objetivos
    4. **PERGUNTAS ESTRATÉGICAS**: O que mais precisamos considerar?
    
    Seja acolhedor mas estratégico. Use tom consultivo.
    """
    response = modelo.generate_content(prompt)
    return response.text

def recomendar_arquitetura_canais(insights_iniciais, objetivos, orcamento, canais_preferencia):
    prompt = f"""
    Com base na análise inicial abaixo, você agora precisa RECOMENDAR A ARQUITETURA DE CANAIS.
    
    **Análise Inicial do Cliente:**
    {insights_iniciais}
    
    **Objetivos:**
    {objetivos}
    
    **Orçamento:** R$ {orcamento:,.2f}
    
    **Canais Considerados:** {canais_preferencia if canais_preferencia else "Definir baseado na estratégia"}
    
    Forneça uma recomendação estratégica com:
    
    1. **ARQUITETURA DE CANAIS**: Quais canais usar e porquê (considere: Facebook, Instagram, Google Ads, TikTok, LinkedIn, YouTube)
    2. **FUNÇÃO DE CADA CANAL**: O papel de cada um na jornada do consumidor (Awareness, Consideração, Conversão)
    3. **ALOCAÇÃO ESTRATÉGICA**: Percentual do budget por canal COM JUSTIFICATIVA
    4. **SINERGIA ENTRE CANAIS**: Como eles trabalham juntos
    5. **POR QUE ESTA ARQUITETURA**: A lógica estratégica por trás da escolha
    
    Use storytelling para explicar como esses canais vão contar a história da marca.
    """
    response = modelo.generate_content(prompt)
    return response.text

def definir_estrutura_narrativa(arquitetura_canais, objetivos, cliente):
    prompt = f"""
    Agora, com a arquitetura de canais definida, você precisa CRIAR A ESTRUTURA NARRATIVA DO PLANO.
    Esta estrutura será a "espinha dorsal" de todo o planejamento.
    
    **Arquitetura de Canais:**
    {arquitetura_canais}
    
    **Objetivos:**
    {objetivos}
    
    **Cliente:** {cliente}
    
    Crie 3 possíveis ESTRUTURAS DE PLANO (arquétipos de jornada) e recomende a melhor:
    
    **Opção 1 - JORNADA HERÓICA (Lançamento → Construção → Consolidação)**
    - Fase 1: Aquecimento e Construção de Expectativa
    - Fase 2: Lançamento e Impacto
    - Fase 3: Sustentação e Nutrição
    
    **Opção 2 - JORNADA DE RELACIONAMENTO (Atração → Conversão → Fidelização)**
    - Fase 1: Atração e Topo de Funil
    - Fase 2: Conversão e Meio de Funil
    - Fase 3: Fidelização e Advocacy
    
    **Opção 3 - JORNADA SAZONAL (Pré → Durante → Pós)**
    - Fase 1: Construção de Awareness Pré-Sazonalidade
    - Fase 2: Ativação Durante o Período Chave
    - Fase 3: Pós e Retenção
    
    **Opção 4 - Crie uma estrutura personalizada baseada no contexto do cliente**
    
    Para cada opção, explique:
    - A metáfora/narrativa por trás
    - Objetivo de cada fase
    - Duração sugerida
    - Qual OKR principal em cada fase
    
    Por fim, RECOMENDE a melhor estrutura com justificativa estratégica.
    """
    response = modelo.generate_content(prompt)
    return response.text

def detalhar_fases(estrutura_escolhida, arquitetura_canais, orcamento):
    prompt = f"""
    Com a estrutura narrativa escolhida, agora você precisa DETALHAR CADA FASE da campanha.
    
    **Estrutura Escolhida:**
    {estrutura_escolhida}
    
    **Arquitetura de Canais e Alocação:**
    {arquitetura_canais}
    
    **Orçamento Total:** R$ {orcamento:,.2f}
    
    Para CADA FASE da estrutura escolhida, forneça um detalhamento completo:
    
    ---
    **FASE [NOME DA FASE]**
    
    🎯 **Objetivo da Fase:**
    [Objetivo claro e mensurável]
    
    📊 **OKRs da Fase:**
    - Objective 1: [KR1, KR2, KR3]
    - Objective 2: [KR1, KR2, KR3]
    
    💰 **Alocação de Budget:** R$ [valor] ([percentual]% do total)
    
    🎨 **Estratégia Criativa:**
    - Conceito/Temática da fase
    - Tipos de conteúdo recomendados
    - Exemplos de abordagens criativas
    
    📱 **Atuação por Plataforma:**
    - [Plataforma 1]: Tipo de campanha, formato, objetivo específico
    - [Plataforma 2]: Tipo de campanha, formato, objetivo específico
    - [Plataforma 3]: Tipo de campanha, formato, objetivo específico
    
    🎯 **Segmentação Estratégica:**
    - Público-alvo específico desta fase
    - Critérios de segmentação (demográfico, comportamental, interesses)
    - Justificativa da escolha
    
    🤝 **Ações de CRM/Relacionamento:**
    - Como engajar e nutrir a base
    - Trigger points para comunicação
    - Estratégias de introdução de clientes na campanha
    
    ⏱️ **Timing e Duração:**
    - Duração sugerida
    - Marcos importantes dentro da fase
    - Frequência recomendada
    
    🔄 **Sinergia com outras fases:**
    - Como esta fase prepara para a próxima
    - O que será construído para sustentar
    
    ---
    """
    response = modelo.generate_content(prompt)
    return response.text

def criar_cronograma_narrativo(fases_detalhadas, cliente):
    prompt = f"""
    Agora, com todas as fases detalhadas, crie uma RÉGUA CRONOLÓGICA que conte a história da campanha ao longo do tempo.
    
    **Fases Detalhadas:**
    {fases_detalhadas}
    
    **Cliente:** {cliente}
    
    Crie um cronograma narrativo em formato de linha do tempo que inclua:
    
    1. **VISÃO GERAL DA JORNADA**: Um parágrafo que conte a história completa da campanha
    
    2. **LINHA DO TEMPO DETALHADA** (mês a mês ou semana a semana):
       - Mês/Semana 1: [O que acontece + porquê]
       - Mês/Semana 2: [O que acontece + porquê]
       - (continue para todo o período)
    
    3. **MARCOS IMPORTANTES**:
       - Datas-chave de lançamentos
       - Momentos de avaliação/otimização
       - Pontos de virada na narrativa
    
    4. **CALENDÁRIO DE CONTEÚDO ESTRATÉGICO**:
       - Que tipo de conteúdo em cada momento
       - Por que esse conteúdo faz sentido no storytelling
    
    5. **TRIGGERS DE ATIVAÇÃO**:
       - Quando e como acionar diferentes públicos
       - Gatilhos para campanhas específicas
    
    O cronograma deve ser visualmente descritivo e contar uma história com começo, meio e fim.
    """
    response = modelo.generate_content(prompt)
    return response.text

def gerar_recomendacoes_finais(plano_completo, cliente):
    prompt = f"""
    Como toque final, você precisa gerar RECOMENDAÇÕES EXECUTIVAS e APRENDIZADOS ESPERADOS.
    
    **Plano Completo:**
    {plano_completo}
    
    **Cliente:** {cliente}
    
    Forneça:
    
    1. **RESUMO EXECUTIVO DA ESTRATÉGIA**: Um parágrafo poderoso que resume todo o plano
    
    2. **3 APRENDIZADOS QUE ESPERAMOS OBTER**: O que vamos descobrir com esta campanha
    
    3. **RECOMENDAÇÕES DE OTIMIZAÇÃO CONTÍNUA**: Como evoluir o plano durante a execução
    
    4. **PRÓXIMOS PASSOS IMEDIATOS**: O que fazer agora para começar
    
    5. **PERGUNTAS ESTRATÉGICAS PARA O CLIENTE**: O que ainda precisa ser definido/alinhado
    
    Finalize com uma mensagem inspiradora sobre o potencial da campanha.
    """
    response = modelo.generate_content(prompt)
    return response.text

# Sidebar com progresso narrativo
with st.sidebar:
    st.header("📖 Jornada do Planejamento")
    
    etapas = {
        1: "🎯 Entendendo seu Negócio",
        2: "🔍 Insights Estratégicos",
        3: "📱 Arquitetura de Canais",
        4: "🏗️ Estrutura Narrativa",
        5: "📅 Detalhamento das Fases",
        6: "⏱️ Cronograma da Jornada",
        7: "✨ Recomendações Finais"
    }
    
    for num, desc in etapas.items():
        if num < st.session_state.etapa_atual:
            st.success(f"✓ {desc}")
        elif num == st.session_state.etapa_atual:
            st.info(f"▶ {desc}")
        else:
            st.write(f"○ {desc}")
    
    st.markdown("---")
    if st.session_state.plano_final:
        st.balloons()
        st.success("✅ Plano completo gerado!")

# Formulário principal - Etapa 1: Coleta de Dados
if st.session_state.etapa_atual == 1:
    st.header("🎯 Etapa 1: Conte-me sobre seu negócio")
    st.markdown(""nossa jornada começa aqui. Quanto mais eu souber sobre sua marca, mais estratégico será o plano.")
    
    with st.form("dados_iniciais"):
        col1, col2 = st.columns(2)
        
        with col1:
            cliente = st.text_input("Nome da Conta/Cliente *", placeholder="Ex: Loja de Roupas Sustentável")
            orcamento = st.number_input("Orçamento Total (R$) *", min_value=1000.0, step=1000.0, format="%.2f")
            
            objetivos = st.text_area(
                "Objetivos Principais do Plano *",
                placeholder="Ex: Aumentar vendas em 30%, lançar novo produto, fortalecer marca...",
                height=100
            )
        
        with col2:
            canais_preferencia = st.multiselect(
                "Canais de Interesse (opcional - posso recomendar os melhores)",
                ["Facebook", "Instagram", "Google Ads", "TikTok", "LinkedIn Ads", "YouTube", "Display", "Programática"]
            )
            
            contexto = st.text_area(
                "Contexto, Desafios e Oportunidades *",
                placeholder="Conte sobre o momento da marca, concorrência, diferenciais, público-alvo...",
                height=150
            )
        
        st.markdown("---")
        submitted = st.form_submit_button("🚀 Iniciar Jornada Estratégica")
        
        if submitted and cliente and orcamento and objetivos and contexto:
            with st.spinner("Analisando suas informações e gerando primeiros insights..."):
                st.session_state.dados_coletados = {
                    'cliente': cliente,
                    'orcamento': orcamento,
                    'objetivos': objetivos,
                    'contexto': contexto,
                    'canais_preferencia': canais_preferencia
                }
                
                # Gerar primeira análise
                insights = gerar_insights_iniciais(
                    cliente, orcamento, objetivos, contexto, 
                    ", ".join(canais_preferencia) if canais_preferencia else "A definir"
                )
                st.session_state.narrativa_gerada['insights_iniciais'] = insights
                st.session_state.etapa_atual = 2
                st.rerun()

# Etapa 2: Insights Iniciais
elif st.session_state.etapa_atual == 2:
    st.header("🔍 Etapa 2: Meus Primeiros Insights")
    st.markdown("Com base no que você me contou, aqui está minha análise inicial:")
    
    st.info(st.session_state.narrativa_gerada['insights_iniciais'])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Entendi, vamos para a arquitetura de canais"):
            with st.spinner("Analisando a melhor combinação de canais para sua estratégia..."):
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
        if st.button("🔄 Voltar e ajustar informações"):
            st.session_state.etapa_atual = 1
            st.rerun()

# Etapa 3: Arquitetura de Canais
elif st.session_state.etapa_atual == 3:
    st.header("📱 Etapa 3: Arquitetura Estratégica de Canais")
    st.markdown("Agora, vamos definir como seus canais vão trabalhar juntos para contar sua história:")
    
    st.markdown(st.session_state.narrativa_gerada['arquitetura_canais'])
    
    if st.button("🏗️ Definir Estrutura Narrativa do Plano"):
        with st.spinner("Criando a espinha dorsal da sua estratégia..."):
            estrutura = definir_estrutura_narrativa(
                st.session_state.narrativa_gerada['arquitetura_canais'],
                st.session_state.dados_coletados['objetivos'],
                st.session_state.dados_coletados['cliente']
            )
            st.session_state.narrativa_gerada['estrutura_plano'] = estrutura
            st.session_state.etapa_atual = 4
            st.rerun()

# Etapa 4: Estrutura Narrativa
elif st.session_state.etapa_atual == 4:
    st.header("🏗️ Etapa 4: A Estrutura da Sua Jornada")
    st.markdown("Aqui estão as possíveis estruturas para contar a história da sua campanha:")
    
    st.markdown(st.session_state.narrativa_gerada['estrutura_plano'])
    
    st.markdown("---")
    st.markdown("**Qual estrutura faz mais sentido para você?**")
    
    estrutura_escolhida = st.text_area(
        "Cole ou resuma a estrutura recomendada (ou crie sua própria):",
        height=150,
        value="Seguir a recomendação da IA"
    )
    
    if st.button("📅 Avançar para Detalhamento das Fases"):
        with st.spinner("Detalhando cada fase da sua jornada..."):
            fases = detalhar_fases(
                estrutura_escolhida,
                st.session_state.narrativa_gerada['arquitetura_canais'],
                st.session_state.dados_coletados['orcamento']
            )
            st.session_state.narrativa_gerada['fases_detalhadas'] = fases
            st.session_state.etapa_atual = 5
            st.rerun()

# Etapa 5: Detalhamento das Fases
elif st.session_state.etapa_atual == 5:
    st.header("📅 Etapa 5: Suas Fases em Detalhe")
    st.markdown("Cada fase da sua campanha, estrategicamente detalhada:")
    
    st.markdown(st.session_state.narrativa_gerada['fases_detalhadas'])
    
    if st.button("⏱️ Criar Cronograma Narrativo"):
        with st.spinner("Construindo a linha do tempo da sua história..."):
            cronograma = criar_cronograma_narrativo(
                st.session_state.narrativa_gerada['fases_detalhadas'],
                st.session_state.dados_coletados['cliente']
            )
            st.session_state.narrativa_gerada['cronograma'] = cronograma
            st.session_state.etapa_atual = 6
            st.rerun()

# Etapa 6: Cronograma Narrativo
elif st.session_state.etapa_atual == 6:
    st.header("⏱️ Etapa 6: A Linha do Tempo da Sua Jornada")
    st.markdown("Como sua história vai se desenrolar no tempo:")
    
    st.markdown(st.session_state.narrativa_gerada['cronograma'])
    
    if st.button("✨ Gerar Recomendações Finais"):
        with st.spinner("Finalizando seu plano estratégico..."):
            # Compilar plano completo
            plano_completo = f"""
            # PLANO ESTRATÉGICO DE MÍDIAS - {st.session_state.dados_coletados['cliente']}
            
            ## INSIGHTS INICIAIS
            {st.session_state.narrativa_gerada['insights_iniciais']}
            
            ## ARQUITETURA DE CANAIS
            {st.session_state.narrativa_gerada['arquitetura_canais']}
            
            ## ESTRUTURA DO PLANO
            {st.session_state.narrativa_gerada['estrutura_plano']}
            
            ## FASES DETALHADAS
            {st.session_state.narrativa_gerada['fases_detalhadas']}
            
            ## CRONOGRAMA
            {st.session_state.narrativa_gerada['cronograma']}
            """
            
            recomendacoes = gerar_recomendacoes_finais(
                plano_completo,
                st.session_state.dados_coletados['cliente']
            )
            st.session_state.narrativa_gerada['recomendacoes'] = recomendacoes
            st.session_state.plano_final = plano_completo + "\n\n" + recomendacoes
            st.session_state.etapa_atual = 7
            st.rerun()

# Etapa 7: Plano Final
elif st.session_state.etapa_atual == 7:
    st.header("✨ Seu Plano Estratégico Está Pronto!")
    st.markdown("A jornada foi concluída. Aqui está seu plano completo:")
    
    with st.expander("📋 Ver Plano Completo", expanded=True):
        st.markdown(st.session_state.plano_final)
    
    st.markdown("---")
    
    # Download do plano
    st.download_button(
        label="📥 Baixar Plano Estratégico (Markdown)",
        data=st.session_state.plano_final,
        file_name=f"plano_midias_{st.session_state.dados_coletados['cliente'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )
    
    st.markdown("---")
    st.markdown("""
    ### 🌟 Próximos Passos
    
    1. **Revise o plano** com sua equipe
    2. **Ajuste detalhes** específicos do seu negócio
    3. **Inicie a execução** seguindo o cronograma
    4. **Monitore e otimize** baseado nos OKRs definidos
    
    Lembre-se: este é um plano vivo. Adapte conforme aprende com os dados reais.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Começar Novo Planejamento"):
            for key in ['etapa_atual', 'dados_coletados', 'narrativa_gerada', 'plano_final']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        st.markdown("[Compartilhar plano](#)")

# Rodapé
st.markdown("---")
st.markdown("*Planejamento estratégico gerado por IA com Gemini 2.5 Flash*")
