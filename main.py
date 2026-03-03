import streamlit as st
import google.generativeai as genai
import os
from datetime import datetime
import json
import time
import re

# Configuração inicial
st.set_page_config(
    layout="wide",
    page_title="Planejador Estratégico de Mídias - IA Narrativa",
    page_icon="📖"
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
                "descricao": "O Alcance representa o número de pessoas únicas expostas ao anúncio."
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
                "descricao": "Custo por mil impressões - métrica de eficiência."
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
                "descricao": "Taxa de cliques - indica relevância."
            },
            {
                "nome": "Cliques",
                "formula": "Total de cliques",
                "faixa_tipica": "Depende de CTR",
                "quando_usar": "Volume de interesse",
                "descricao": "Total de interações ativas."
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
                "descricao": "CTR mais alto indica consideração."
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
                "nome": "ThruPlay",
                "formula": "Vídeos assistidos 15s+",
                "faixa_tipica": "20-50%",
                "quando_usar": "Conteúdo demonstrativo",
                "descricao": "Visualização de demos e depoimentos."
            },
            {
                "nome": "Páginas por Sessão",
                "formula": "Pageviews / Sessões",
                "faixa_tipica": "1.5-3.0",
                "quando_usar": "Exploração do site",
                "descricao": "Profundidade de navegação."
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
    "Twitter": [
        "Reconhecimento de Marca", "Alcance", "Engajamento", "Tráfego",
    ],
    "Pinterest": [
        "Reconhecimento de Marca", "Tráfego", "Vendas de Catálogo",
        "Engajamento",
    ],
}

