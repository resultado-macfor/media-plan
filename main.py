import streamlit as st
import google.generativeai as genai
import os
from datetime import datetime, timedelta
import json
import time
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuração inicial
st.set_page_config(
    layout="wide",
    page_title="Planejador Tático de Mídias Pagas",
    page_icon="📊"
)

# Inicializar Gemini
gemini_api_key = os.getenv("GEM_API_KEY")
genai.configure(api_key=gemini_api_key)
modelo = genai.GenerativeModel("gemini-2.5-flash")

# ============================================================================
# BASE DE CONHECIMENTO DE MÍDIAS (COMPLETA)
# ============================================================================

TIPOS_CAMPANHA = [
    "Reconhecimento de Marca",
    "Alcance",
    "Tráfego",
    "Engajamento",
    "Visualizações de Vídeo",
    "Geração de Leads",
    "Promoção de App",
    "Vendas/Conversões",
    "Vendas de Catálogo",
    "Remarketing/Retargeting",
    "Branding Institucional",
]

ETAPAS_FUNIL = [
    "Consciência (Awareness)",
    "Interesse",
    "Consideração",
    "Intenção",
    "Conversão/Ação",
    "Retenção/Fidelização",
]

LEGACY_FUNNEL_MAP = {
    "Topo": "Consciência (Awareness)",
    "Meio": "Consideração",
    "Fundo": "Conversão/Ação",
}

KPIS_POR_ETAPA = {
    "Consciência (Awareness)": {
        "primarios": [
            {
                "nome": "Alcance",
                "formula": "Usuários únicos impactados",
                "faixa_tipica": "Varia por budget; ref: 1M alcance para ~R$15k-25k",
                "quando_usar": "Sempre em campanhas de awareness",
                "descricao": "Número de pessoas únicas expostas ao anúncio. Métrica principal segundo Byron Sharp."
            },
            {
                "nome": "Impressões",
                "formula": "Total de exibições do anúncio",
                "faixa_tipica": "2-3x o alcance com frequência saudável",
                "quando_usar": "Para medir volume total de exposição",
                "descricao": "Total de vezes que o anúncio foi exibido."
            },
            {
                "nome": "CPM",
                "formula": "(Custo total / Impressões) x 1000",
                "faixa_tipica": "R$8-25",
                "quando_usar": "Para avaliar eficiência de custo por exposição",
                "descricao": "Custo por mil impressões."
            }
        ],
        "secundarios": [
            {
                "nome": "Frequência",
                "formula": "Impressões / Alcance",
                "faixa_tipica": "1.5-3.0",
                "quando_usar": "Para controlar saturação",
                "descricao": "Média de exposições por pessoa."
            },
            {
                "nome": "Brand Lift",
                "formula": "% aumento em reconhecimento",
                "faixa_tipica": "3-15%",
                "quando_usar": "Para medir impacto real",
                "descricao": "Aumento na lembrança de marca."
            }
        ]
    },
    "Interesse": {
        "primarios": [
            {
                "nome": "CTR",
                "formula": "(Cliques / Impressões) x 100",
                "faixa_tipica": "0.5-2.0%",
                "quando_usar": "Para medir atratividade",
                "descricao": "Taxa de cliques - indica relevância do criativo."
            },
            {
                "nome": "Cliques",
                "formula": "Total de cliques",
                "faixa_tipica": "Depende de CTR",
                "quando_usar": "Volume de interesse",
                "descricao": "Total de interações ativas com o anúncio."
            },
            {
                "nome": "CPC",
                "formula": "Custo total / Cliques",
                "faixa_tipica": "R$0.30-3.00",
                "quando_usar": "Eficiência de custo",
                "descricao": "Custo por clique."
            }
        ],
        "secundarios": [
            {
                "nome": "Taxa de Engajamento",
                "formula": "(Engajamentos / Alcance) x 100",
                "faixa_tipica": "1-5%",
                "quando_usar": "Profundidade do interesse",
                "descricao": "Interações ativas com conteúdo."
            },
            {
                "nome": "ThruPlay",
                "formula": "Vídeos assistidos 15s+",
                "faixa_tipica": "15-40%",
                "quando_usar": "Interesse em vídeo",
                "descricao": "Visualizações longas de vídeo."
            }
        ]
    },
    "Consideração": {
        "primarios": [
            {
                "nome": "CTR",
                "formula": "(Cliques / Impressões) x 100",
                "faixa_tipica": "1.0-3.0%",
                "quando_usar": "Avaliação ativa",
                "descricao": "CTR mais alto indica consideração ativa."
            },
            {
                "nome": "CPC",
                "formula": "Custo total / Cliques",
                "faixa_tipica": "R$0.50-5.00",
                "quando_usar": "Custo de engajamento qualificado",
                "descricao": "Custo para engajar audiência qualificada."
            },
            {
                "nome": "Taxa de Engajamento",
                "formula": "(Engajamentos / Alcance) x 100",
                "faixa_tipica": "2-6%",
                "quando_usar": "Profundidade de avaliação",
                "descricao": "Engajamento profundo indica consideração."
            }
        ],
        "secundarios": [
            {
                "nome": "Páginas por Sessão",
                "formula": "Pageviews / Sessões",
                "faixa_tipica": "1.5-3.0",
                "quando_usar": "Exploração do site",
                "descricao": "Profundidade de navegação."
            },
            {
                "nome": "Bounce Rate",
                "formula": "(Sessões de página única / Total) x 100",
                "faixa_tipica": "30-60%",
                "quando_usar": "Relevância do tráfego",
                "descricao": "Taxa de rejeição - quanto menor, melhor."
            }
        ]
    },
    "Intenção": {
        "primarios": [
            {
                "nome": "Leads Gerados",
                "formula": "Total de formulários",
                "faixa_tipica": "2-8% do tráfego",
                "quando_usar": "Geração de leads",
                "descricao": "Contatos qualificados capturados."
            },
            {
                "nome": "CPL",
                "formula": "Custo total / Leads",
                "faixa_tipica": "R$5-50 (B2C); R$30-200 (B2B)",
                "quando_usar": "Eficiência de captação",
                "descricao": "Custo por lead."
            },
            {
                "nome": "Taxa de Conversão de Lead",
                "formula": "(Leads / Cliques) x 100",
                "faixa_tipica": "2-10%",
                "quando_usar": "Otimizar landing pages",
                "descricao": "Eficiência da página de captura."
            }
        ],
        "secundarios": [
            {
                "nome": "Adições ao Carrinho",
                "formula": "Add-to-cart events",
                "faixa_tipica": "5-15% do tráfego",
                "quando_usar": "E-commerce",
                "descricao": "Intenção de compra."
            },
            {
                "nome": "Mensagens Recebidas",
                "formula": "Total via WhatsApp/Messenger",
                "faixa_tipica": "R$1-10 por mensagem",
                "quando_usar": "Campanhas com CTA de mensagem",
                "descricao": "Conversas iniciadas."
            }
        ]
    },
    "Conversão/Ação": {
        "primarios": [
            {
                "nome": "Conversões",
                "formula": "Ações completadas",
                "faixa_tipica": "1-5% do tráfego",
                "quando_usar": "Performance principal",
                "descricao": "Total de vendas/cadastros."
            },
            {
                "nome": "CPA",
                "formula": "Custo total / Conversões",
                "faixa_tipica": "R$20-150 (e-commerce)",
                "quando_usar": "Eficiência de conversão",
                "descricao": "Custo por aquisição."
            },
            {
                "nome": "ROAS",
                "formula": "Receita / Investimento",
                "faixa_tipica": "2x-6x",
                "quando_usar": "Retorno financeiro",
                "descricao": "Retorno sobre investimento."
            }
        ],
        "secundarios": [
            {
                "nome": "Ticket Médio",
                "formula": "Receita / Conversões",
                "faixa_tipica": "Varia por segmento",
                "quando_usar": "Qualidade das conversões",
                "descricao": "Valor médio por venda."
            },
            {
                "nome": "Taxa de Conversão",
                "formula": "(Conversões / Cliques) x 100",
                "faixa_tipica": "1-5%",
                "quando_usar": "Otimizar funil",
                "descricao": "Eficiência do funil final."
            }
        ]
    },
    "Retenção/Fidelização": {
        "primarios": [
            {
                "nome": "Taxa de Retenção",
                "formula": "(Retidos / Início) x 100",
                "faixa_tipica": "60-80% mensal",
                "quando_usar": "Fidelização",
                "descricao": "Clientes que permanecem."
            },
            {
                "nome": "LTV",
                "formula": "Ticket x Frequência x Tempo",
                "faixa_tipica": "3-5x o CPA",
                "quando_usar": "Valor do cliente",
                "descricao": "Valor vitalício do cliente."
            },
            {
                "nome": "Taxa de Recompra",
                "formula": "(Compras recorrentes / Total) x 100",
                "faixa_tipica": "20-40% em 90 dias",
                "quando_usar": "Efetividade da retenção",
                "descricao": "Clientes que compram novamente."
            }
        ],
        "secundarios": [
            {
                "nome": "NPS",
                "formula": "% Promotores - % Detratores",
                "faixa_tipica": "30-70",
                "quando_usar": "Satisfação",
                "descricao": "Propensão a recomendar."
            },
            {
                "nome": "Churn Rate",
                "formula": "(Perdidos / Total) x 100",
                "faixa_tipica": "2-8% mensal",
                "quando_usar": "Perda de base",
                "descricao": "Clientes perdidos."
            }
        ]
    }
}

PLATAFORMA_OBJETIVOS = {
    "Meta Ads (Facebook/Instagram)": [
        "Reconhecimento de Marca", "Alcance", "Tráfego", "Engajamento",
        "Visualizações de Vídeo", "Geração de Leads", "Vendas/Conversões",
        "Vendas de Catálogo", "Remarketing/Retargeting", "Promoção de App",
    ],
    "Google Ads": [
        "Reconhecimento de Marca", "Tráfego", "Vendas/Conversões",
        "Geração de Leads", "Promoção de App", "Alcance",
        "Vendas de Catálogo",
    ],
    "TikTok": [
        "Reconhecimento de Marca", "Alcance", "Tráfego", "Engajamento",
        "Visualizações de Vídeo", "Vendas/Conversões", "Geração de Leads",
    ],
    "LinkedIn": [
        "Reconhecimento de Marca", "Tráfego", "Engajamento",
        "Geração de Leads", "Branding Institucional",
    ],
    "YouTube": [
        "Reconhecimento de Marca", "Alcance", "Visualizações de Vídeo",
        "Tráfego", "Vendas/Conversões",
    ],
    "Mídia Programática": [
        "Reconhecimento de Marca", "Alcance", "Tráfego",
        "Remarketing/Retargeting", "Vendas/Conversões",
    ],
}

BENCHMARKS_BR = {
    "Meta Ads": {
        "CPM": {"min": 8.0, "max": 25.0, "medio": 15.0, "unidade": "R$"},
        "CPC": {"min": 0.30, "max": 3.00, "medio": 1.20, "unidade": "R$"},
        "CTR": {"min": 0.8, "max": 2.5, "medio": 1.5, "unidade": "%"},
        "CPA": {"min": 15.0, "max": 120.0, "medio": 55.0, "unidade": "R$"},
        "ROAS": {"min": 2.0, "max": 6.0, "medio": 3.5, "unidade": "x"},
    },
    "Google Ads": {
        "CPM": {"min": 5.0, "max": 35.0, "medio": 18.0, "unidade": "R$"},
        "CPC": {"min": 1.00, "max": 8.00, "medio": 3.50, "unidade": "R$"},
        "CTR": {"min": 2.0, "max": 8.0, "medio": 4.5, "unidade": "%"},
        "CPA": {"min": 25.0, "max": 200.0, "medio": 80.0, "unidade": "R$"},
        "ROAS": {"min": 2.0, "max": 8.0, "medio": 4.0, "unidade": "x"},
    },
    "TikTok": {
        "CPM": {"min": 5.0, "max": 20.0, "medio": 10.0, "unidade": "R$"},
        "CPC": {"min": 0.20, "max": 2.00, "medio": 0.80, "unidade": "R$"},
        "CTR": {"min": 0.5, "max": 2.0, "medio": 1.2, "unidade": "%"},
        "CPA": {"min": 10.0, "max": 80.0, "medio": 35.0, "unidade": "R$"},
        "ROAS": {"min": 1.5, "max": 5.0, "medio": 3.0, "unidade": "x"},
    },
    "LinkedIn": {
        "CPM": {"min": 30.0, "max": 80.0, "medio": 50.0, "unidade": "R$"},
        "CPC": {"min": 5.00, "max": 25.00, "medio": 12.00, "unidade": "R$"},
        "CTR": {"min": 0.3, "max": 1.0, "medio": 0.6, "unidade": "%"},
        "CPA": {"min": 50.0, "max": 500.0, "medio": 180.0, "unidade": "R$"},
    },
}

