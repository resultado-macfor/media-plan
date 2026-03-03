        if metas_okr and st.button("💾 Salvar Metas e Reescrever Capítulos", use_container_width=True):
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