BENCHMARKS_BR = {
    "Meta Ads (Facebook/Instagram)": {
        "CPM": {"min": 8.0, "max": 25.0, "medio": 15.0, "unidade": "R$"},
        "CPC": {"min": 0.30, "max": 3.00, "medio": 1.20, "unidade": "R$"},
        "CTR": {"min": 0.8, "max": 2.5, "medio": 1.5, "unidade": "%"},
        "CPA": {"min": 15.0, "max": 120.0, "medio": 55.0, "unidade": "R$"},
        "ROAS": {"min": 2.0, "max": 6.0, "medio": 3.5, "unidade": "x"},
        "CPL": {"min": 5.0, "max": 50.0, "medio": 20.0, "unidade": "R$"},
    },
    "Google Ads": {
        "CPM": {"min": 5.0, "max": 35.0, "medio": 18.0, "unidade": "R$"},
        "CPC": {"min": 1.00, "max": 8.00, "medio": 3.50, "unidade": "R$"},
        "CTR": {"min": 2.0, "max": 8.0, "medio": 4.5, "unidade": "%"},
        "CPA": {"min": 25.0, "max": 200.0, "medio": 80.0, "unidade": "R$"},
        "ROAS": {"min": 2.0, "max": 8.0, "medio": 4.0, "unidade": "x"},
        "CPL": {"min": 10.0, "max": 80.0, "medio": 35.0, "unidade": "R$"},
    },
    "TikTok": {
        "CPM": {"min": 5.0, "max": 20.0, "medio": 10.0, "unidade": "R$"},
        "CPC": {"min": 0.20, "max": 2.00, "medio": 0.80, "unidade": "R$"},
        "CTR": {"min": 0.5, "max": 2.0, "medio": 1.2, "unidade": "%"},
        "CPA": {"min": 10.0, "max": 80.0, "medio": 35.0, "unidade": "R$"},
        "ROAS": {"min": 1.5, "max": 5.0, "medio": 3.0, "unidade": "x"},
        "CPL": {"min": 3.0, "max": 30.0, "medio": 12.0, "unidade": "R$"},
    },
    "LinkedIn": {
        "CPM": {"min": 30.0, "max": 80.0, "medio": 50.0, "unidade": "R$"},
        "CPC": {"min": 5.00, "max": 25.00, "medio": 12.00, "unidade": "R$"},
        "CTR": {"min": 0.3, "max": 1.0, "medio": 0.6, "unidade": "%"},
        "CPA": {"min": 50.0, "max": 500.0, "medio": 180.0, "unidade": "R$"},
        "CPL": {"min": 30.0, "max": 200.0, "medio": 80.0, "unidade": "R$"},
    },
    "YouTube": {
        "CPM": {"min": 10.0, "max": 30.0, "medio": 18.0, "unidade": "R$"},
        "CPV": {"min": 0.02, "max": 0.15, "medio": 0.06, "unidade": "R$"},
        "VTR": {"min": 15.0, "max": 40.0, "medio": 25.0, "unidade": "%"},
        "CTR": {"min": 0.3, "max": 1.5, "medio": 0.7, "unidade": "%"},
    },
    "Mídia Programática": {
        "CPM": {"min": 3.0, "max": 20.0, "medio": 10.0, "unidade": "R$"},
        "CPC": {"min": 0.50, "max": 5.00, "medio": 2.00, "unidade": "R$"},
        "CTR": {"min": 0.1, "max": 0.5, "medio": 0.25, "unidade": "%"},
        "CPA": {"min": 20.0, "max": 150.0, "medio": 60.0, "unidade": "R$"},
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

THEORETICAL_FRAMEWORKS = {
    "summary": "Diversos frameworks acadêmicos descrevem a jornada do consumidor.",
    "frameworks": {
        "AIDA": {
            "author": "E. St. Elmo Lewis (1898)",
            "stages": ["Attention", "Interest", "Desire", "Action"],
            "key_insight": "Modelo de funil linear mais antigo."
        },
        "STDC": {
            "author": "Avinash Kaushik (2013)",
            "stages": ["See", "Think", "Do", "Care"],
            "key_insight": "Cada etapa tem métricas diferentes."
        },
        "McKinsey CDJ": {
            "author": "McKinsey (2009)",
            "stages": ["Consideração Inicial", "Avaliação Ativa", "Compra", "Pós-Compra", "Loop"],
            "key_insight": "Touchpoints na avaliação ativa são 2-3x mais influentes."
        },
        "Binet_and_Field": {
            "author": "Les Binet & Peter Field",
            "key_insight": "Regra 60/40: 60% construção de marca, 40% ativação."
        },
        "Byron_Sharp": {
            "author": "Byron Sharp",
            "key_insight": "Crescimento vem de novos compradores, não fidelização."
        }
    }
}

def get_enriched_funnel_context(etapa):
    """Contexto enriquecido para cada etapa"""
    contexts = {
        "Consciência (Awareness)": "Foco em alcance e construção de marca. Métricas: Alcance, Impressões, CPM.",
        "Interesse": "Gerar engajamento e curiosidade. Métricas: CTR, Cliques, CPC.",
        "Consideração": "Aprofundar avaliação. Métricas: CTR qualificado, Micro-conversões.",
        "Intenção": "Capturar leads qualificados. Métricas: Leads, CPL.",
        "Conversão/Ação": "Fechar vendas. Métricas: Conversões, CPA, ROAS.",
        "Retenção/Fidelização": "Manter clientes. Métricas: LTV, Taxa de recompra."
    }
    return contexts.get(etapa, "")

# ============================================================================
# FUNÇÕES DE GERAÇÃO COM NARRATIVA EXPLÍCITA
# ============================================================================

def gerar_insights_iniciais(cliente, orcamento, objetivos, contexto, canais_preferencia, 
                           instrucoes_refinamento=None, versao_anterior=None):
    """Ato 1: O Encontro - Conhecendo o cliente e seu mundo"""
    
    prompt_intro = """
Você é um Estrategista de Mídias Sênior e um Contador de Histórias. 
Sua missão é construir um plano de mídia que seja uma JORNADA NARRATIVA, 
onde cada elemento se conecta ao próximo como em uma grande história.

A história que você vai contar tem 6 atos:
Ato 1 - O Encontro: Conhecendo o cliente e seu mundo (insights iniciais)
Ato 2 - A Descoberta: Revelando os caminhos possíveis (arquitetura de canais)
Ato 3 - A Estrutura: Definindo os capítulos da jornada (estrutura narrativa)
Ato 4 - Os Capítulos: Detalhando cada fase da história (detalhamento das fases)
Ato 5 - A Linha do Tempo: Quando cada capítulo acontece (cronograma)
Ato 6 - O Desfecho: Recomendações finais e próximos passos

Hoje começamos o **ATO 1 - O ENCONTRO**. 
"""
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
{prompt_intro}

Você já havia escrito uma versão do Ato 1 para {cliente}, mas o cliente pediu ajustes.
MANTENHA a narrativa existente, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR DO ATO 1:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO:**
{instrucoes_refinamento}

**INFORMAÇÕES DO CLIENTE:**
- Cliente: {cliente}
- Orçamento: R$ {orcamento:,.2f}
- Objetivos: {objetivos}
- Contexto: {contexto}
- Canais de Interesse: {canais_preferencia}

Retorne a versão COMPLETA do Ato 1, aplicando apenas os refinamentos solicitados.
Mantenha o tom narrativo e a estrutura de "história".
"""
    else:
        prompt = f"""
{prompt_intro}

**INFORMAÇÕES DO CLIENTE:**
- Cliente: {cliente}
- Orçamento Total: R$ {orcamento:,.2f}
- Objetivos Principais: {objetivos}
- Contexto/Desafios: {contexto}
- Canais de Interesse: {canais_preferencia if canais_preferencia else "A definir"}

**BASE DE CONHECIMENTO ESTRATÉGICO (use estes conceitos na narrativa):**

**Frameworks Teóricos (como parte da história):**
- **Binet & Field**: A grande dicotomia - construir marca (60%) vs ativar vendas (40%)
- **Byron Sharp**: O herói precisa conquistar novos territórios (novos compradores)
- **McKinsey CDJ**: A jornada não é linear - há loops de fidelidade
- **STDC**: A audiência tem diferentes papéis na história

**Benchmarks Brasil (o cenário da nossa história):**
- Meta Ads: CPM R$8-25 (70% abaixo do mundo - nossa vantagem)
- WhatsApp: 93,7% de penetração - o aliado secreto
- Instagram: 92% dos brasileiros - nosso palco principal

Agora, escreva o **ATO 1 - O ENCONTRO** em formato narrativo, como se fosse o primeiro capítulo de um livro.

Estruture sua narrativa com:

## 📖 ATO 1: O ENCONTRO - Conhecendo {cliente}

### 1.1 Quem é nosso protagonista?
[Descreva o cliente, seu negócio, seus desafios e sonhos - como se estivesse apresentando um personagem]

### 1.2 O cenário onde nossa história se passa
[Analise o mercado, a concorrência, as oportunidades - o "mundo" onde o protagonista vive]

### 1.3 O que nosso herói deseja alcançar?
[Os objetivos do cliente, traduzidos em desejos narrativos - o que ele quer conquistar]

### 1.4 Os recursos disponíveis para esta jornada
[O que R$ {orcamento:,.2f} significa no contexto brasileiro - quanto território podemos conquistar]

### 1.5 Primeiras pistas do caminho
[Insights iniciais sobre a estratégia - para onde a história pode ir]

### 1.6 As perguntas que ainda precisamos responder
[Mistérios a serem desvendados nos próximos atos]

Use uma linguagem envolvente, como se estivesse contando uma história para o cliente.
Evite linguagem puramente técnica - cada conceito deve ser explicado como parte da narrativa.
"""
    response = modelo.generate_content(prompt)
    return response.text


def recomendar_arquitetura_canais(insights_iniciais, objetivos, orcamento, canais_preferencia,
                                  instrucoes_refinamento=None, versao_anterior=None):
    """Ato 2: A Descoberta - Revelando os caminhos possíveis"""
    
    prompt_intro = """
Continuamos nossa jornada narrativa. No Ato 1, conhecemos nosso protagonista e seu mundo.
Agora, no **ATO 2 - A DESCOBERTA**, vamos revelar os caminhos que nosso herói pode seguir.

Como em toda boa história, o protagonista precisa escolher quais ferramentas e aliados levará em sua jornada.
Os canais de mídia são esses aliados - cada um com seus poderes e limitações.
"""
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
{prompt_intro}

Você já havia escrito uma versão do Ato 2, mas o cliente pediu ajustes.
MANTENHA a narrativa existente, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR DO ATO 2:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO:**
{instrucoes_refinamento}

**CONTEXTO:**
- Objetivos: {objetivos}
- Orçamento: R$ {orcamento:,.2f}

Retorne a versão COMPLETA do Ato 2, aplicando apenas os refinamentos solicitados.
"""
    else:
        prompt = f"""
{prompt_intro}

**A HISTÓRIA ATÉ AGORA (resumo do Ato 1):**
{insights_iniciais[:500]}...

**Objetivos do protagonista:** {objetivos}
**Recursos disponíveis:** R$ {orcamento:,.2f}
**Canais considerados:** {canais_preferencia if canais_preferencia else "A definir"}

**OS ALIADOS DISPONÍVEIS (e seus poderes):**

- **YouTube**: O contador de histórias - 75% das pessoas descobrem novas marcas aqui
- **Meta (Instagram/Facebook)**: O anfitrião da festa - 92% dos brasileiros estão aqui
- **TikTok**: O jovem criativo - 91,7 milhões de brasileiros
- **Google Ads**: O bibliotecário - conecta quem busca com respostas
- **LinkedIn**: O executivo - ideal para histórias B2B
- **WhatsApp**: O confidente - 93,7% de penetração, 55% de conversão
- **Programática**: O megafone - alcance massivo em milhares de lugares

**A SABEDORIA DOS ANTIGOS (frameworks):**

Para cada etapa da jornada do herói, diferentes aliados são mais úteis:

| Etapa da Jornada | Aliados mais poderosos | O que eles fazem |
|-----------------|----------------------|------------------|
| Consciência | YouTube, TikTok, Meta, Programática | Apresentam o herói ao mundo |
| Interesse | Meta, TikTok, Google Discovery | Despertam curiosidade |
| Consideração | Google Search, YouTube, LinkedIn | Ajudam na avaliação |
| Intenção | Google Search, Meta Lead Ads, WhatsApp | Capturam leads |
| Conversão | Google Shopping, Meta Dynamic Ads | Fecham o negócio |
| Retenção | Email, WhatsApp, Custom Audiences | Mantêm o relacionamento |

Agora, escreva o **ATO 2 - A DESCOBERTA** em formato narrativo.

Estruture sua narrativa com:

## 📖 ATO 2: A DESCOBERTA - Os Caminhos do Herói

### 2.1 Os aliados que nosso protagonista pode escolher
[Apresente cada canal recomendado como um personagem - por que este aliado? qual seu superpoder?]

### 2.2 O papel de cada aliado na jornada
[Explique como cada canal contribui em diferentes momentos da história]

### 2.3 Como distribuir nossos recursos entre os aliados
[Apresente a alocação de budget como uma "estratégia de batalha" - quanto investir em cada frente]

### 2.4 A sinergia entre os aliados
[Como eles trabalham juntos - o YouTube apresenta, o Meta reengaja, o Google captura, o WhatsApp converte]

### 2.5 Por que esta é a melhor aliança para nossa história
[A justificativa estratégica, conectando aos objetivos do Ato 1]

Use metáforas e storytelling. Cada recomendação deve parecer uma escolha natural na jornada do herói.
"""
    response = modelo.generate_content(prompt)
    return response.text


def definir_estrutura_narrativa(arquitetura_canais, objetivos, cliente, orcamento,
                                instrucoes_refinamento=None, versao_anterior=None):
    """Ato 3: A Estrutura - Definindo os capítulos da jornada"""
    
    prompt_intro = """
Chegamos ao **ATO 3 - A ESTRUTURA**. Agora que conhecemos nosso protagonista (Ato 1) 
e escolhemos nossos aliados (Ato 2), precisamos definir os capítulos desta grande história.

Como em todo bom livro, filme ou série, nossa campanha terá começo, meio e fim - 
mas não necessariamente nessa ordem. Às vezes o herói precisa revisitar lugares, 
aprender lições, e construir relacionamentos ao longo do tempo.
"""
    
    # Construir templates de alocação
    templates_texto = ""
    for nome, template in TEMPLATES_ALOCACAO_BUDGET.items():
        distribuicao = ", ".join([f"{etapa}: {pct}%" for etapa, pct in template["distribuicao"].items() if pct > 0])
        templates_texto += f"\n- **{nome}**: {template['descricao']} | {distribuicao}"
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
{prompt_intro}

Você já havia escrito uma versão do Ato 3, mas o cliente pediu ajustes.
MANTENHA a narrativa existente, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO:**
{instrucoes_refinamento}

Retorne a versão COMPLETA do Ato 3, aplicando apenas os refinamentos.
"""
    else:
        prompt = f"""
{prompt_intro}

**A HISTÓRIA ATÉ AGORA:**
- Nosso protagonista: {cliente}
- Seu objetivo: {objetivos}
- Seus aliados: {arquitetura_canais[:300]}...
- Recursos: R$ {orcamento:,.2f}

**TEMPLATES DE ALOCAÇÃO (referência para distribuição de recursos):**
{templates_texto}

**ARQUÉTIPOS DE JORNADA (possíveis estruturas narrativas):**

**Opção 1 - A JORNADA DO HERÓI (Lançamento → Construção → Consolidação)**
- Ato 3.1 - O Chamado: Apresentamos o herói ao mundo (Consciência)
- Ato 3.2 - A Travessia: Conquistamos aliados e superamos desafios (Interesse + Consideração)
- Ato 3.3 - O Retorno: Colhemos os frutos da jornada (Conversão + Retenção)

**Opção 2 - A JORNADA DO RELACIONAMENTO (Atração → Conversão → Fidelização)**
- Ato 3.1 - O Primeiro Encontro: Atraímos a audiência (Consciência + Interesse)
- Ato 3.2 - O Compromisso: Convertemos em clientes (Consideração + Intenção + Conversão)
- Ato 3.3 - O Casamento: Fidelizamos para sempre (Retenção)

**Opção 3 - A JORNADA SAZONAL (Antes → Durante → Depois)**
- Ato 3.1 - A Preparação: Construímos expectativa (Consciência)
- Ato 3.2 - A Batalha: Ativamos no momento crítico (Todas as etapas aceleradas)
- Ato 3.3 - A Cura: Cuidamos dos sobreviventes (Retenção)

**Opção 4 - A JORNADA CONTÍNUA (Always-on)**
- Um ciclo infinito onde todas as etapas acontecem simultaneamente

Agora, escreva o **ATO 3 - A ESTRUTURA** em formato narrativo.

Para cada opção de estrutura, conte uma mini-história:
- Qual é a metáfora por trás desta jornada?
- O que acontece em cada capítulo?
- Quanto tempo dura cada capítulo?
- O que medimos em cada capítulo?

Por fim, RECOMENDE a melhor estrutura para nosso protagonista, justificando por que esta história faz sentido para {cliente}.

Use a estrutura:

## 📖 ATO 3: A ESTRUTURA - Os Capítulos da Nossa História

### 3.1 As possíveis jornadas que nosso herói pode seguir
[Apresente cada opção como uma história diferente]

### 3.2 A jornada recomendada para {cliente}
[Explique por que esta estrutura foi escolhida]

### 3.3 Visão geral dos capítulos
[Uma prévia do que vem nos próximos atos]
"""
    response = modelo.generate_content(prompt)
    return response.text


def detalhar_fases(estrutura_escolhida, arquitetura_canais, orcamento, cliente, objetivos,
                   metas_okr=None, instrucoes_refinamento=None, versao_anterior=None):
    """Ato 4: Os Capítulos - Detalhando cada fase da história"""
    
    metas_texto = ""
    if metas_okr:
        metas_texto = "\n**METAS DEFINIDAS PELO PROTAGONISTA:**\n"
        for fase, metas in metas_okr.items():
            metas_texto += f"\n**{fase}:**\n"
            for meta in metas:
                metas_texto += f"- {meta}\n"
    
    prompt_intro = """
Chegamos ao coração da nossa narrativa: o **ATO 4 - OS CAPÍTULOS**.

Agora vamos detalhar cada capítulo da jornada que escolhemos no Ato 3.
Cada capítulo tem seu próprio tom, seus próprios desafios, suas próprias métricas de sucesso.
É aqui que a história ganha vida em detalhes.
"""
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
{prompt_intro}

Você já havia escrito os capítulos, mas o cliente pediu ajustes.
MANTENHA a narrativa existente, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR DOS CAPÍTULOS:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO:**
{instrucoes_refinamento}

{metas_texto}

Retorne a versão COMPLETA dos capítulos, aplicando apenas os refinamentos solicitados.
"""
    else:
        prompt = f"""
{prompt_intro}

**A HISTÓRIA ATÉ AGORA:**
- Protagonista: {cliente}
- Objetivo: {objetivos}
- Aliados: {arquitetura_canais[:200]}...
- Estrutura escolhida: {estrutura_escolhida[:300]}...
- Recursos totais: R$ {orcamento:,.2f}

{metas_texto}

**GUIA PARA ESCREVER CADA CAPÍTULO:**

Cada capítulo deve contar uma mini-história completa, com:

- **📖 NARRATIVA DO CAPÍTULO**: O que acontece neste capítulo? Qual o tom? (ex: "O capítulo da descoberta")

- **🎯 O QUE NOSSO HERÓI QUER AQUI**: Os objetivos específicos desta fase da jornada

- **📊 COMO MEDIMOS O SUCESSO**: As métricas que mostram se estamos no caminho certo (incluindo as metas definidas)

- **⚠️ O QUE NÃO DEVEMOS MEDIR**: Armadilhas comuns - métricas que parecem importantes mas enganam

- **💰 QUANTO VAMOS INVESTIR**: A parcela do tesouro dedicada a este capítulo

- **🎨 AS FERRAMENTAS CRIATIVAS**: Que tipo de conteúdo vamos criar? (vídeos, posts, anúncios...)

- **📱 COMO NOSSOS ALIADOS ATUAM**: Cada plataforma tem um papel específico neste capítulo

- **🎯 QUEM ENCONTRAMOS AQUI**: O público específico deste momento da jornada

- **🤝 COMO CUIDAMOS DOS RELACIONAMENTOS**: Ações de CRM e nutrição

- **⏱️ QUANTO TEMPO DURA ESTE CAPÍTULO**: Duração e marcos importantes

- **🔄 COMO ISTO CONECTA AO PRÓXIMO CAPÍTULO**: A transição na narrativa

Agora, escreva o **ATO 4 - OS CAPÍTULOS**, detalhando CADA FASE da estrutura escolhida.

Use o formato:

## 📖 ATO 4: OS CAPÍTULOS - A Jornada em Detalhe

### Capítulo 1: [NOME DO PRIMEIRO CAPÍTULO]

[Todo o detalhamento deste capítulo, seguindo o guia acima]

### Capítulo 2: [NOME DO SEGUNDO CAPÍTULO]

[Todo o detalhamento...]

[Continue para todos os capítulos]

Mantenha o tom narrativo. Cada capítulo deve parecer parte de uma história maior.
"""
    response = modelo.generate_content(prompt)
    return response.text


def criar_cronograma_narrativo(fases_detalhadas, cliente, orcamento,
                              instrucoes_refinamento=None, versao_anterior=None):
    """Ato 5: A Linha do Tempo - Quando cada capítulo acontece"""
    
    prompt_intro = """
A história está quase completa. Temos nosso protagonista (Ato 1), nossos aliados (Ato 2),
nossa estrutura (Ato 3), e nossos capítulos detalhados (Ato 4).

Agora, no **ATO 5 - A LINHA DO TEMPO**, vamos organizar tudo no calendário.
Quando cada capítulo começa? Quanto tempo dura? O que acontece em cada semana?
É aqui que a história ganha seu ritmo.
"""
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
{prompt_intro}

Você já havia escrito uma versão da linha do tempo, mas o cliente pediu ajustes.
MANTENHA a narrativa existente, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO:**
{instrucoes_refinamento}

Retorne a versão COMPLETA da linha do tempo, aplicando apenas os refinamentos.
"""
    else:
        prompt = f"""
{prompt_intro}

**A HISTÓRIA ATÉ AGORA:**
- Cliente: {cliente}
- Orçamento: R$ {orcamento:,.2f}
- Capítulos: {fases_detalhadas[:500]}...

Crie uma **LINHA DO TEMPO NARRATIVA** que conte a história mês a mês.

Estruture como:

## 📖 ATO 5: A LINHA DO TEMPO - O Ritmo da Nossa História

### 5.1 A visão geral da jornada no tempo
[Um parágrafo contando como os capítulos se distribuem no calendário]

### 5.2 Mês a mês: a história se desenrolando

**Mês 1 - [TÍTULO DO MÊS]**
- O que acontece: [descrição das ações]
- Por que agora: [justificativa narrativa para o timing]
- Quem está atuando: [canais principais]
- O que criamos: [conteúdo principal]
- Como medimos: [métrica-chave desta semana]
- Como conecta ao próximo mês: [transição]

**Mês 2 - [TÍTULO DO MÊS]**
[mesma estrutura...]

[Continue para todos os meses]

### 5.3 Os marcos importantes da nossa jornada
- Datas especiais (lançamentos, eventos sazonais)
- Momentos de pausa para avaliar
- Pontos de virada na história

### 5.4 Os gatilhos que ativam novos capítulos
[Quando certos eventos disparam ações automáticas]

### 5.5 Como novos personagens entram na história
[Estratégias de aquisição de clientes ao longo do tempo]

Use linguagem de contador de histórias. Cada mês deve parecer um novo capítulo emocionante.
"""
    response = modelo.generate_content(prompt)
    return response.text


def gerar_recomendacoes_finais(plano_completo, cliente, objetivos,
                              instrucoes_refinamento=None, versao_anterior=None):
    """Ato 6: O Desfecho - Recomendações finais e o que vem depois"""
    
    prompt_intro = """
Chegamos ao último ato da nossa história: o **ATO 6 - O DESFECHO**.

Toda boa história precisa de um final que inspire, que motive, que mostre o caminho adiante.
Aqui vamos resumir tudo que aprendemos, dar as recomendações finais,
e preparar nosso protagonista para o que vem depois que esta história terminar.

Porque, como em toda grande saga, o fim é apenas o começo de uma nova jornada.
"""
    
    if instrucoes_refinamento and versao_anterior:
        prompt = f"""
{prompt_intro}

Você já havia escrito uma versão do desfecho, mas o cliente pediu ajustes.
MANTENHA a narrativa existente, mas refine APENAS os pontos solicitados.

**VERSÃO ANTERIOR:**
{versao_anterior}

**INSTRUÇÕES DE REFINAMENTO:**
{instrucoes_refinamento}

Retorne a versão COMPLETA do desfecho, aplicando apenas os refinamentos.
"""
    else:
        prompt = f"""
{prompt_intro}

**A HISTÓRIA COMPLETA (resumo):**
{plano_completo[:1000]}...

**Protagonista:** {cliente}
**Objetivo original:** {objetivos}

Agora, escreva o **ATO 6 - O DESFECHO** em formato narrativo.

Estruture como:

## 📖 ATO 6: O DESFECHO - A Jornada Continua

### 6.1 O resumo da nossa epopeia
[Um parágrafo poderoso contando toda a história em poucas palavras]

### 6.2 As lições que vamos aprender
[3-5 aprendizados que esperamos obter com esta jornada]

### 6.3 Como ajustar a rota durante a viagem
[Recomendações de otimização contínua - o que monitorar, quando ajustar]

### 6.4 O que fazer agora: os primeiros passos
[Checklist de ações imediatas, como se fosse "o que levar na mochila"]

### 6.5 As perguntas que ainda precisamos responder
[Dúvidas estratégicas que devem ser resolvidas antes de partir]

### 6.6 A mensagem do narrador
[Uma mensagem inspiradora para motivar a equipe, conectando ao propósito maior]

Finalize com uma citação ou metáfora que encapsule toda a jornada.
"""
    response = modelo.generate_content(prompt)
    return response.text

# ============================================================================
# FUNÇÕES DE INTERFACE (CORRIGIDAS - SEM EXPANDERS ANINHADOS)
# ============================================================================

def render_refinamento_box(etapa_nome, etapa_chave, funcao_gerar, **kwargs):
    """Caixa de refinamento com storytelling - SEM EXPANDERS ANINHADOS"""
    
    st.markdown("---")
    st.subheader("✏️ Refinar este capítulo")
    
    # Usar columns em vez de expander aninhado
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**O que você gostaria de ajustar no {etapa_nome}?**")
    
    with col2:
        mostrar_form = st.checkbox("✏️ Refinar", key=f"show_refine_{etapa_chave}")
    
    if mostrar_form:
        st.markdown("Seja específico. Exemplos:")
        st.markdown("- 'Aumente o orçamento do Capítulo 2 para 40%'")
        st.markdown("- 'Adicione TikTok como aliado no Capítulo 1'")
        st.markdown("- 'Mude a métrica principal de Alcance para Impressões'")
        
        with st.form(key=f"refine_form_{etapa_chave}"):
            instrucao = st.text_area(
                "Instruções para reescrever esta cena:",
                height=100,
                placeholder="Descreva os ajustes que você quer na narrativa..."
            )
            
            col1, col2 = st.columns(2)
            with col1:
                submit_refine = st.form_submit_button("🔄 Reescrever com estes ajustes", use_container_width=True)
            with col2:
                cancel_refine = st.form_submit_button("↩️ Manter como está", use_container_width=True)
            
            if submit_refine and instrucao:
                with st.spinner("Reescrevendo este capítulo..."):
                    versao_anterior = st.session_state.narrativa_gerada[etapa_chave]
                    kwargs['instrucoes_refinamento'] = instrucao
                    kwargs['versao_anterior'] = versao_anterior
                    
                    nova_versao = funcao_gerar(**kwargs)
                    st.session_state.narrativa_gerada[etapa_chave] = nova_versao
                    st.rerun()

def render_metas_okr_editor(fases_detalhadas):
    """Editor de metas OKR com linguagem narrativa - SEM EXPANDERS ANINHADOS"""
    
    st.markdown("---")
    st.subheader("🎯 Definir os objetivos de cada capítulo")
    st.markdown("""
    Como em toda boa história, nosso protagonista precisa de metas claras.
    Defina o que queremos alcançar em cada capítulo da jornada.
    """)
    
    metas_por_fase = {}
    
    # Identificar capítulos
    capítulos = []
    linhas = fases_detalhadas.split('\n')
    for linha in linhas[:50]:
        if 'Capítulo' in linha and '**' in linha:
            match = re.search(r'\*\*Capítulo[:\s]*(.*?)\*\*', linha, re.IGNORECASE)
            if match:
                capítulos.append(match.group(1).strip())
    
    if not capítulos:
        capítulos = ["Capítulo 1 - O Chamado", "Capítulo 2 - A Travessia", "Capítulo 3 - O Retorno"]
    
    # Usar tabs em vez de expanders aninhados
    if capítulos:
        tabs = st.tabs([f"📊 {c[:20]}..." for c in capítulos])
        
        for idx, (capitulo, tab) in enumerate(zip(capítulos, tabs)):
            with tab:
                st.markdown(f"### {capitulo}")
                st.markdown(f"**O que nosso herói deve conquistar neste capítulo?**")
                
                metas_capitulo = []
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown("**Objetivo**")
                with col2:
                    st.markdown("**Meta**")
                with col3:
                    st.markdown("**Unidade**")
                
                for i in range(2):  # 2 metas por capítulo
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        descricao = st.text_input(
                            f"Objetivo {i+1}",
                            key=f"okr_desc_{capitulo}_{i}",
                            placeholder="Ex: Aumentar o reconhecimento da marca",
                            label_visibility="collapsed"
                        )
                    
                    with col2:
                        valor = st.text_input(
                            "Meta",
                            key=f"okr_valor_{capitulo}_{i}",
                            placeholder="Ex: 1.5M",
                            label_visibility="collapsed"
                        )
                    
                    with col3:
                        unidade = st.selectbox(
                            "Unidade",
                            ["pessoas", "%", "R$", "unidades", "leads"],
                            key=f"okr_unit_{capitulo}_{i}",
                            label_visibility="collapsed"
                        )
                    
                    if descricao and valor:
                        metas_capitulo.append(f"{descricao}: {valor} {unidade}")
                
                if metas_capitulo:
                    metas_por_fase[capitulo] = metas_capitulo
                    st.success(f"✅ Metas definidas para {capitulo}")
    
    if metas_por_fase:
        if st.button("💾 Incorporar estas metas à narrativa", use_container_width=True):
            st.session_state.metas_okr = metas_por_fase
            st.success("Metas salvas! Use o botão de refinamento para reescrever os capítulos com estas metas.")
            st.rerun()
    
    return metas_por_fase

# ============================================================================
# INTERFACE PRINCIPAL STREAMLIT
# ============================================================================

st.title("📖 Planejador Estratégico de Mídias - Uma Jornada Narrativa")
st.markdown("""
Bem-vindo ao **Planejador Narrativo de Mídias** - um consultor de IA que conta histórias.

Aqui, seu plano de mídia não será apenas uma coleção de números e estratégias.
Será uma **jornada épica**, com começo, meio e fim, onde cada decisão flui naturalmente para a próxima,
como os capítulos de um grande livro.

Vamos começar nossa história juntos.
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

# Sidebar com a estrutura narrativa
with st.sidebar:
    st.header("📚 A Jornada em 6 Atos")
    
    narrativa_etapas = {
        1: "🎬 ATO 1: O Encontro",
        2: "🗺️ ATO 2: A Descoberta",
        3: "🏛️ ATO 3: A Estrutura",
        4: "📖 ATO 4: Os Capítulos",
        5: "⏳ ATO 5: A Linha do Tempo",
        6: "✨ ATO 6: O Desfecho",
        7: "📋 O Livro Completo"
    }
    
    for num, desc in narrativa_etapas.items():
        if num < st.session_state.etapa_atual:
            st.success(f"✓ {desc}")
        elif num == st.session_state.etapa_atual:
            st.info(f"▶ {desc}")
        else:
            st.write(f"○ {desc}")
    
    st.markdown("---")
    st.markdown("*Uma história bem contada é uma estratégia bem executada.*")

# ETAPA 1: Coleta de Dados - O Encontro
if st.session_state.etapa_atual == 1:
    st.header("🎬 ATO 1: O Encontro - Conhecendo Nosso Protagonista")
    st.markdown("""
    Toda grande história começa com um encontro. Aqui, vou conhecer você, seu negócio, seus sonhos e desafios.
    **Conte-me tudo.** Quanto mais eu souber, mais épica será nossa jornada.
    """)
    
    with st.form("dados_cliente_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            cliente = st.text_input("Quem é nosso protagonista? (Nome do Cliente) *", 
                                   placeholder="Ex: Loja de Roupas Sustentável")
            orcamento = st.number_input("Qual o tesouro disponível? (Orçamento em R$) *", 
                                       min_value=0.0, step=1000.0, format="%.2f")
            
        with col2:
            canais = st.multiselect(
                "Quais aliados ele já conhece? (Canais de interesse)",
                list(PLATAFORMA_OBJETIVOS.keys())
            )
        
        objetivos = st.text_area("O que nosso herói deseja conquistar? (Objetivos) *", height=100,
                                placeholder="Ex: Aumentar vendas em 30%, lançar novo produto, fortalecer marca...")
        
        contexto = st.text_area("Qual o mundo onde ele vive? (Contexto e Desafios) *", height=150,
                               placeholder="Conte sobre o momento da marca, concorrência, público-alvo...")
        
        st.markdown("*Campos obrigatórios")
        submitted = st.form_submit_button("🚀 Iniciar Nossa Jornada", use_container_width=True)
        
        if submitted:
            if cliente and orcamento and objetivos and contexto:
                with st.spinner("Escrevendo o primeiro ato da nossa história..."):
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
            else:
                st.error("Preencha todos os campos obrigatórios (*)")

# ETAPA 2: Insights Iniciais
elif st.session_state.etapa_atual == 2:
    st.header("🔍 ATO 1: O Encontro (Continuação) - Nossos Primeiros Insights")
    
    st.markdown(st.session_state.narrativa_gerada['insights_iniciais'])
    
    render_refinamento_box(
        "ATO 1",
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
        if st.button("✅ Avançar para o ATO 2", use_container_width=True):
            with st.spinner("Descobrindo os caminhos possíveis..."):
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
        if st.button("↩️ Voltar", use_container_width=True):
            st.session_state.etapa_atual = 1
            st.rerun()

# ETAPA 3: Arquitetura de Canais
elif st.session_state.etapa_atual == 3:
    st.header("🗺️ ATO 2: A Descoberta - Os Caminhos do Herói")
    
    st.markdown(st.session_state.narrativa_gerada['arquitetura_canais'])
    
    render_refinamento_box(
        "ATO 2",
        'arquitetura_canais',
        recomendar_arquitetura_canais,
        insights_iniciais=st.session_state.narrativa_gerada['insights_iniciais'],
        objetivos=st.session_state.dados_coletados['objetivos'],
        orcamento=st.session_state.dados_coletados['orcamento'],
        canais_preferencia=", ".join(st.session_state.dados_coletados['canais_preferencia']) if st.session_state.dados_coletados['canais_preferencia'] else "Definir"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏛️ Avançar para o ATO 3", use_container_width=True):
            with st.spinner("Estruturando os capítulos da jornada..."):
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
        if st.button("↩️ Voltar", use_container_width=True):
            st.session_state.etapa_atual = 2
            st.rerun()

# ETAPA 4: Estrutura Narrativa
elif st.session_state.etapa_atual == 4:
    st.header("🏛️ ATO 3: A Estrutura - Os Capítulos da Nossa História")
    
    st.markdown(st.session_state.narrativa_gerada['estrutura_plano'])
    
    st.markdown("---")
    
    with st.form("estrutura_form"):
        estrutura_confirmada = st.text_area(
            "A estrutura que escolhemos (edite se necessário):",
            value=st.session_state.narrativa_gerada['estrutura_plano'],
            height=200
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submit_estrutura = st.form_submit_button("📖 Confirmar e Avançar para o ATO 4", use_container_width=True)
        with col2:
            cancel_estrutura = st.form_submit_button("↩️ Cancelar", use_container_width=True)
        
        if submit_estrutura:
            if estrutura_confirmada != st.session_state.narrativa_gerada['estrutura_plano']:
                st.session_state.narrativa_gerada['estrutura_plano'] = estrutura_confirmada
            st.session_state.etapa_atual = 5
            st.rerun()
        
        if cancel_estrutura:
            st.rerun()
    
    render_refinamento_box(
        "ATO 3",
        'estrutura_plano',
        definir_estrutura_narrativa,
        arquitetura_canais=st.session_state.narrativa_gerada['arquitetura_canais'],
        objetivos=st.session_state.dados_coletados['objetivos'],
        cliente=st.session_state.dados_coletados['cliente'],
        orcamento=st.session_state.dados_coletados['orcamento']
    )

# ETAPA 5: Detalhamento das Fases
elif st.session_state.etapa_atual == 5:
    st.header("📖 ATO 4: Os Capítulos - A Jornada em Detalhe")
    
    # Se não tem fases geradas ainda, gerar
    if 'fases_detalhadas' not in st.session_state.narrativa_gerada:
        with st.spinner("Escrevendo cada capítulo da nossa história..."):
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
    
    # Editor de OKRs
    with st.expander("🎯 Definir Metas para Cada Capítulo", expanded=not st.session_state.metas_okr):
        metas_okr = render_metas_okr_editor(st.session_state.narrativa_gerada['fases_detalhadas'])
        
        if metas_okr:
            if st.button("💾 Salvar Metas e Reescrever Capítulos", use_container_width=True):
                st.session_state.metas_okr = metas_okr
                with st.spinner("Reescrevendo os capítulos com suas metas..."):
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
    
    render_refinamento_box(
        "ATO 4",
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
        if st.button("⏳ Avançar para o ATO 5", use_container_width=True):
            with st.spinner("Criando a linha do tempo da nossa história..."):
                cronograma = criar_cronograma_narrativo(
                    st.session_state.narrativa_gerada['fases_detalhadas'],
                    st.session_state.dados_coletados['cliente'],
                    st.session_state.dados_coletados['orcamento']
                )
                st.session_state.narrativa_gerada['cronograma'] = cronograma
                st.session_state.etapa_atual = 6
                st.rerun()
    
    with col2:
        if st.button("↩️ Voltar", use_container_width=True):
            st.session_state.etapa_atual = 4
            st.rerun()

# ETAPA 6: Cronograma Narrativo
elif st.session_state.etapa_atual == 6:
    st.header("⏳ ATO 5: A Linha do Tempo - O Ritmo da Nossa História")
    
    st.markdown(st.session_state.narrativa_gerada['cronograma'])
    
    render_refinamento_box(
        "ATO 5",
        'cronograma',
        criar_cronograma_narrativo,
        fases_detalhadas=st.session_state.narrativa_gerada['fases_detalhadas'],
        cliente=st.session_state.dados_coletados['cliente'],
        orcamento=st.session_state.dados_coletados['orcamento']
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✨ Avançar para o ATO 6", use_container_width=True):
            # Compilar plano completo
            plano_completo = f"""
# A GRANDE JORNADA: O PLANO ESTRATÉGICO DE {st.session_state.dados_coletados['cliente'].upper()}

---

## 📖 ATO 1: O ENCONTRO - Conhecendo Nosso Protagonista
{st.session_state.narrativa_gerada['insights_iniciais']}

---

## 🗺️ ATO 2: A DESCOBERTA - Os Caminhos do Herói
{st.session_state.narrativa_gerada['arquitetura_canais']}

---

## 🏛️ ATO 3: A ESTRUTURA - Os Capítulos da Nossa História
{st.session_state.narrativa_gerada['estrutura_plano']}

---

## 📖 ATO 4: OS CAPÍTULOS - A Jornada em Detalhe
{st.session_state.narrativa_gerada['fases_detalhadas']}

---

## ⏳ ATO 5: A LINHA DO TEMPO - O Ritmo da Nossa História
{st.session_state.narrativa_gerada['cronograma']}

---

*Esta história foi escrita em {datetime.now().strftime('%d/%m/%Y')} para {st.session_state.dados_coletados['cliente']}*
"""
            
            with st.spinner("Escrevendo o desfecho da nossa história..."):
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
        if st.button("↩️ Voltar", use_container_width=True):
            st.session_state.etapa_atual = 5
            st.rerun()

# ETAPA 7: Plano Final
elif st.session_state.etapa_atual == 7:
    st.header("✨ ATO 6: O Desfecho - A Jornada Continua")
    st.markdown("""
    **Parabéns! Nossa história está completa.**  
    O plano estratégico abaixo é a saga que você e sua equipe vão viver nos próximos meses.
    """)
    
    with st.expander("📖 O LIVRO COMPLETO: Nossa Jornada Épica", expanded=True):
        st.markdown(st.session_state.plano_final)
    
    # Download
    st.download_button(
        label="📥 Baixar Nossa História (Markdown)",
        data=st.session_state.plano_final,
        file_name=f"jornada_{st.session_state.dados_coletados['cliente'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown",
        use_container_width=True
    )
    
    st.markdown("---")
    
    # Opção de refinamento final
    with st.expander("✏️ Refinar Nossa História Completa"):
        st.markdown("**Deseja fazer ajustes finais em toda a narrativa?**")
        
        with st.form("refinamento_final_form"):
            refinamento_final = st.text_area(
                "Instruções para reescrever partes da história:",
                height=100,
                placeholder="Descreva os ajustes que deseja em toda a narrativa..."
            )
            
            col1, col2 = st.columns(2)
            with col1:
                submit_refinamento = st.form_submit_button("🔄 Reescrever História com Estes Ajustes", use_container_width=True)
            with col2:
                cancel_refinamento = st.form_submit_button("↩️ Manter como Está", use_container_width=True)
            
            if submit_refinamento and refinamento_final:
                with st.spinner("Reescrevendo toda a saga com seus ajustes..."):
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
# A GRANDE JORNADA: O PLANO ESTRATÉGICO DE {st.session_state.dados_coletados['cliente'].upper()}

---

## 📖 ATO 1: O ENCONTRO - Conhecendo Nosso Protagonista
{insights}

---

## 🗺️ ATO 2: A DESCOBERTA - Os Caminhos do Herói
{arquitetura}

---

## 🏛️ ATO 3: A ESTRUTURA - Os Capítulos da Nossa História
{estrutura}

---

## 📖 ATO 4: OS CAPÍTULOS - A Jornada em Detalhe
{fases}

---

## ⏳ ATO 5: A LINHA DO TEMPO - O Ritmo da Nossa História
{cronograma}

---

*Esta história foi escrita em {datetime.now().strftime('%d/%m/%Y')} para {st.session_state.dados_coletados['cliente']}*
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
        if st.button("🔄 Começar uma Nova Jornada", use_container_width=True):
            for key in ['etapa_atual', 'dados_coletados', 'narrativa_gerada', 'plano_final', 'metas_okr']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        if st.button("↩️ Voltar para o ATO 5", use_container_width=True):
            st.session_state.etapa_atual = 6
            st.rerun()
    
    st.markdown("---")
    st.markdown("""
    ### 📌 As Lições do Narrador
    
    *"Toda grande jornada termina onde começou, mas agora conhecemos o caminho."*
    
    Lembre-se dos princípios que guiaram nossa história:
    
    - **Cada capítulo tem seu próprio propósito** - Não meça um capítulo com as métricas de outro
    - **Nossos aliados trabalham juntos** - A sinergia entre canais é mais poderosa que qualquer um sozinho
    - **O protagonista (cliente) está no centro** - Toda decisão deve servir à sua jornada
    - **A história nunca termina** - O desfecho de hoje é o começo da próxima aventura
    
    Que esta saga seja apenas o primeiro volume de uma longa e próspera parceria.
    """)

# Rodapé
st.markdown("---")
st.markdown("""
*Planejador Narrativo de Mídias com IA - Transformando estratégia em histórias.*  
*Baseado nos frameworks de Binet & Field, Byron Sharp, McKinsey e STDC.*  
*Dados e benchmarks do mercado brasileiro.*
""")