TEMPLATES_ALOCACAO_BUDGET = {
    "Marca Nova / Lançamento": {
        "descricao": "Foco em awareness e construção de audiência",
        "distribuicao": {
            "Consciência (Awareness)": 40,
            "Interesse": 25,
            "Consideração": 20,
            "Intenção": 10,
            "Conversão/Ação": 5,
            "Retenção/Fidelização": 0,
        },
    },
    "E-commerce / Performance": {
        "descricao": "Foco em conversões com suporte de awareness",
        "distribuicao": {
            "Consciência (Awareness)": 15,
            "Interesse": 10,
            "Consideração": 15,
            "Intenção": 20,
            "Conversão/Ação": 30,
            "Retenção/Fidelização": 10,
        },
    },
    "B2B / Geração de Leads": {
        "descricao": "Foco em leads qualificados com nurturing",
        "distribuicao": {
            "Consciência (Awareness)": 20,
            "Interesse": 20,
            "Consideração": 25,
            "Intenção": 25,
            "Conversão/Ação": 10,
            "Retenção/Fidelização": 0,
        },
    },
    "Branding / Institucional": {
        "descricao": "Foco em presença de marca e reputação",
        "distribuicao": {
            "Consciência (Awareness)": 45,
            "Interesse": 25,
            "Consideração": 15,
            "Intenção": 5,
            "Conversão/Ação": 5,
            "Retenção/Fidelização": 5,
        },
    },
    "Retenção / CRM": {
        "descricao": "Foco em base existente e recompra",
        "distribuicao": {
            "Consciência (Awareness)": 5,
            "Interesse": 5,
            "Consideração": 10,
            "Intenção": 15,
            "Conversão/Ação": 25,
            "Retenção/Fidelização": 40,
        },
    },
}

# ============================================================================
# BASE DE CONHECIMENTO PARA AVALIAÇÃO
# ============================================================================

TEORIA_FRAMEWORKS = {
    "Binet & Field": {
        "principio": "Regra 60/40: 60% do budget para construção de marca (emocional, amplo alcance) e 40% para ativação (racional, segmentada).",
        "aplicacao": "Campanhas de topo de funil devem ser emocionais; campanhas de fundo de funil podem ser mais racionais.",
        "erros_comuns": "Combinar construção de marca e ativação no mesmo criativo; medir awareness por métricas de conversão."
    },
    "Byron Sharp": {
        "principio": "Crescimento vem da aquisição de novos compradores leves, não da fidelização. Priorizar alcance sobre frequência.",
        "aplicacao": "Campanhas de awareness devem ter targeting amplo e foco em ativos distintivos de marca.",
        "erros_comuns": "Segmentação excessiva; foco excessivo em fidelização; mensagens muito focadas em produto."
    },
    "McKinsey CDJ": {
        "principio": "Touchpoints na avaliação ativa são 2-3x mais influentes que na consideração inicial. Loop de fidelidade permite recompra direta.",
        "aplicacao": "Investir em conteúdo de consideração (comparativos, demos, depoimentos) tem alto ROI.",
        "erros_comuns": "Ignorar a fase de avaliação ativa; não nutrir leads adequadamente."
    },
    "STDC (Kaushik)": {
        "principio": "See (maior audiência qualificada), Think (avaliação ativa), Do (transação), Care (clientes existentes).",
        "aplicacao": "Cada etapa tem métricas diferentes: See = alcance/CPM; Think = CTR/CPC; Do = CPA/ROAS; Care = LTV/recompra.",
        "erros_comuns": "Medir campanhas de See por CPA; medir campanhas de Do por alcance."
    }
}

TEORIA_ETAPAS = {
    "Consciência (Awareness)": {
        "objetivo": "Construir memória de marca e disponibilidade mental.",
        "metricas_primarias": ["Alcance", "Impressões", "CPM"],
        "metricas_secundarias": ["Frequência", "Brand Lift"],
        "canais_recomendados": ["YouTube", "Meta Ads", "TikTok", "Programática"],
        "erros_comuns": ["Medir por CPA", "Targeting muito restrito", "Frequência mal gerenciada"]
    },
    "Interesse": {
        "objetivo": "Despertar curiosidade e gerar engajamento inicial.",
        "metricas_primarias": ["CTR", "Cliques", "CPC"],
        "metricas_secundarias": ["Taxa de Engajamento", "ThruPlay", "Tempo no site"],
        "canais_recomendados": ["Meta Ads", "TikTok", "Google Discovery"],
        "erros_comuns": ["Otimizar só por volume sem qualidade", "Desalinhamento anúncio-landing page"]
    },
    "Consideração": {
        "objetivo": "Aprofundar avaliação e comparar alternativas.",
        "metricas_primarias": ["CTR qualificado", "Micro-conversões", "Páginas por sessão"],
        "metricas_secundarias": ["Bounce Rate", "Tempo em páginas de produto"],
        "canais_recomendados": ["Google Search", "YouTube", "LinkedIn"],
        "erros_comuns": ["Não nutrir leads", "Pular para conversão", "Falta de variedade de conteúdo"]
    },
    "Intenção": {
        "objetivo": "Capturar leads qualificados e sinais de compra.",
        "metricas_primarias": ["Leads", "CPL", "Taxa de conversão de lead"],
        "metricas_secundarias": ["Adições ao carrinho", "Mensagens recebidas"],
        "canais_recomendados": ["Google Search", "Meta Lead Ads", "WhatsApp"],
        "erros_comuns": ["Formulários longos", "Follow-up lento", "Otimizar só por CPL sem qualidade"]
    },
    "Conversão/Ação": {
        "objetivo": "Fechar vendas e gerar receita.",
        "metricas_primarias": ["Conversões", "CPA", "ROAS"],
        "metricas_secundarias": ["Ticket médio", "Taxa de conversão"],
        "canais_recomendados": ["Google Shopping", "Meta Dynamic Ads", "Remarketing"],
        "erros_comuns": ["Desalinhamento mensagem-landing page", "Ignorar atribuição", "Foco em audiências frias"]
    },
    "Retenção/Fidelização": {
        "objetivo": "Maximizar valor do cliente e reduzir churn.",
        "metricas_primarias": ["LTV", "Taxa de retenção", "Taxa de recompra"],
        "metricas_secundarias": ["NPS", "Churn Rate"],
        "canais_recomendados": ["Email", "WhatsApp", "Custom Audiences"],
        "erros_comuns": ["Ignorar base existente", "Tratar clientes como prospects", "Dependência excessiva de descontos"]
    }
}

TEORIA_PLATAFORMAS = {
    "Meta Ads": {
        "forte_para": ["Consciência", "Interesse", "Conversão"],
        "benchmarks": "CPM R$8-25, CPC R$0,30-3,00, CTR 0,8-2,5%",
        "diferencial_br": "CPM 70-94% abaixo da média global"
    },
    "Google Ads": {
        "forte_para": ["Consideração", "Intenção", "Conversão"],
        "benchmarks": "CPM R$5-35, CPC R$1-8, CTR 2-8%",
        "diferencial_br": "Maior segmento de anúncios digitais (R$4,1B)"
    },
    "TikTok": {
        "forte_para": ["Consciência", "Interesse"],
        "benchmarks": "CPM R$5-20, CPC R$0,20-2,00, CTR 0,5-2,0%",
        "diferencial_br": "91,7M usuários, alto engajamento orgânico"
    },
    "LinkedIn": {
        "forte_para": ["Consideração", "Intenção (B2B)"],
        "benchmarks": "CPM R$30-80, CPC R$5-25, CTR 0,3-1,0%",
        "diferencial_br": "Público B2B qualificado"
    },
    "YouTube": {
        "forte_para": ["Consciência", "Consideração"],
        "benchmarks": "CPM R$10-30, CPV R$0,02-0,15, VTR 15-40%",
        "diferencial_br": "144M usuários, formato de storytelling"
    },
    "WhatsApp": {
        "forte_para": ["Intenção", "Conversão", "Retenção"],
        "benchmarks": "Taxa de conversão 55%, valor médio R$557",
        "diferencial_br": "93,7% penetração, canal crítico no Brasil"
    }
}

# ============================================================================
# FUNÇÕES DE AVALIAÇÃO E REFINAMENTO
# ============================================================================

def avaliar_segmento(segmento_texto, tipo_segmento, dados_cliente):
    """
    Avalia um segmento gerado, identificando pontos genéricos, rasos ou repetitivos.
    Retorna uma avaliação crítica com pontos de melhoria.
    """
    
    # Construir base de conhecimento para avaliação
    teoria_relevante = ""
    
    if tipo_segmento == "analise_inicial":
        teoria_relevante = f"""
**Teoria de Diagnóstico:**
- Deve conter análise específica do negócio, não genérica
- Deve considerar área geográfica: {dados_cliente.get('area_geografica', 'não especificada')}
- Deve ter projeções realistas baseadas em orçamento: R$ {dados_cliente.get('orcamento', 0):,.2f}
- Deve conectar objetivos a estratégias iniciais
"""
    
    elif tipo_segmento == "arquitetura_canais":
        teoria_relevante = f"""
**Teoria de Arquitetura de Canais:**
{chr(10).join([f"- {k}: {v['forte_para']} - {v['benchmarks']}" for k, v in TEORIA_PLATAFORMAS.items()])}

**Alinhamento por Etapa do Funil:**
{chr(10).join([f"- {k}: {v['canais_recomendados']}" for k, v in TEORIA_ETAPAS.items()])}
"""
    
    elif tipo_segmento == "estrutura_plano":
        teoria_relevante = f"""
**Teoria de Estrutura de Planos:**
- Binet & Field: {TEORIA_FRAMEWORKS['Binet & Field']['principio']}
- Deve definir fases sequenciais com objetivos claros
- Cada fase deve ter OKRs específicos
- Deve considerar alocação por etapa do funil
"""
    
    elif tipo_segmento == "fases_detalhadas":
        etapas_texto = ""
        for etapa, info in TEORIA_ETAPAS.items():
            etapas_texto += f"""
**{etapa}**
- Objetivo: {info['objetivo']}
- Métricas primárias: {', '.join(info['metricas_primarias'])}
- Erros comuns: {', '.join(info['erros_comuns'])}
"""
        teoria_relevante = etapas_texto
    
    elif tipo_segmento == "cronograma":
        teoria_relevante = """
**Teoria de Cronograma:**
- Deve ter prazos específicos, não genéricos
- Deve incluir marcos de avaliação
- Deve considerar sazonalidades
- Deve ter gatilhos de ativação baseados em dados
"""
    
    prompt_avaliacao = f"""
Você é um avaliador crítico de planos de mídia. Sua função é identificar pontos fracos em segmentos de planejamento.

**SEGMENTO A AVALIAR:**
{tipo_segmento.upper()}

{segmento_texto}

**DADOS DO CLIENTE:**
- Cliente: {dados_cliente.get('cliente', 'N/A')}
- Orçamento: R$ {dados_cliente.get('orcamento', 0):,.2f}
- Área Geográfica: {dados_cliente.get('area_geografica', 'N/A')}
- Objetivos: {dados_cliente.get('objetivos', 'N/A')}

**BASE DE CONHECIMENTO PARA AVALIAÇÃO:**
{teoria_relevante}

**CRITÉRIOS DE AVALIAÇÃO:**

1. **ESPECIFICIDADE** (0-10): O texto é específico para este cliente ou poderia ser usado para qualquer um?
   - Identifique frases genéricas que poderiam estar em qualquer plano

2. **PROFUNDIDADE** (0-10): O texto aprofunda nos detalhes ou é superficial?
   - Identifique onde faltam dados, benchmarks ou justificativas

3. **ORIGINALIDADE** (0-10): O texto é repetitivo ou traz insights novos?
   - Identifique repetições de conceitos ou falta de ideias originais

4. **ALINHAMENTO TEÓRICO** (0-10): O texto está alinhado com as melhores práticas?
   - Identifique desvios das recomendações teóricas

5. **APLICAÇÃO PRÁTICA** (0-10): O texto é acionável ou muito abstrato?
   - Identifique onde faltam elementos práticos de execução

**FORMATO DA RESPOSTA:**

## AVALIAÇÃO CRÍTICA

### Pontuação Geral
- Especificidade: [X]/10
- Profundidade: [X]/10
- Originalidade: [X]/10
- Alinhamento Teórico: [X]/10
- Aplicação Prática: [X]/10
- **Média: [X]/10**

### Pontos Fortes
- [Listar 2-3 pontos fortes do segmento]

### Pontos Fracos Identificados
1. [Ponto fraco 1] - [Exemplo concreto do texto]
2. [Ponto fraco 2] - [Exemplo concreto do texto]
3. [Ponto fraco 3] - [Exemplo concreto do texto]

### Sugestões de Melhoria
1. [Sugestão específica 1]
2. [Sugestão específica 2]
3. [Sugestão específica 3]

### Referências da Base de Conhecimento
- [Cite quais conceitos da base de conhecimento se aplicam aqui]
"""
    
    response = modelo.generate_content(prompt_avaliacao)
    return response.text


def refinar_segmento(segmento_original, avaliacao, tipo_segmento, dados_cliente):
    """
    Refina o segmento original com base na avaliação e na base de conhecimento.
    """
    
    # Construir contexto da base de conhecimento
    conhecimento_base = ""
    
    if tipo_segmento == "analise_inicial":
        conhecimento_base = f"""
**Base de Conhecimento - Diagnóstico:**
- Use benchmarks reais do Brasil: Meta CPM R$8-25, Google CPM R$5-35, TikTok CPM R$5-20
- Considere a área geográfica {dados_cliente.get('area_geografica', '')} nas projeções
- Conecte cada insight aos objetivos do cliente: {dados_cliente.get('objetivos', '')}
- Inclua projeções realistas para R$ {dados_cliente.get('orcamento', 0):,.2f}
"""
    
    elif tipo_segmento == "arquitetura_canais":
        conhecimento_base = f"""
**Base de Conhecimento - Arquitetura de Canais:**
{chr(10).join([f"- {k}: Ideal para {v['forte_para']}. Benchmarks: {v['benchmarks']}. {v.get('diferencial_br', '')}" for k, v in TEORIA_PLATAFORMAS.items()])}

**Matriz de Alocação por Etapa:**
{chr(10).join([f"- {k}: Recomendado {v['canais_recomendados']}" for k, v in TEORIA_ETAPAS.items()])}

**Orçamento do cliente: R$ {dados_cliente.get('orcamento', 0):,.2f}**
- Inclua valores absolutos em R$, não apenas percentuais
- Justifique cada alocação com benchmarks
"""
    
    elif tipo_segmento == "estrutura_plano":
        conhecimento_base = f"""
**Base de Conhecimento - Estrutura:**
- Binet & Field 60/40: {TEORIA_FRAMEWORKS['Binet & Field']['principio']}
- STDC: See (alcance), Think (CTR), Do (conversão), Care (retenção)
- Cada fase deve ter OKRs específicos baseados nas metas do cliente
- Considere a área geográfica {dados_cliente.get('area_geografica', '')} no timing

**Templates de Alocação (referência):**
{chr(10).join([f"- {k}: {v['descricao']}" for k, v in TEMPLATES_ALOCACAO_BUDGET.items()])}
"""
    
    elif tipo_segmento == "fases_detalhadas":
        conhecimento_base = f"""
**Base de Conhecimento - Detalhamento por Etapa:**
{chr(10).join([f"**{etapa}:** Objetivo: {info['objetivo']} | Métricas: {', '.join(info['metricas_primarias'])} | Evitar: {', '.join(info['erros_comuns'])}" for etapa, info in TEORIA_ETAPAS.items()])}

**Orçamento total: R$ {dados_cliente.get('orcamento', 0):,.2f}**
- Cada fase deve ter budget específico em R$
- Inclua distribuição por canal dentro de cada fase
- Use benchmarks reais para justificar as escolhas
"""
    
    elif tipo_segmento == "cronograma":
        conhecimento_base = f"""
**Base de Conhecimento - Cronograma:**
- Inclua datas específicas (ex: "Semana 1-2 de abril")
- Defina marcos de avaliação a cada 2-4 semanas
- Considere sazonalidades relevantes para {dados_cliente.get('area_geografica', '')}
- Inclua gatilhos baseados em performance (ex: "se CPA < R$50, aumentar budget em 20%")
"""
    
    prompt_refinamento = f"""
Você é um Estrategista de Mídias Pagas Sênior. Sua tarefa é REFINAR um segmento de plano de mídia com base em uma avaliação crítica.

**SEGMENTO ORIGINAL:**
{tipo_segmento.upper()}

{segmento_original}

**AVALIAÇÃO CRÍTICA RECEBIDA:**
{avaliacao}

**DADOS DO CLIENTE:**
- Cliente: {dados_cliente.get('cliente', 'N/A')}
- Orçamento: R$ {dados_cliente.get('orcamento', 0):,.2f}
- Área Geográfica: {dados_cliente.get('area_geografica', 'N/A')}
- Objetivos: {dados_cliente.get('objetivos', 'N/A')}
- Metas definidas: {dados_cliente.get('metas_iniciais', [])}

**BASE DE CONHECIMENTO PARA REFINAMENTO:**
{conhecimento_base}

**INSTRUÇÕES:**

1. Mantenha a estrutura geral do segmento original
2. Incorpore as sugestões de melhoria da avaliação
3. Use a base de conhecimento para adicionar dados concretos (benchmarks, valores, prazos)
4. Torne o texto mais específico para este cliente
5. Adicione profundidade onde a avaliação apontou superficialidade
6. Elimine repetições e clichês
7. Garanta que cada recomendação tenha uma justificativa

**REGRAS:**
- NÃO remova informações relevantes do original
- NÃO invente dados sem base nos benchmarks fornecidos
- Mantenha o tom profissional e executivo
- Use a área geográfica e orçamento para contextualizar

Produza a versão REFINADA do segmento, com o mesmo formato e estrutura do original, porém mais específico, profundo e acionável.
"""
    
    response = modelo.generate_content(prompt_refinamento)
    return response.text


def gerar_com_avaliacao(funcao_geradora, tipo_segmento, **kwargs):
    """
    Função wrapper que:
    1. Gera o segmento inicial
    2. Avalia o segmento
    3. Refina com base na avaliação
    4. Retorna o segmento refinado
    """
    
    # Extrair dados do cliente do kwargs
    dados_cliente = {
        'cliente': kwargs.get('cliente', ''),
        'orcamento': kwargs.get('orcamento', 0),
        'area_geografica': kwargs.get('area_geografica', ''),
        'objetivos': kwargs.get('objetivos', ''),
        'metas_iniciais': st.session_state.get('metas_iniciais', [])
    }
    
    # PASSO 1: Geração inicial
    with st.spinner(f"Gerando {tipo_segmento}..."):
        segmento_inicial = funcao_geradora(**kwargs)
    
    # PASSO 2: Avaliação
    with st.spinner(f"Avaliando qualidade do {tipo_segmento}..."):
        avaliacao = avaliar_segmento(segmento_inicial, tipo_segmento, dados_cliente)
    
    # PASSO 3: Refinamento
    with st.spinner(f"Refinando {tipo_segmento} com base na avaliação..."):
        segmento_refinado = refinar_segmento(segmento_inicial, avaliacao, tipo_segmento, dados_cliente)
    
    # Armazenar avaliação para debug (opcional)
    if 'avaliacoes' not in st.session_state:
        st.session_state.avaliacoes = {}
    st.session_state.avaliacoes[tipo_segmento] = avaliacao
    
    return segmento_refinado

# ============================================================================
# FUNÇÕES DE GERAÇÃO (adaptadas para usar o sistema de avaliação)
# ============================================================================

def gerar_analise_inicial(cliente, orcamento, objetivos, contexto, canais_preferencia, area_geografica,
                         instrucoes_refinamento=None, versao_anterior=None):
    """Etapa 1: Análise inicial - Diagnóstico do negócio"""
    
    if instrucoes_refinamento and versao_anterior:
        # Se for refinamento manual, usar o fluxo normal
        prompt = f"""
Você é um Estrategista de Mídias Pagas Sênior. Abaixo está uma análise inicial para {cliente}.
O usuário pediu ajustes específicos. MANTENHA a estrutura geral, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO:**
{instrucoes_refinamento}

**DADOS DO CLIENTE:**
- Cliente: {cliente}
- Orçamento: R$ {orcamento:,.2f}
- Área Geográfica: {area_geografica}
- Objetivos: {objetivos}
- Contexto: {contexto}
- Canais de Interesse: {canais_preferencia}

Retorne a versão COMPLETA da análise, aplicando apenas os refinamentos.
"""
        response = modelo.generate_content(prompt)
        return response.text
    
    else:
        # Geração inicial normal
        prompt = f"""
Você é um Estrategista de Mídias Pagas Sênior. Faça uma ANÁLISE INICIAL detalhada.

**DADOS DO CLIENTE:**
- Cliente: {cliente}
- Orçamento Total: R$ {orcamento:,.2f}
- Área Geográfica de Atuação: {area_geografica}
- Objetivos Principais: {objetivos}
- Contexto/Desafios: {contexto}
- Canais de Interesse: {canais_preferencia if canais_preferencia else "A definir"}

**FRAMEWORKS ESTRATÉGICOS (use como base):**
- Binet & Field: 60% construção de marca / 40% ativação
- Byron Sharp: Crescimento via novos compradores, priorizar alcance
- McKinsey CDJ: Touchpoints na avaliação ativa são 2-3x mais influentes
- STDC: See (awareness), Think (consideração), Do (conversão), Care (retenção)

**BENCHMARKS BRASIL (para projeções realistas):**
- Meta Ads: CPM R$8-25, CPC R$0,30-3,00, CTR 0,8-2,5%
- Google Ads: CPM R$5-35, CPC R$1-8, CTR 2-8%
- WhatsApp: 93,7% penetração, 55% conversão

**CONSIDERAÇÕES POR ÁREA GEOGRÁFICA:**
- Se {area_geografica} for nacional: considerar diferenças regionais (Sudeste vs Nordeste)
- Se {area_geografica} for estadual/municipal: ajustar CPMs e concorrência local

**ESTRUTURA DA ANÁLISE:**

## 1. DIAGNÓSTICO DO NEGÓCIO
[Análise do cliente, seus desafios e oportunidades considerando a área geográfica {area_geografica}]

## 2. POTENCIAL DO ORÇAMENTO
[O que R$ {orcamento:,.2f} pode entregar em {area_geografica} - projeções de alcance, cliques, leads]

## 3. DIRECIONAMENTOS ESTRATÉGICOS INICIAIS
[Recomendações preliminares baseadas nos objetivos e área geográfica]

## 4. PONTOS CRÍTICOS A CONSIDERAR
[Questões que precisam ser endereçadas no planejamento]
"""
        response = modelo.generate_content(prompt)
        return response.text


def recomendar_arquitetura_canais(analise_inicial, objetivos, orcamento, canais_preferencia, area_geografica,
                                  instrucoes_refinamento=None, versao_anterior=None):
    """Etapa 2: Arquitetura de canais"""
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
Você é um Estrategista de Mídias Pagas Sênior. Abaixo está uma arquitetura de canais.
O usuário pediu ajustes específicos. MANTENHA a estrutura geral, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO:**
{instrucoes_refinamento}

**CONTEXTO:**
- Objetivos: {objetivos}
- Orçamento: R$ {orcamento:,.2f}
- Área Geográfica: {area_geografica}

Retorne a versão COMPLETA da arquitetura, aplicando apenas os refinamentos.
"""
        response = modelo.generate_content(prompt)
        return response.text
    
    else:
        prompt = f"""
Você é um Estrategista de Mídias Pagas Sênior. Com base na análise inicial, recomende a ARQUITETURA DE CANAIS.

**ANÁLISE INICIAL:**
{analise_inicial[:500]}...

**Objetivos:** {objetivos}
**Orçamento:** R$ {orcamento:,.2f}
**Área Geográfica:** {area_geografica}
**Canais considerados:** {canais_preferencia if canais_preferencia else "A definir"}

**ALINHAMENTO CANAL X ETAPA DO FUNIL:**

| Canal | Melhor para | Por quê |
|-------|-------------|---------|
| YouTube | Consciência, Consideração | 75% descobrem novas marcas aqui, TrueView otimizado |
| Meta Ads | Consciência, Interesse, Conversão | Alcance massivo, CPM baixo no Brasil (R$8-25) |
| TikTok | Consciência, Interesse | 91,7M usuários, alto engajamento orgânico |
| Google Search | Consideração, Intenção, Conversão | Captura intenção ativa, CTR 3-8% |
| LinkedIn | Consideração, Intenção (B2B) | Público profissional qualificado |
| WhatsApp | Intenção, Conversão, Retenção | 93,7% penetração, 55% conversão |
| Programática | Consciência, Retenção | Alcance complementar, frequency capping |

**CONSIDERAÇÕES PARA {area_geografica}:**
- [Ajustar recomendações com base na área geográfica - densidade populacional, hábitos de consumo de mídia, etc.]

**ESTRUTURA DA RECOMENDAÇÃO:**

## 1. ARQUITETURA DE CANAIS RECOMENDADA
[Lista dos canais selecionados e justificativa para cada um, considerando {area_geografica}]

## 2. FUNÇÃO DE CADA CANAL NA JORNADA
[Qual etapa do funil cada canal atende e por quê]

## 3. ALOCAÇÃO DE BUDGET POR CANAL
[Tabela com percentuais e valores em R$, com justificativa baseada em benchmarks]
Forneça os dados em formato que possa ser extraído para gráficos (percentuais claros)

## 4. SINERGIA ENTRE CANAIS
[Como os canais trabalham juntos - fluxo de tráfego e remarketing]

## 5. PROJEÇÕES DE PERFORMANCE PARA {area_geografica}
[Estimativas de alcance, cliques, leads com base nos benchmarks BR ajustados para a região]
"""
        response = modelo.generate_content(prompt)
        return response.text


def definir_estrutura_plano(arquitetura_canais, objetivos, cliente, orcamento, area_geografica, metas_iniciais=None,
                           instrucoes_refinamento=None, versao_anterior=None):
    """Etapa 3: Estrutura do plano"""
    
    metas_texto = ""
    if metas_iniciais:
        metas_texto = "\n**METAS GLOBAIS DO PLANO (definidas pelo cliente):**\n"
        for meta in metas_iniciais:
            metas_texto += f"- {meta}\n"
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
Você é um Estrategista de Mídias Pagas Sênior. Abaixo está uma estrutura de plano.
O usuário pediu ajustes específicos. MANTENHA a estrutura geral, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO:**
{instrucoes_refinamento}

Retorne a versão COMPLETA da estrutura, aplicando apenas os refinamentos.
"""
        response = modelo.generate_content(prompt)
        return response.text
    
    else:
        # Construir templates de alocação
        templates_texto = ""
        for nome, template in TEMPLATES_ALOCACAO_BUDGET.items():
            distribuicao = ", ".join([f"{etapa}: {pct}%" for etapa, pct in template["distribuicao"].items() if pct > 0])
            templates_texto += f"\n- **{nome}**: {template['descricao']} | {distribuicao}"
        
        prompt = f"""
Você é um Estrategista de Mídias Pagas Sênior. Defina a ESTRUTURA DO PLANO.

**Arquitetura de Canais:**
{arquitetura_canais[:400]}...

**Cliente:** {cliente}
**Objetivos:** {objetivos}
**Área Geográfica:** {area_geografica}
**Orçamento Total:** R$ {orcamento:,.2f}

{metas_texto}

**TEMPLATES DE ALOCAÇÃO POR ETAPA (referência):**
{templates_texto}

**PRINCÍPIOS ESTRATÉGICOS:**
- Consciência: Alcance e CPM - construir memória de marca
- Interesse: CTR e CPC - despertar curiosidade
- Consideração: Micro-conversões e engajamento profundo
- Intenção: Leads e CPL - capturar contatos qualificados
- Conversão: CPA e ROAS - fechar vendas
- Retenção: LTV e taxa de recompra - maximizar valor do cliente

**ESTRUTURA DA RECOMENDAÇÃO:**

## 1. MODELO DE ALOCAÇÃO POR ETAPA DO FUNIL
[Percentual do budget dedicado a cada etapa, com justificativa baseada nos objetivos]
Forneça percentuais claros que possam ser visualizados em gráficos.

## 2. FASES DO PLANO
[Defina 2-4 fases sequenciais, cada uma com:]
- Nome da fase
- Duração sugerida (em semanas)
- Etapas do funil priorizadas
- Alocação de budget (percentual do total)
- OKRs principais da fase (considerando as metas globais definidas)

## 3. FLUXO DE INFORMAÇÕES ENTRE FASES
[Como uma fase alimenta a próxima - ex: fase 1 gera audiência para remarketing na fase 2]

## 4. MATRIZ DE RESPONSABILIDADES POR CANAL EM CADA FASE
[Qual canal atua em qual fase e com qual objetivo]
"""
        response = modelo.generate_content(prompt)
        return response.text


def detalhar_fases(estrutura_plano, arquitetura_canais, orcamento, cliente, objetivos, area_geografica,
                   metas_okr=None, instrucoes_refinamento=None, versao_anterior=None):
    """Etapa 4: Detalhamento tático de cada fase"""
    
    metas_texto = ""
    if metas_okr:
        metas_texto = "\n**METAS DEFINIDAS PELO CLIENTE:**\n"
        for fase, metas in metas_okr.items():
            metas_texto += f"\n**{fase}:**\n"
            for meta in metas:
                metas_texto += f"- {meta}\n"
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
Você é um Estrategista de Mídias Pagas Sênior. Abaixo está o detalhamento das fases.
O usuário pediu ajustes específicos. MANTENHA a estrutura geral, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO:**
{instrucoes_refinamento}

{metas_texto}

Retorne a versão COMPLETA do detalhamento, aplicando apenas os refinamentos.
"""
        response = modelo.generate_content(prompt)
        return response.text
    
    else:
        prompt = f"""
Você é um Estrategista de Mídias Pagas Sênior. Detalhe CADA FASE do plano.

**Estrutura do Plano:**
{estrutura_plano[:500]}...

**Arquitetura de Canais:**
{arquitetura_canais[:300]}...

**Cliente:** {cliente}
**Objetivos:** {objetivos}
**Área Geográfica:** {area_geografica}
**Orçamento Total:** R$ {orcamento:,.2f}

{metas_texto}

**TEMPLATE PARA CADA FASE:**

### FASE [NÚMERO]: [NOME DA FASE]

**📊 OBJETIVOS E OKRs**
- Objetivo principal:
- OKR 1: [Métrica primária] - Meta: [valor]
- OKR 2: [Métrica secundária] - Meta: [valor]
- ⚠️ O que NÃO medir nesta fase: [métricas inadequadas para esta etapa]

**💰 ALOCAÇÃO DE BUDGET**
- Valor: R$ [X] ([Y]% do total)
- Distribuição por canal:
  * Canal A: R$ [X] ([Y]%) - Justificativa
  * Canal B: R$ [X] ([Y]%) - Justificativa

**🎯 PÚBLICO-ALVO**
- Segmentação primária (considerando {area_geografica}):
- Segmentação secundária:
- Listas de remarketing a construir:

**📱 ATUAÇÃO POR PLATAFORMA**
- [Plataforma 1]:
  * Tipo de campanha: [ex: Reconhecimento, Tráfego, Conversão]
  * Formato: [ex: Reels, Search, Display]
  * Objetivo específico:
  * Benchmarks esperados: [CPM, CPC, CTR com base nos dados BR]

**🎨 ESTRATÉGIA CRIATIVA**
- Abordagem criativa principal:
- Tipos de conteúdo:
- Testes A/B sugeridos:

**⏱️ TIMING E MARCOS**
- Duração: [X semanas]
- Datas importantes:
- Pontos de avaliação:

**🔄 CONEXÃO COM PRÓXIMA FASE**
- O que esta fase entrega para a fase seguinte:
- Audiências a nutrir para remarketing:

[Repita para cada fase identificada na estrutura do plano]
"""
        response = modelo.generate_content(prompt)
        return response.text


def criar_cronograma(fases_detalhadas, cliente, orcamento, area_geografica,
                    instrucoes_refinamento=None, versao_anterior=None):
    """Etapa 5: Cronograma de execução"""
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
Você é um Estrategista de Mídias Pagas Sênior. Abaixo está um cronograma.
O usuário pediu ajustes específicos. MANTENHA a estrutura geral, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO:**
{instrucoes_refinamento}

Retorne a versão COMPLETA do cronograma, aplicando apenas os refinamentos.
"""
        response = modelo.generate_content(prompt)
        return response.text
    
    else:
        prompt = f"""
Você é um Estrategista de Mídias Pagas Sênior. Crie um CRONOGRAMA DE EXECUÇÃO detalhado.

**Fases Detalhadas:**
{fases_detalhadas[:800]}...

**Cliente:** {cliente}
**Área Geográfica:** {area_geografica}
**Orçamento Total:** R$ {orcamento:,.2f}

**ESTRUTURA DO CRONOGRAMA:**

## 1. VISÃO GERAL DA EXECUÇÃO
[Parágrafo resumindo a sequência e duração total, considerando particularidades de {area_geografica}]

## 2. CRONOGRAMA MÊS A MÊS

**MÊS 1 - [NOME DA FASE]**
- Semana 1-2:
  * Ativações:
  * Budget previsto:
  * Métricas a monitorar:
- Semana 3-4:
  * Ativações:
  * Ajustes baseados em dados iniciais:
- Entregáveis do mês:

**MÊS 2 - [NOME DA FASE]**
[mesma estrutura...]

[Continuar para todos os meses, garantindo que as datas estejam claras para visualização em gráfico]

## 3. MARCOS DE AVALIAÇÃO
- [Data específica]: Revisão de performance e realocação de budget
- [Data específica]: Teste A/B de criativos
- [Data específica]: Avaliação de resultados e planejamento próximo mês

## 4. GATILHOS DE ATIVAÇÃO
- [Evento]: Dispara [ação]
- [Evento]: Dispara [ação]

## 5. CHECKLIST DE IMPLEMENTAÇÃO
- [ ] Configurar [canal] com [especificações]
- [ ] Implementar pixels de rastreamento
- [ ] Criar audiências de remarketing
- [ ] etc.
"""
        response = modelo.generate_content(prompt)
        return response.text


def gerar_recomendacoes_executivas(plano_completo, cliente, objetivos, area_geografica,
                                  instrucoes_refinamento=None, versao_anterior=None):
    """Etapa 6: Recomendações executivas e próximos passos"""
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
Você é um Estrategista de Mídias Pagas Sênior. Abaixo estão recomendações executivas.
O usuário pediu ajustes específicos. MANTENHA a estrutura geral, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO:**
{instrucoes_refinamento}

Retorne a versão COMPLETA das recomendações, aplicando apenas os refinamentos.
"""
        response = modelo.generate_content(prompt)
        return response.text
    
    else:
        prompt = f"""
Você é um Estrategista de Mídias Pagas Sênior. Gere RECOMENDAÇÕES EXECUTIVAS finais.

**Resumo do Plano:**
{plano_completo[:1000]}...

**Cliente:** {cliente}
**Área Geográfica:** {area_geografica}
**Objetivos originais:** {objetivos}

**ESTRUTURA DAS RECOMENDAÇÕES:**

## 1. SÍNTESE EXECUTIVA
[Resumo do plano em 1 parágrafo - alocação de budget, principais canais, fases, considerações para {area_geografica}]

## 2. RECOMENDAÇÕES DE OTIMIZAÇÃO CONTÍNUA
- O que monitorar diariamente:
- O que avaliar semanalmente:
- O que revisar mensalmente:
- Sinais de sucesso:
- Sinais de alerta:

## 3. APRENDIZADOS A VALIDAR
[Hipóteses a serem confirmadas durante a execução]

## 4. PRÓXIMOS PASSOS IMEDIATOS
1. [ ] [Ação] - Responsável: [quem] - Prazo: [quando]
2. [ ] [Ação] - Responsável: [quem] - Prazo: [quando]
3. [ ] [Ação] - Responsável: [quem] - Prazo: [quando]

## 5. PERGUNTAS PENDENTES
[Questões a serem resolvidas antes da execução]
"""
        response = modelo.generate_content(prompt)
        return response.text

# ============================================================================
# FUNÇÕES DE INTERFACE
# ============================================================================

def render_refinamento_box(etapa_nome, etapa_chave, funcao_gerar, **kwargs):
    """Caixa de refinamento"""
    
    st.markdown("---")
    st.subheader("✏️ Refinar esta etapa")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Ajustes na {etapa_nome}**")
    with col2:
        mostrar_form = st.checkbox("Refinar", key=f"show_refine_{etapa_chave}")
    
    if mostrar_form:
        st.markdown("Descreva os ajustes desejados. Exemplos:")
        st.markdown("- 'Aumente o budget da Fase 2 para 40%'")
        st.markdown("- 'Adicione TikTok como canal'")
        st.markdown("- 'Mude as métricas da Fase 1 para Alcance e CPM'")
        
        with st.form(key=f"refine_form_{etapa_chave}"):
            instrucao = st.text_area(
                "Instruções:",
                height=100,
                placeholder="Descreva os ajustes..."
            )
            
            col1, col2 = st.columns(2)
            with col1:
                submit_refine = st.form_submit_button("🔄 Aplicar Ajustes", use_container_width=True)
            with col2:
                cancel_refine = st.form_submit_button("Cancelar", use_container_width=True)
            
            if submit_refine and instrucao:
                with st.spinner("Aplicando ajustes..."):
                    versao_anterior = st.session_state.narrativa_gerada[etapa_chave]
                    kwargs['instrucoes_refinamento'] = instrucao
                    kwargs['versao_anterior'] = versao_anterior
                    
                    nova_versao = funcao_gerar(**kwargs)
                    st.session_state.narrativa_gerada[etapa_chave] = nova_versao
                    st.rerun()


def render_metas_iniciais_editor():
    """Editor de metas OKR no início do planejamento"""
    
    st.markdown("---")
    st.subheader("🎯 Metas do Plano")
    st.markdown("Defina as metas globais que o plano deve alcançar:")
    
    metas = []
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Meta 1**")
        metrica1 = st.selectbox("Métrica", ["Alcance", "Impressões", "CTR", "CPC", "Leads", "CPL", "Conversões", "CPA", "ROAS", "Receita"], key="meta1_metrica")
        valor1 = st.text_input("Valor", key="meta1_valor", placeholder="Ex: 500000")
        unidade1 = "milhões" if metrica1 in ["Alcance", "Impressões"] else ("%" if metrica1 == "CTR" else ("R$" if metrica1 in ["CPC", "CPL", "CPA", "Receita"] else ("x" if metrica1 == "ROAS" else "")))
        if metrica1 and valor1:
            metas.append(f"{metrica1}: {valor1} {unidade1}")
    
    with col2:
        st.markdown("**Meta 2**")
        metrica2 = st.selectbox("Métrica", ["Alcance", "Impressões", "CTR", "CPC", "Leads", "CPL", "Conversões", "CPA", "ROAS", "Receita"], key="meta2_metrica", index=4)
        valor2 = st.text_input("Valor", key="meta2_valor", placeholder="Ex: 1000")
        unidade2 = "milhões" if metrica2 in ["Alcance", "Impressões"] else ("%" if metrica2 == "CTR" else ("R$" if metrica2 in ["CPC", "CPL", "CPA", "Receita"] else ("x" if metrica2 == "ROAS" else "")))
        if metrica2 and valor2:
            metas.append(f"{metrica2}: {valor2} {unidade2}")
    
    with col3:
        st.markdown("**Meta 3**")
        metrica3 = st.selectbox("Métrica", ["Alcance", "Impressões", "CTR", "CPC", "Leads", "CPL", "Conversões", "CPA", "ROAS", "Receita"], key="meta3_metrica", index=6)
        valor3 = st.text_input("Valor", key="meta3_valor", placeholder="Ex: 200")
        unidade3 = "milhões" if metrica3 in ["Alcance", "Impressões"] else ("%" if metrica3 == "CTR" else ("R$" if metrica3 in ["CPC", "CPL", "CPA", "Receita"] else ("x" if metrica3 == "ROAS" else "")))
        if metrica3 and valor3:
            metas.append(f"{metrica3}: {valor3} {unidade3}")
    
    return metas


def render_metas_okr_editor(fases_detalhadas):
    """Editor de metas OKR por fase"""
    
    st.markdown("---")
    st.subheader("🎯 Definir Metas por Fase")
    st.markdown("Defina as metas específicas para cada fase do plano:")
    
    metas_por_fase = {}
    
    # Identificar fases
    fases = []
    linhas = fases_detalhadas.split('\n')
    for linha in linhas[:50]:
        if 'FASE' in linha.upper() and '**' in linha:
            match = re.search(r'\*\*FASE[:\s]*(\d+)[:\s]*(.*?)\*\*', linha, re.IGNORECASE)
            if match:
                fases.append(f"Fase {match.group(1)}: {match.group(2).strip()}")
    
    if not fases:
        fases = ["Fase 1", "Fase 2", "Fase 3", "Fase 4"]
    
    # Tabs para cada fase
    if fases:
        tabs = st.tabs([f"📊 {f[:20]}..." for f in fases])
        
        for idx, (fase, tab) in enumerate(zip(fases, tabs)):
            with tab:
                st.markdown(f"**Metas para {fase}**")
                
                metas_fase = []
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown("**Métrica**")
                with col2:
                    st.markdown("**Meta**")
                with col3:
                    st.markdown("**Unidade**")
                
                for i in range(3):  # Até 3 metas por fase
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        metrica = st.selectbox(
                            f"Métrica {i+1}",
                            ["Alcance", "Impressões", "CPM", "CTR", "CPC", "Leads", "CPL", "Conversões", "CPA", "ROAS", "Outro"],
                            key=f"metrica_{fase}_{i}",
                            label_visibility="collapsed",
                            index=i
                        )
                    
                    with col2:
                        valor = st.text_input(
                            "Valor",
                            key=f"valor_{fase}_{i}",
                            placeholder="Ex: 1.5",
                            label_visibility="collapsed"
                        )
                    
                    with col3:
                        if metrica in ["Alcance", "Impressões"]:
                            unidade = "milhões"
                        elif metrica in ["CPM", "CPC", "CPL", "CPA"]:
                            unidade = "R$"
                        elif metrica in ["CTR"]:
                            unidade = "%"
                        elif metrica in ["ROAS"]:
                            unidade = "x"
                        else:
                            unidade = st.text_input("Unidade", key=f"unidade_{fase}_{i}", placeholder="unid", label_visibility="collapsed")
                    
                    if metrica and valor and metrica != "Outro":
                        metas_fase.append(f"{metrica}: {valor} {unidade if unidade else ''}")
                    elif metrica == "Outro":
                        col_extra1, col_extra2 = st.columns(2)
                        with col_extra1:
                            outra_metrica = st.text_input("Qual métrica?", key=f"outra_{fase}_{i}")
                        with col_extra2:
                            outra_unidade = st.text_input("Unidade", key=f"outra_unid_{fase}_{i}", placeholder="ex: unidades")
                        if outra_metrica and valor:
                            metas_fase.append(f"{outra_metrica}: {valor} {outra_unidade if outra_unidade else ''}")
                
                if metas_fase:
                    metas_por_fase[fase] = metas_fase
                    st.success(f"✅ Metas definidas para {fase}")
    
    if metas_por_fase:
        if st.button("💾 Salvar Metas e Atualizar Fases", use_container_width=True):
            st.session_state.metas_okr = metas_por_fase
            st.success("Metas salvas! Use o botão de refinamento para atualizar as fases.")
            st.rerun()
    
    return metas_por_fase


def mostrar_avaliacao(tipo_segmento):
    """Mostra a avaliação do segmento (para debug/transparência)"""
    if 'avaliacoes' in st.session_state and tipo_segmento in st.session_state.avaliacoes:
        with st.expander("📋 Ver avaliação de qualidade deste segmento", expanded=False):
            st.markdown(st.session_state.avaliacoes[tipo_segmento])

# ============================================================================
# FUNÇÕES DE VISUALIZAÇÃO GRÁFICA
# ============================================================================

def criar_grafico_alocacao_budget(arquitetura_texto):
    """Extrai dados de alocação de budget do texto da arquitetura e cria gráfico"""
    
    # Tentar extrair dados de alocação do texto
    canais = []
    valores = []
    cores = px.colors.qualitative.Set3
    
    # Padrões comuns no texto
    linhas = arquitetura_texto.split('\n')
    for linha in linhas:
        # Procurar por padrões como "Meta Ads: R$ 15.000 (30%)" ou "Meta Ads: 30%"
        match = re.search(r'([A-Za-z\s]+):\s*R?\$?\s*([\d,\.]+)?\s*\(?(\d+)%\)?', linha)
        if match:
            canal = match.group(1).strip()
            percentual = int(match.group(3))
            if canal and percentual:
                canais.append(canal[:20])  # Limitar tamanho
                valores.append(percentual)
    
    # Se não encontrou nada, usar dados de exemplo baseados em benchmarks
    if not canais:
        canais = ["Meta Ads", "Google Ads", "TikTok", "LinkedIn", "YouTube", "Programática"]
        valores = [35, 25, 15, 10, 10, 5]  # Distribuição exemplo
    
    # Criar DataFrame
    df = pd.DataFrame({
        'Canal': canais,
        'Alocação (%)': valores
    })
    df = df.sort_values('Alocação (%)', ascending=True)
    
    # Criar gráfico de barras horizontais
    fig = px.bar(
        df, 
        x='Alocação (%)', 
        y='Canal',
        orientation='h',
        title='Distribuição de Budget por Canal',
        text='Alocação (%)',
        color='Alocação (%)',
        color_continuous_scale='Blues',
        labels={'Alocação (%)': 'Percentual do Budget'}
    )
    
    fig.update_traces(
        textposition='outside',
        marker=dict(line=dict(color='rgba(0,0,0,0.3)', width=1))
    )
    fig.update_layout(
        height=400,
        xaxis=dict(range=[0, max(valores) + 10]),
        showlegend=False,
        coloraxis_showscale=False
    )
    
    return fig

def criar_grafico_alocacao_funil(arquitetura_texto, estrutura_texto):
    """Cria gráfico de alocação por etapa do funil"""
    
    etapas = []
    percentuais = []
    
    # Tentar extrair da estrutura do plano
    linhas = estrutura_texto.split('\n') if estrutura_texto else []
    for linha in linhas:
        for etapa in ETAPAS_FUNIL:
            if etapa in linha:
                match = re.search(r'(\d+)%', linha)
                if match:
                    etapas.append(etapa)
                    percentuais.append(int(match.group(1)))
                    break
    
    # Se não encontrou, usar template baseado nos objetivos
    if not etapas:
        # Distribuição exemplo balanceada
        etapas = ETAPAS_FUNIL
        percentuais = [25, 15, 15, 15, 20, 10]
    
    # Criar DataFrame
    df = pd.DataFrame({
        'Etapa do Funil': etapas,
        'Alocação (%)': percentuais
    })
    
    # Criar gráfico de pizza/donut
    fig = go.Figure(data=[go.Pie(
        labels=df['Etapa do Funil'],
        values=df['Alocação (%)'],
        hole=.4,
        marker=dict(colors=px.colors.qualitative.Pastel),
        textinfo='label+percent',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>Alocação: %{value}%<extra></extra>'
    )])
    
    fig.update_layout(
        title='Distribuição de Budget por Etapa do Funil',
        height=400,
        annotations=[dict(text='Budget por Funil', x=0.5, y=0.5, font_size=12, showarrow=False)]
    )
    
    return fig

def criar_grafico_cronograma(fases_texto, orcamento_total):
    """Cria gráfico de Gantt para o cronograma de execução"""
    
    # Tentar extrair fases e durações do texto
    fases = []
    inicio = []
    fim = []
    budgets = []
    
    data_inicio = datetime.now().replace(day=1)
    
    # Padrão: procurar por "Fase X" ou "Mês X"
    linhas = fases_texto.split('\n')
    fase_atual = None
    duracao_semanas = 4  # padrão
    
    for i, linha in enumerate(linhas):
        # Procurar por títulos de fase
        if 'FASE' in linha.upper() or 'MÊS' in linha.upper():
            match = re.search(r'(FASE|MÊS)\s*(\d+)[:\s]*(.*?)(?:\*\*|$)', linha, re.IGNORECASE)
            if match:
                num_fase = match.group(2)
                nome_fase = match.group(3).strip() if match.group(3) else f"Fase {num_fase}"
                fase_atual = f"Fase {num_fase}: {nome_fase[:30]}"
                
                # Tentar encontrar duração nas próximas linhas
                for j in range(1, 5):
                    if i+j < len(linhas):
                        linha_seguinte = linhas[i+j]
                        if 'dura' in linha_seguinte.lower() or 'semana' in linha_seguinte.lower():
                            match_duracao = re.search(r'(\d+)\s*semanas?', linha_seguinte, re.IGNORECASE)
                            if match_duracao:
                                duracao_semanas = int(match_duracao.group(1))
                                break
                
                # Adicionar fase
                fases.append(fase_atual)
                data_fim = data_inicio + timedelta(weeks=duracao_semanas) if fases else data_inicio + timedelta(weeks=4)
                inicio.append(data_inicio.strftime('%Y-%m-%d'))
                fim.append(data_fim.strftime('%Y-%m-%d'))
                
                # Budget estimado (distribuição uniforme como fallback)
                budgets.append(orcamento_total / (len(linhas) // 20 + 1))
                
                data_inicio = data_fim
    
    # Se não encontrou fases, criar exemplo
    if not fases:
        fases = ["Fase 1: Aquecimento", "Fase 2: Lançamento", "Fase 3: Sustentação"]
        data_hoje = datetime.now().replace(day=1)
        for i, fase in enumerate(fases):
            inicio.append((data_hoje + timedelta(weeks=i*4)).strftime('%Y-%m-%d'))
            fim.append((data_hoje + timedelta(weeks=(i+1)*4)).strftime('%Y-%m-%d'))
            budgets.append(orcamento_total / 3)
    
    # Criar DataFrame para o Gantt
    df_gantt = pd.DataFrame({
        'Fase': fases,
        'Início': pd.to_datetime(inicio),
        'Fim': pd.to_datetime(fim),
        'Budget (R$)': budgets
    })
    
    # Criar gráfico de Gantt
    fig = px.timeline(
        df_gantt,
        x_start='Início',
        x_end='Fim',
        y='Fase',
        color='Budget (R$)',
        color_continuous_scale='Viridis',
        title='Cronograma de Execução por Fase',
        labels={'Fase': '', 'color': 'Budget (R$)'}
    )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=400,
        xaxis_title='Data',
        showlegend=False
    )
    
    # Formatar hover
    fig.update_traces(
        hovertemplate='<b>%{y}</b><br>Início: %{x|%d/%m/%Y}<br>Término: %{x|%d/%m/%Y}<br>Budget: R$ %{customdata[0]:,.0f}<extra></extra>',
        customdata=df_gantt[['Budget (R$)']]
    )
    
    return fig

def criar_grafico_projecao_metricas(orcamento_total):
    """Cria gráfico de projeção de métricas baseado em benchmarks"""
    
    # Estimativas baseadas em benchmarks
    metricas = {
        'Alcance (milhões)': orcamento_total / 15 * 1.2,  # ~1.2M por R$15k
        'Impressões (milhões)': orcamento_total / 15 * 3,
        'Cliques (milhares)': orcamento_total / 15 * 12,
        'Leads': orcamento_total / 15 * 150,
        'Conversões': orcamento_total / 15 * 30
    }
    
    df = pd.DataFrame({
        'Métrica': list(metricas.keys()),
        'Projeção': list(metricas.values())
    })
    
    fig = px.bar(
        df,
        x='Métrica',
        y='Projeção',
        title='Projeção de Métricas (Baseado em Benchmarks)',
        text=df['Projeção'].round(0).astype(int),
        color='Projeção',
        color_continuous_scale='Greens'
    )
    
    fig.update_traces(textposition='outside')
    fig.update_layout(
        height=400,
        xaxis_tickangle=-45,
        showlegend=False,
        coloraxis_showscale=False,
        yaxis_title='Volume Projetado'
    )
    
    return fig

def criar_grafico_comparativo_benchmarks():
    """Cria gráfico comparativo de benchmarks por plataforma"""
    
    dados = []
    for plataforma, metricas in BENCHMARKS_BR.items():
        if 'CPM' in metricas:
            dados.append({
                'Plataforma': plataforma,
                'CPM Médio (R$)': metricas['CPM']['medio'],
                'CPC Médio (R$)': metricas.get('CPC', {}).get('medio', 0),
                'CTR Médio (%)': metricas.get('CTR', {}).get('medio', 0)
            })
    
    df = pd.DataFrame(dados)
    
    # Criar subplots
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=('CPM Médio (R$)', 'CPC Médio (R$)', 'CTR Médio (%)'),
        shared_yaxes=False
    )
    
    # Adicionar barras para CPM
    fig.add_trace(
        go.Bar(x=df['Plataforma'], y=df['CPM Médio (R$)'], name='CPM', marker_color='rgb(55, 83, 109)'),
        row=1, col=1
    )
    
    # Adicionar barras para CPC
    fig.add_trace(
        go.Bar(x=df['Plataforma'], y=df['CPC Médio (R$)'], name='CPC', marker_color='rgb(26, 118, 255)'),
        row=1, col=2
    )
    
    # Adicionar barras para CTR
    fig.add_trace(
        go.Bar(x=df['Plataforma'], y=df['CTR Médio (%)'], name='CTR', marker_color='rgb(50, 171, 96)'),
        row=1, col=3
    )
    
    fig.update_layout(
        title='Comparativo de Benchmarks por Plataforma',
        height=400,
        showlegend=False,
        hovermode='x unified'
    )
    
    fig.update_xaxes(tickangle=45)
    
    return fig

def criar_grafico_okr_radar(metas_okr):
    """Cria gráfico de radar para visualizar OKRs"""
    
    if not metas_okr:
        return None
    
    # Preparar dados
    categorias = []
    valores = []
    
    for fase, metas in list(metas_okr.items())[:6]:  # Limitar a 6 fases
        categorias.append(fase[:20])
        # Usar número de metas como proxy de complexidade
        valores.append(len(metas) * 20)
    
    if not categorias:
        return None
    
    # Criar gráfico de radar
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill='toself',
        name='Intensidade de OKRs',
        line_color='rgb(31, 119, 180)',
        fillcolor='rgba(31, 119, 180, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        title='Distribuição de OKRs por Fase',
        height=400,
        showlegend=False
    )
    
    return fig

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

st.title("📊 Planejador Tático de Mídias Pagas")
st.markdown("""
Este planejador cria um plano tático completo de mídias pagas, com autoavaliação de qualidade em cada etapa:

1. **Diagnóstico** → entendimento do negócio e objetivos
2. **Arquitetura** → definição dos canais por etapa do funil
3. **Estrutura** → fases do plano e alocação de budget
4. **Detalhamento** → táticas por fase com OKRs
5. **Cronograma** → execução mês a mês
6. **Recomendações** → próximos passos e otimizações

Cada seção é automaticamente avaliada e refinada para garantir especificidade, profundidade e aplicabilidade.
""")
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
if 'metas_iniciais' not in st.session_state:
    st.session_state.metas_iniciais = []
if 'avaliacoes' not in st.session_state:
    st.session_state.avaliacoes = {}

# Sidebar com progresso
with st.sidebar:
    st.header("📋 Etapas do Planejamento")
    
    etapas = {
        1: "1. Diagnóstico Inicial",
        2: "2. Arquitetura de Canais",
        3: "3. Estrutura do Plano",
        4: "4. Detalhamento Tático",
        5: "5. Cronograma",
        6: "6. Recomendações Executivas",
        7: "📄 Plano Completo"
    }
    
    for num, desc in etapas.items():
        if num < st.session_state.etapa_atual:
            st.success(f"✓ {desc}")
        elif num == st.session_state.etapa_atual:
            st.info(f"▶ {desc}")
        else:
            st.write(f"○ {desc}")
    
    st.markdown("---")
    if st.session_state.dados_coletados:
        st.markdown(f"**Cliente:** {st.session_state.dados_coletados.get('cliente', '')}")
        st.markdown(f"**Orçamento:** R$ {st.session_state.dados_coletados.get('orcamento', 0):,.2f}")
        st.markdown(f"**Área:** {st.session_state.dados_coletados.get('area_geografica', '')}")

# ETAPA 1: Diagnóstico Inicial (com metas e área geográfica)
if st.session_state.etapa_atual == 1:
    st.header("1. Diagnóstico Inicial")
    st.markdown("Preencha os dados para iniciar o planejamento.")
    
    with st.form("dados_cliente_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            cliente = st.text_input("Cliente *", placeholder="Ex: Loja de Roupas Sustentável")
            orcamento = st.number_input("Orçamento Total (R$) *", min_value=0.0, step=1000.0, format="%.2f")
            area_geografica = st.text_input("Área Geográfica de Atuação *", placeholder="Ex: Brasil, Sudeste, São Paulo, Região Metropolitana de SP...")
            
        with col2:
            canais = st.multiselect(
                "Canais de Interesse (opcional)",
                list(PLATAFORMA_OBJETIVOS.keys())
            )
        
        objetivos = st.text_area("Objetivos Principais *", height=100,
                                placeholder="Ex: Aumentar vendas em 30%, lançar novo produto, fortalecer marca...")
        
        contexto = st.text_area("Contexto do Negócio *", height=150,
                               placeholder="Momento da marca, concorrência, público-alvo, diferenciais, histórico...")
        
        st.markdown("*Campos obrigatórios")
        submitted = st.form_submit_button("🚀 Gerar Diagnóstico", use_container_width=True)
        
        if submitted:
            if cliente and orcamento and objetivos and contexto and area_geografica:
                with st.spinner("Gerando diagnóstico..."):
                    st.session_state.dados_coletados = {
                        'cliente': cliente,
                        'orcamento': orcamento,
                        'area_geografica': area_geografica,
                        'objetivos': objetivos,
                        'contexto': contexto,
                        'canais_preferencia': canais
                    }
                    
                    # Renderizar editor de metas após o diagnóstico
                    st.session_state.etapa_atual = 1.5
                    st.rerun()
            else:
                st.error("Preencha todos os campos obrigatórios (*)")

# ETAPA 1.5: Definição de Metas
elif st.session_state.etapa_atual == 1.5:
    st.header("1.5 Definição de Metas do Plano")
    st.markdown("Defina as metas globais que este plano deve alcançar.")
    
    metas = render_metas_iniciais_editor()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Salvar Metas e Continuar", use_container_width=True):
            st.session_state.metas_iniciais = metas
            with st.spinner("Gerando análise inicial com autoavaliação..."):
                # Usar o sistema de avaliação automática
                analise = gerar_com_avaliacao(
                    gerar_analise_inicial,
                    "analise_inicial",
                    cliente=st.session_state.dados_coletados['cliente'],
                    orcamento=st.session_state.dados_coletados['orcamento'],
                    objetivos=st.session_state.dados_coletados['objetivos'],
                    contexto=st.session_state.dados_coletados['contexto'],
                    canais_preferencia=", ".join(st.session_state.dados_coletados['canais_preferencia']) if st.session_state.dados_coletados['canais_preferencia'] else "A definir",
                    area_geografica=st.session_state.dados_coletados['area_geografica']
                )
                st.session_state.narrativa_gerada['analise_inicial'] = analise
                st.session_state.etapa_atual = 2
                st.rerun()
    
    with col2:
        if st.button("↩️ Voltar", use_container_width=True):
            st.session_state.etapa_atual = 1
            st.rerun()

# ETAPA 2: Análise Inicial
elif st.session_state.etapa_atual == 2:
    st.header("1. Diagnóstico Inicial (Resultado)")
    
    st.markdown(st.session_state.narrativa_gerada['analise_inicial'])
    
    # Mostrar avaliação (opcional)
    mostrar_avaliacao("analise_inicial")
    
    # Gráfico de benchmarks para contexto
    with st.expander("📊 Comparativo de Benchmarks por Plataforma", expanded=False):
        fig_bench = criar_grafico_comparativo_benchmarks()
        st.plotly_chart(fig_bench, use_container_width=True)
    
    render_refinamento_box(
        "análise inicial",
        'analise_inicial',
        gerar_analise_inicial,
        cliente=st.session_state.dados_coletados['cliente'],
        orcamento=st.session_state.dados_coletados['orcamento'],
        objetivos=st.session_state.dados_coletados['objetivos'],
        contexto=st.session_state.dados_coletados['contexto'],
        canais_preferencia=", ".join(st.session_state.dados_coletados['canais_preferencia']) if st.session_state.dados_coletados['canais_preferencia'] else "A definir",
        area_geografica=st.session_state.dados_coletados['area_geografica']
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Avançar para Arquitetura de Canais", use_container_width=True):
            with st.spinner("Gerando arquitetura de canais com autoavaliação..."):
                arquitetura = gerar_com_avaliacao(
                    recomendar_arquitetura_canais,
                    "arquitetura_canais",
                    analise_inicial=st.session_state.narrativa_gerada['analise_inicial'],
                    objetivos=st.session_state.dados_coletados['objetivos'],
                    orcamento=st.session_state.dados_coletados['orcamento'],
                    canais_preferencia=", ".join(st.session_state.dados_coletados['canais_preferencia']) if st.session_state.dados_coletados['canais_preferencia'] else "Definir",
                    area_geografica=st.session_state.dados_coletados['area_geografica']
                )
                st.session_state.narrativa_gerada['arquitetura_canais'] = arquitetura
                st.session_state.etapa_atual = 3
                st.rerun()
    
    with col2:
        if st.button("↩️ Voltar para Metas", use_container_width=True):
            st.session_state.etapa_atual = 1.5
            st.rerun()

# ETAPA 3: Arquitetura de Canais
elif st.session_state.etapa_atual == 3:
    st.header("2. Arquitetura de Canais")
    
    st.markdown(st.session_state.narrativa_gerada['arquitetura_canais'])
    
    # Mostrar avaliação
    mostrar_avaliacao("arquitetura_canais")
    
    # Gráfico de alocação de budget
    st.subheader("📊 Visualização da Alocação de Budget")
    col1, col2 = st.columns(2)
    
    with col1:
        fig_budget = criar_grafico_alocacao_budget(st.session_state.narrativa_gerada['arquitetura_canais'])
        st.plotly_chart(fig_budget, use_container_width=True)
    
    with col2:
        # Gráfico de projeção de métricas
        fig_projecao = criar_grafico_projecao_metricas(st.session_state.dados_coletados['orcamento'])
        st.plotly_chart(fig_projecao, use_container_width=True)
    
    render_refinamento_box(
        "arquitetura de canais",
        'arquitetura_canais',
        recomendar_arquitetura_canais,
        analise_inicial=st.session_state.narrativa_gerada['analise_inicial'],
        objetivos=st.session_state.dados_coletados['objetivos'],
        orcamento=st.session_state.dados_coletados['orcamento'],
        canais_preferencia=", ".join(st.session_state.dados_coletados['canais_preferencia']) if st.session_state.dados_coletados['canais_preferencia'] else "Definir",
        area_geografica=st.session_state.dados_coletados['area_geografica']
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Avançar para Estrutura do Plano", use_container_width=True):
            with st.spinner("Estruturando fases do plano com autoavaliação..."):
                estrutura = gerar_com_avaliacao(
                    definir_estrutura_plano,
                    "estrutura_plano",
                    arquitetura_canais=st.session_state.narrativa_gerada['arquitetura_canais'],
                    objetivos=st.session_state.dados_coletados['objetivos'],
                    cliente=st.session_state.dados_coletados['cliente'],
                    orcamento=st.session_state.dados_coletados['orcamento'],
                    area_geografica=st.session_state.dados_coletados['area_geografica'],
                    metas_iniciais=st.session_state.metas_iniciais
                )
                st.session_state.narrativa_gerada['estrutura_plano'] = estrutura
                st.session_state.etapa_atual = 4
                st.rerun()
    
    with col2:
        if st.button("↩️ Voltar", use_container_width=True):
            st.session_state.etapa_atual = 2
            st.rerun()

# ETAPA 4: Estrutura do Plano
elif st.session_state.etapa_atual == 4:
    st.header("3. Estrutura do Plano")
    
    st.markdown(st.session_state.narrativa_gerada['estrutura_plano'])
    
    # Mostrar avaliação
    mostrar_avaliacao("estrutura_plano")
    
    # Gráfico de alocação por etapa do funil
    st.subheader("📊 Distribuição de Budget por Etapa do Funil")
    fig_funil = criar_grafico_alocacao_funil(
        st.session_state.narrativa_gerada['arquitetura_canais'],
        st.session_state.narrativa_gerada['estrutura_plano']
    )
    st.plotly_chart(fig_funil, use_container_width=True)
    
    st.markdown("---")
    
    with st.form("estrutura_form"):
        estrutura_confirmada = st.text_area(
            "Estrutura definida (edite se necessário):",
            value=st.session_state.narrativa_gerada['estrutura_plano'],
            height=200
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submit_estrutura = st.form_submit_button("✅ Confirmar e Avançar", use_container_width=True)
        with col2:
            cancel_estrutura = st.form_submit_button("Cancelar", use_container_width=True)
        
        if submit_estrutura:
            if estrutura_confirmada != st.session_state.narrativa_gerada['estrutura_plano']:
                st.session_state.narrativa_gerada['estrutura_plano'] = estrutura_confirmada
            st.session_state.etapa_atual = 5
            st.rerun()
        
        if cancel_estrutura:
            st.rerun()
    
    render_refinamento_box(
        "estrutura do plano",
        'estrutura_plano',
        definir_estrutura_plano,
        arquitetura_canais=st.session_state.narrativa_gerada['arquitetura_canais'],
        objetivos=st.session_state.dados_coletados['objetivos'],
        cliente=st.session_state.dados_coletados['cliente'],
        orcamento=st.session_state.dados_coletados['orcamento'],
        area_geografica=st.session_state.dados_coletados['area_geografica'],
        metas_iniciais=st.session_state.metas_iniciais
    )

# ETAPA 5: Detalhamento Tático
elif st.session_state.etapa_atual == 5:
    st.header("4. Detalhamento Tático das Fases")
    
    # Se não tem fases geradas ainda, gerar
    if 'fases_detalhadas' not in st.session_state.narrativa_gerada:
        with st.spinner("Detalhando cada fase com autoavaliação..."):
            metas_okr = st.session_state.metas_okr if st.session_state.metas_okr else None
            
            fases = gerar_com_avaliacao(
                detalhar_fases,
                "fases_detalhadas",
                estrutura_plano=st.session_state.narrativa_gerada['estrutura_plano'],
                arquitetura_canais=st.session_state.narrativa_gerada['arquitetura_canais'],
                orcamento=st.session_state.dados_coletados['orcamento'],
                cliente=st.session_state.dados_coletados['cliente'],
                objetivos=st.session_state.dados_coletados['objetivos'],
                area_geografica=st.session_state.dados_coletados['area_geografica'],
                metas_okr=metas_okr
            )
            st.session_state.narrativa_gerada['fases_detalhadas'] = fases
    
    # Mostrar avaliação
    mostrar_avaliacao("fases_detalhadas")
    
    # Gráfico de radar de OKRs
    if st.session_state.metas_okr:
        with st.expander("📊 Visualização de OKRs por Fase", expanded=False):
            fig_radar = criar_grafico_okr_radar(st.session_state.metas_okr)
            if fig_radar:
                st.plotly_chart(fig_radar, use_container_width=True)
    
    # Editor de OKRs
    with st.expander("🎯 Definir Metas por Fase", expanded=not st.session_state.metas_okr):
        metas_okr = render_metas_okr_editor(st.session_state.narrativa_gerada['fases_detalhadas'])
        
        if metas_okr:
            if st.button("💾 Salvar Metas e Atualizar Fases", use_container_width=True):
                st.session_state.metas_okr = metas_okr
                with st.spinner("Atualizando fases com as metas definidas..."):
                    fases = detalhar_fases(
                        st.session_state.narrativa_gerada['estrutura_plano'],
                        st.session_state.narrativa_gerada['arquitetura_canais'],
                        st.session_state.dados_coletados['orcamento'],
                        st.session_state.dados_coletados['cliente'],
                        st.session_state.dados_coletados['objetivos'],
                        st.session_state.dados_coletados['area_geografica'],
                        metas_okr=metas_okr
                    )
                    st.session_state.narrativa_gerada['fases_detalhadas'] = fases
                    st.rerun()
    
    # Exibir conteúdo
    st.markdown(st.session_state.narrativa_gerada['fases_detalhadas'])
    
    render_refinamento_box(
        "detalhamento das fases",
        'fases_detalhadas',
        detalhar_fases,
        estrutura_plano=st.session_state.narrativa_gerada['estrutura_plano'],
        arquitetura_canais=st.session_state.narrativa_gerada['arquitetura_canais'],
        orcamento=st.session_state.dados_coletados['orcamento'],
        cliente=st.session_state.dados_coletados['cliente'],
        objetivos=st.session_state.dados_coletados['objetivos'],
        area_geografica=st.session_state.dados_coletados['area_geografica'],
        metas_okr=st.session_state.metas_okr
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Avançar para Cronograma", use_container_width=True):
            with st.spinner("Gerando cronograma de execução com autoavaliação..."):
                cronograma = gerar_com_avaliacao(
                    criar_cronograma,
                    "cronograma",
                    fases_detalhadas=st.session_state.narrativa_gerada['fases_detalhadas'],
                    cliente=st.session_state.dados_coletados['cliente'],
                    orcamento=st.session_state.dados_coletados['orcamento'],
                    area_geografica=st.session_state.dados_coletados['area_geografica']
                )
                st.session_state.narrativa_gerada['cronograma'] = cronograma
                st.session_state.etapa_atual = 6
                st.rerun()
    
    with col2:
        if st.button("↩️ Voltar", use_container_width=True):
            st.session_state.etapa_atual = 4
            st.rerun()

# ETAPA 6: Cronograma
elif st.session_state.etapa_atual == 6:
    st.header("5. Cronograma de Execução")
    
    st.markdown(st.session_state.narrativa_gerada['cronograma'])
    
    # Mostrar avaliação
    mostrar_avaliacao("cronograma")
    
    # Gráfico de Gantt do cronograma
    st.subheader("📊 Linha do Tempo das Fases")
    fig_gantt = criar_grafico_cronograma(
        st.session_state.narrativa_gerada['fases_detalhadas'],
        st.session_state.dados_coletados['orcamento']
    )
    st.plotly_chart(fig_gantt, use_container_width=True)
    
    render_refinamento_box(
        "cronograma",
        'cronograma',
        criar_cronograma,
        fases_detalhadas=st.session_state.narrativa_gerada['fases_detalhadas'],
        cliente=st.session_state.dados_coletados['cliente'],
        orcamento=st.session_state.dados_coletados['orcamento'],
        area_geografica=st.session_state.dados_coletados['area_geografica']
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Avançar para Recomendações", use_container_width=True):
            # Compilar plano completo
            plano_completo = f"""
# PLANO TÁTICO DE MÍDIAS PAGAS - {st.session_state.dados_coletados['cliente'].upper()}

**Área Geográfica:** {st.session_state.dados_coletados['area_geografica']}
**Orçamento Total:** R$ {st.session_state.dados_coletados['orcamento']:,.2f}
**Data de Geração:** {datetime.now().strftime('%d/%m/%Y')}

---

## 1. DIAGNÓSTICO INICIAL
{st.session_state.narrativa_gerada['analise_inicial']}

---

## 2. ARQUITETURA DE CANAIS
{st.session_state.narrativa_gerada['arquitetura_canais']}

---

## 3. ESTRUTURA DO PLANO
{st.session_state.narrativa_gerada['estrutura_plano']}

---

## 4. DETALHAMENTO TÁTICO DAS FASES
{st.session_state.narrativa_gerada['fases_detalhadas']}

---

## 5. CRONOGRAMA DE EXECUÇÃO
{st.session_state.narrativa_gerada['cronograma']}

---

*Plano gerado em {datetime.now().strftime('%d/%m/%Y')} para {st.session_state.dados_coletados['cliente']}*
"""
            
            with st.spinner("Gerando recomendações executivas com autoavaliação..."):
                recomendacoes = gerar_com_avaliacao(
                    gerar_recomendacoes_executivas,
                    "recomendacoes",
                    plano_completo=plano_completo,
                    cliente=st.session_state.dados_coletados['cliente'],
                    objetivos=st.session_state.dados_coletados['objetivos'],
                    area_geografica=st.session_state.dados_coletados['area_geografica']
                )
                st.session_state.narrativa_gerada['recomendacoes'] = recomendacoes
                st.session_state.plano_final = plano_completo + "\n\n" + recomendacoes
                st.session_state.etapa_atual = 7
                st.rerun()
    
    with col2:
        if st.button("↩️ Voltar", use_container_width=True):
            st.session_state.etapa_atual = 5
            st.rerun()

# ETAPA 7: Plano Final
elif st.session_state.etapa_atual == 7:
    st.header("6. Recomendações Executivas")
    st.markdown("**Plano tático completo gerado com sucesso.**")
    
    # Mostrar recomendações
    st.markdown(st.session_state.narrativa_gerada['recomendacoes'])
    
    # Mostrar avaliação das recomendações
    mostrar_avaliacao("recomendacoes")
    
    st.markdown("---")
    
    # Dashboard de gráficos do plano
    st.subheader("📊 Dashboard do Plano")
    
    tab1, tab2, tab3 = st.tabs(["Alocação de Budget", "Cronograma", "Projeções"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            fig_budget = criar_grafico_alocacao_budget(st.session_state.narrativa_gerada['arquitetura_canais'])
            st.plotly_chart(fig_budget, use_container_width=True)
        with col2:
            fig_funil = criar_grafico_alocacao_funil(
                st.session_state.narrativa_gerada['arquitetura_canais'],
                st.session_state.narrativa_gerada['estrutura_plano']
            )
            st.plotly_chart(fig_funil, use_container_width=True)
    
    with tab2:
        fig_gantt = criar_grafico_cronograma(
            st.session_state.narrativa_gerada['fases_detalhadas'],
            st.session_state.dados_coletados['orcamento']
        )
        st.plotly_chart(fig_gantt, use_container_width=True)
    
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            fig_projecao = criar_grafico_projecao_metricas(st.session_state.dados_coletados['orcamento'])
            st.plotly_chart(fig_projecao, use_container_width=True)
        with col2:
            if st.session_state.metas_okr:
                fig_radar = criar_grafico_okr_radar(st.session_state.metas_okr)
                if fig_radar:
                    st.plotly_chart(fig_radar, use_container_width=True)
    
    with st.expander("📄 Ver Plano Completo", expanded=False):
        st.markdown(st.session_state.plano_final)
    
    # Download
    st.download_button(
        label="📥 Baixar Plano Completo (Markdown)",
        data=st.session_state.plano_final,
        file_name=f"plano_midias_{st.session_state.dados_coletados['cliente'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown",
        use_container_width=True
    )
    
    st.markdown("---")
    
    # Opção de refinamento final
    with st.expander("✏️ Refinar Plano Completo"):
        with st.form("refinamento_final_form"):
            refinamento_final = st.text_area(
                "Instruções para ajustes finais:",
                height=100,
                placeholder="Descreva os ajustes desejados em todo o plano..."
            )
            
            col1, col2 = st.columns(2)
            with col1:
                submit_refinamento = st.form_submit_button("🔄 Aplicar Ajustes Finais", use_container_width=True)
            with col2:
                cancel_refinamento = st.form_submit_button("Cancelar", use_container_width=True)
            
            if submit_refinamento and refinamento_final:
                with st.spinner("Aplicando ajustes finais em todas as seções..."):
                    # Regenerar cada seção
                    analise = gerar_analise_inicial(
                        st.session_state.dados_coletados['cliente'],
                        st.session_state.dados_coletados['orcamento'],
                        st.session_state.dados_coletados['objetivos'],
                        st.session_state.dados_coletados['contexto'],
                        ", ".join(st.session_state.dados_coletados['canais_preferencia']) if st.session_state.dados_coletados['canais_preferencia'] else "A definir",
                        st.session_state.dados_coletados['area_geografica'],
                        instrucoes_refinamento=refinamento_final,
                        versao_anterior=st.session_state.narrativa_gerada['analise_inicial']
                    )
                    st.session_state.narrativa_gerada['analise_inicial'] = analise
                    
                    arquitetura = recomendar_arquitetura_canais(
                        analise,
                        st.session_state.dados_coletados['objetivos'],
                        st.session_state.dados_coletados['orcamento'],
                        ", ".join(st.session_state.dados_coletados['canais_preferencia']) if st.session_state.dados_coletados['canais_preferencia'] else "Definir",
                        st.session_state.dados_coletados['area_geografica'],
                        instrucoes_refinamento=refinamento_final,
                        versao_anterior=st.session_state.narrativa_gerada['arquitetura_canais']
                    )
                    st.session_state.narrativa_gerada['arquitetura_canais'] = arquitetura
                    
                    estrutura = definir_estrutura_plano(
                        arquitetura,
                        st.session_state.dados_coletados['objetivos'],
                        st.session_state.dados_coletados['cliente'],
                        st.session_state.dados_coletados['orcamento'],
                        st.session_state.dados_coletados['area_geografica'],
                        metas_iniciais=st.session_state.metas_iniciais,
                        instrucoes_refinamento=refinamento_final,
                        versao_anterior=st.session_state.narrativa_gerada['estrutura_plano']
                    )
                    st.session_state.narrativa_gerada['estrutura_plano'] = estrutura
                    
                    fases = detalhar_fases(
                        estrutura,
                        arquitetura,
                        st.session_state.dados_coletados['orcamento'],
                        st.session_state.dados_coletados['cliente'],
                        st.session_state.dados_coletados['objetivos'],
                        st.session_state.dados_coletados['area_geografica'],
                        metas_okr=st.session_state.metas_okr,
                        instrucoes_refinamento=refinamento_final,
                        versao_anterior=st.session_state.narrativa_gerada['fases_detalhadas']
                    )
                    st.session_state.narrativa_gerada['fases_detalhadas'] = fases
                    
                    cronograma = criar_cronograma(
                        fases,
                        st.session_state.dados_coletados['cliente'],
                        st.session_state.dados_coletados['orcamento'],
                        st.session_state.dados_coletados['area_geografica'],
                        instrucoes_refinamento=refinamento_final,
                        versao_anterior=st.session_state.narrativa_gerada['cronograma']
                    )
                    st.session_state.narrativa_gerada['cronograma'] = cronograma
                    
                    plano_completo = f"""
# PLANO TÁTICO DE MÍDIAS PAGAS - {st.session_state.dados_coletados['cliente'].upper()}

**Área Geográfica:** {st.session_state.dados_coletados['area_geografica']}
**Orçamento Total:** R$ {st.session_state.dados_coletados['orcamento']:,.2f}
**Data de Geração:** {datetime.now().strftime('%d/%m/%Y')}

---

## 1. DIAGNÓSTICO INICIAL
{analise}

---

## 2. ARQUITETURA DE CANAIS
{arquitetura}

---

## 3. ESTRUTURA DO PLANO
{estrutura}

---

## 4. DETALHAMENTO TÁTICO DAS FASES
{fases}

---

## 5. CRONOGRAMA DE EXECUÇÃO
{cronograma}

---

*Plano gerado em {datetime.now().strftime('%d/%m/%Y')} para {st.session_state.dados_coletados['cliente']}*
"""
                    
                    recomendacoes = gerar_recomendacoes_executivas(
                        plano_completo,
                        st.session_state.dados_coletados['cliente'],
                        st.session_state.dados_coletados['objetivos'],
                        st.session_state.dados_coletados['area_geografica'],
                        instrucoes_refinamento=refinamento_final,
                        versao_anterior=st.session_state.narrativa_gerada['recomendacoes']
                    )
                    st.session_state.narrativa_gerada['recomendacoes'] = recomendacoes
                    st.session_state.plano_final = plano_completo + "\n\n" + recomendacoes
                    
                    st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Novo Planejamento", use_container_width=True):
            for key in ['etapa_atual', 'dados_coletados', 'narrativa_gerada', 'plano_final', 'metas_okr', 'metas_iniciais', 'avaliacoes']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        if st.button("↩️ Voltar para Cronograma", use_container_width=True):
            st.session_state.etapa_atual = 6
            st.rerun()

# Rodapé
st.markdown("---")
st.markdown("""
*Planejador Tático de Mídias Pagas com Autoavaliação - Baseado em dados do mercado brasileiro e frameworks acadêmicos.*
""")
