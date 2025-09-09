import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re
from collections import Counter
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Análise de Sinais de Trading",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("📊 Dashboard de Análise - Sala de Sinais de Trading")
st.markdown("---")

# Cache para carregar dados
@st.cache_data
def load_data():
    """Carrega e processa os dados do CSV"""
    try:
        df = pd.read_csv('mensagens_tratadas.csv')
        df['data'] = pd.to_datetime(df['data'])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

# Função para classificar mensagens
def classify_message(message):
    """Classifica o tipo de mensagem"""
    if pd.isna(message):
        return None
    
    message = str(message)
    
    # Sinais
    if "Novo Sinal Encontrado" in message:
        # Extrair par
        par_match = re.search(r'\*\*Par:\*\* `([^`]+)`', message)
        # Extrair direção
        if "🔴⬇️" in message or "Vender" in message:
            direction = "PUT"
        elif "🟢⬆️" in message or "Comprar" in message:
            direction = "CALL"
        else:
            direction = "UNKNOWN"
        
        return {
            'type': 'SIGNAL',
            'par': par_match.group(1) if par_match else 'UNKNOWN',
            'direction': direction,
            'result': None,
            'gale_level': 0
        }
    
    # WIN direto
    elif "WIN em" in message and "G1" not in message and "G2" not in message:
        par_match = re.search(r'WIN em ([A-Z/]+)', message)
        return {
            'type': 'WIN',
            'par': par_match.group(1) if par_match else 'UNKNOWN',
            'direction': None,
            'result': 'WIN',
            'gale_level': 0
        }
    
    # WIN G1
    elif "WIN (G1)" in message:
        par_match = re.search(r'WIN \(G1\) em ([A-Z/]+)', message)
        return {
            'type': 'WIN_G1',
            'par': par_match.group(1) if par_match else 'UNKNOWN',
            'direction': None,
            'result': 'WIN',
            'gale_level': 1
        }
    
    # WIN G2
    elif "WIN (G2)" in message:
        par_match = re.search(r'WIN \(G2\) em ([A-Z/]+)', message)
        return {
            'type': 'WIN_G2',
            'par': par_match.group(1) if par_match else 'UNKNOWN',
            'direction': None,
            'result': 'WIN',
            'gale_level': 2
        }
    
    # STOP (LOSS)
    elif "STOP em" in message:
        par_match = re.search(r'STOP em ([A-Z/]+)', message)
        return {
            'type': 'STOP',
            'par': par_match.group(1) if par_match else 'UNKNOWN',
            'direction': None,
            'result': 'LOSS',
            'gale_level': 2  # STOP sempre acontece após G2
        }
    
    # Chamadas para GALE
    elif "Faça o GALE 1" in message:
        par_match = re.search(r'para ([A-Z/]+)', message)
        return {
            'type': 'GALE_CALL_1',
            'par': par_match.group(1) if par_match else 'UNKNOWN',
            'direction': None,
            'result': None,
            'gale_level': 1
        }
    
    elif "Faça o GALE 2" in message:
        par_match = re.search(r'para ([A-Z/]+)', message)
        return {
            'type': 'GALE_CALL_2',
            'par': par_match.group(1) if par_match else 'UNKNOWN',
            'direction': None,
            'result': None,
            'gale_level': 2
        }
    
    return None

# Função para calcular métricas de assertividade
def calculate_metrics(df):
    """Calcula métricas de assertividade"""
    
    # Classificar todas as mensagens
    df['classification'] = df['mensagem'].apply(classify_message)
    df_classified = df[df['classification'].notna()].copy()
    
    # Extrair informações
    df_classified['msg_type'] = df_classified['classification'].apply(lambda x: x['type'] if x else None)
    df_classified['par'] = df_classified['classification'].apply(lambda x: x['par'] if x else None)
    df_classified['result'] = df_classified['classification'].apply(lambda x: x['result'] if x else None)
    df_classified['gale_level'] = df_classified['classification'].apply(lambda x: x['gale_level'] if x else None)
    df_classified['direction'] = df_classified['classification'].apply(lambda x: x['direction'] if x else None)
    
    # Contar resultados
    win_direto = len(df_classified[df_classified['msg_type'] == 'WIN'])
    win_g1 = len(df_classified[df_classified['msg_type'] == 'WIN_G1'])
    win_g2 = len(df_classified[df_classified['msg_type'] == 'WIN_G2'])
    stop_loss = len(df_classified[df_classified['msg_type'] == 'STOP'])
    total_signals = len(df_classified[df_classified['msg_type'] == 'SIGNAL'])
    gale1_calls = len(df_classified[df_classified['msg_type'] == 'GALE_CALL_1'])
    gale2_calls = len(df_classified[df_classified['msg_type'] == 'GALE_CALL_2'])
    
    # Calcular métricas
    total_wins = win_direto + win_g1 + win_g2
    total_operations = total_wins + stop_loss
    assertividade = (total_wins / total_operations * 100) if total_operations > 0 else 0
    
    # Assertividade sem Gale (apenas wins diretos vs total de sinais)
    assertividade_sem_gale = (win_direto / total_signals * 100) if total_signals > 0 else 0
    
    metrics = {
        'total_signals': total_signals,
        'win_direto': win_direto,
        'win_g1': win_g1,
        'win_g2': win_g2,
        'stop_loss': stop_loss,
        'total_wins': total_wins,
        'total_operations': total_operations,
        'assertividade': assertividade,
        'assertividade_sem_gale': assertividade_sem_gale,
        'gale1_calls': gale1_calls,
        'gale2_calls': gale2_calls,
        'uso_gale_1': (gale1_calls / total_signals * 100) if total_signals > 0 else 0,
        'uso_gale_2': (gale2_calls / total_signals * 100) if total_signals > 0 else 0
    }
    
    return metrics, df_classified

# Carregar dados
df = load_data()

if df is not None:
    
    # Sidebar com informações
    st.sidebar.header("ℹ️ Informações dos Dados")
    st.sidebar.write(f"**Total de mensagens:** {len(df):,}")
    st.sidebar.write(f"**Período:** {df['data'].min().strftime('%d/%m/%Y')} até {df['data'].max().strftime('%d/%m/%Y')}")
    
    # Filtros
    st.sidebar.header("🔧 Filtros")
    
    # Filtro de data
    min_date = df['data'].min().date()
    max_date = df['data'].max().date()
    
    date_range = st.sidebar.date_input(
        "Período de análise",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = df[
            (df['data'].dt.date >= start_date) & 
            (df['data'].dt.date <= end_date)
        ]
    else:
        df_filtered = df
    
    # Calcular métricas
    metrics, df_classified = calculate_metrics(df_filtered)

    col1a, col2a = st.columns(2, gap="large")

    with col1a:
        st.header("Simulação de entrada com $10 e payout fixo de 90%")
        st.markdown("**Premissas:**")
        st.markdown("- Entrada inicial: $10")
        st.markdown("- Payout fixo: 90% (ou seja, um WIN retorna $9,00 de lucro)")
        st.markdown("- Win no Gale 1: $8,00 de lucro")
        st.markdown("- Win no Gale 2: $6,00 de lucro")
        st.markdown("- STOP total: perda de $70,00")

        # Cálculo do resultado financeiro
        lucro_entrada = metrics['win_direto'] * 9
        lucro_gale1 = metrics['win_g1'] * 8
        lucro_gale2 = metrics['win_g2'] * 6
        perda_stop = metrics['stop_loss'] * (-70)
        resultado_final = lucro_entrada + lucro_gale1 + lucro_gale2 + perda_stop
        st.markdown(f"**Resultado Final:** <span style='color: red'>${resultado_final:.2f}</span>", unsafe_allow_html=True)

    with col2a:
        st.header("Detalhamento do Resultado")
        st.markdown(f"- **Lucro com WIN Direto:** ${lucro_entrada:.2f} ({metrics['win_direto']} WINs)")
        st.markdown(f"- **Lucro com WIN Gale 1:** ${lucro_gale1:.2f} ({metrics['win_g1']} WINs)")
        st.markdown(f"- **Lucro com WIN Gale 2:** ${lucro_gale2:.2f} ({metrics['win_g2']} WINs)")
        st.markdown(f"- **Perda com STOPs:** ${perda_stop:.2f} ({metrics['stop_loss']} STOPs)")
        st.markdown(f"- **Total de Operações Analisadas:** {metrics['total_operations']}")
        st.markdown(f"- **Total de Sinais Iniciais:** {metrics['total_signals']}")

    st.markdown("---")
    
    # Métricas principais
    st.header("📈 Métricas Principais")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total de Sinais", metrics['total_signals'])
    
    with col2:
        st.metric("Assertividade Geral", f"{metrics['assertividade']:.1f}%")
    
    with col3:
        st.metric("Caso entrasse com $10,00", f"{metrics['assertividade_sem_gale']:.1f}%")
    
    with col4:
        st.metric("Total de WINs", metrics['total_wins'])
    
    with col5:
        st.metric("Total de STOPs", metrics['stop_loss'])
    
    # Métricas secundárias
    st.subheader("📊 Detalhamento das Operações")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("WIN Direto", metrics['win_direto'])
    
    with col2:
        st.metric("WIN G1", metrics['win_g1'])
    
    with col3:
        st.metric("WIN G2", metrics['win_g2'])
    
    with col4:
        st.metric("Uso de Gale 1", f"{metrics['uso_gale_1']:.1f}%")
    
    with col5:
        st.metric("Uso de Gale 2", f"{metrics['uso_gale_2']:.1f}%")
    
    with col6:
        recovery_rate = ((metrics['win_g1'] + metrics['win_g2']) / (metrics['gale1_calls']) * 100) if metrics['gale1_calls'] > 0 else 0
        st.metric("Taxa de Recuperação", f"{recovery_rate:.1f}%")
    
    # Gráficos principais
    st.header("📊 Visualizações e Análises")
    
    # Row 1: Distribuição de resultados e performance por par
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribuição de Resultados")
        
        # Dados para o gráfico de pizza
        results_data = {
            'WIN Direto': metrics['win_direto'],
            'WIN G1': metrics['win_g1'],
            'WIN G2': metrics['win_g2'],
            'STOP': metrics['stop_loss']
        }
        
        fig_pie = px.pie(
            values=list(results_data.values()),
            names=list(results_data.keys()),
            title="Distribuição de Resultados por Tipo",
            color_discrete_map={
                'WIN Direto': '#00CC96',
                'WIN G1': '#19D3F3',
                'WIN G2': '#FF9F43',
                'STOP': '#FF6B6B'
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("Performance por Par")
        
        # Análise por par
        par_analysis = df_classified[df_classified['result'].notna()].groupby('par').agg({
            'result': ['count', lambda x: (x == 'WIN').sum()]
        }).reset_index()
        
        if not par_analysis.empty:
            par_analysis.columns = ['par', 'total', 'wins']
            par_analysis['assertividade'] = (par_analysis['wins'] / par_analysis['total'] * 100).round(1)
            
            fig_bar_par = px.bar(
                par_analysis,
                x='par',
                y='assertividade',
                title="Assertividade por Par de Moedas",
                labels={'par': 'Par', 'assertividade': 'Assertividade (%)'},
                color='assertividade',
                color_continuous_scale='RdYlGn'
            )
            fig_bar_par.update_layout(showlegend=False)
            st.plotly_chart(fig_bar_par, use_container_width=True)
    
    # Row 2: Análise temporal
    st.subheader("📅 Análise Temporal")
    
    # Preparar dados temporais
    df_results = df_classified[df_classified['result'].notna()].copy()
    df_results['date'] = df_results['data'].dt.date
    
    daily_analysis = df_results.groupby('date').agg({
        'result': ['count', lambda x: (x == 'WIN').sum()]
    }).reset_index()
    
    if not daily_analysis.empty:
        daily_analysis.columns = ['date', 'total_ops', 'wins']
        daily_analysis['losses'] = daily_analysis['total_ops'] - daily_analysis['wins']
        daily_analysis['assertividade'] = (daily_analysis['wins'] / daily_analysis['total_ops'] * 100).round(1)
        
        # Gráfico temporal combinado
        fig_temporal = go.Figure()
        
        # Barras para wins e losses
        fig_temporal.add_trace(go.Bar(
            x=daily_analysis['date'],
            y=daily_analysis['wins'],
            name='WINs',
            marker_color='#00CC96'
        ))
        
        fig_temporal.add_trace(go.Bar(
            x=daily_analysis['date'],
            y=daily_analysis['losses'],
            name='STOPs',
            marker_color='#FF6B6B'
        ))
        
        # Linha para assertividade
        fig_temporal.add_trace(go.Scatter(
            x=daily_analysis['date'],
            y=daily_analysis['assertividade'],
            mode='lines+markers',
            name='Assertividade (%)',
            yaxis='y2',
            line=dict(color='#FFA500', width=3)
        ))
        
        fig_temporal.update_layout(
            title='Performance Diária: WINs vs STOPs e Assertividade',
            xaxis_title='Data',
            yaxis=dict(title='Número de Operações'),
            yaxis2=dict(title='Assertividade (%)', overlaying='y', side='right'),
            barmode='stack',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_temporal, use_container_width=True)
    
    # Row 3: Análise de horários e padrões
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribuição por Hora do Dia")
        
        df_signals = df_classified[df_classified['msg_type'] == 'SIGNAL'].copy()
        if not df_signals.empty:
            df_signals['hora'] = df_signals['data'].dt.hour
            hourly_dist = df_signals['hora'].value_counts().sort_index()
            
            fig_hourly = px.bar(
                x=hourly_dist.index,
                y=hourly_dist.values,
                title="Distribuição de Sinais por Hora",
                labels={'x': 'Hora do Dia', 'y': 'Quantidade de Sinais'},
                color=hourly_dist.values,
                color_continuous_scale='viridis'
            )
            fig_hourly.update_layout(showlegend=False)
            st.plotly_chart(fig_hourly, use_container_width=True)
    
    with col2:
        st.subheader("Análise de Direção (PUT vs CALL)")
        
        direction_analysis = df_classified[df_classified['direction'].notna()]
        if not direction_analysis.empty:
            direction_counts = direction_analysis['direction'].value_counts()
            
            fig_direction = px.pie(
                values=direction_counts.values,
                names=direction_counts.index,
                title="Distribuição PUT vs CALL",
                color_discrete_map={'PUT': '#FF6B6B', 'CALL': '#00CC96'}
            )
            st.plotly_chart(fig_direction, use_container_width=True)
    
    # Row 4: Análise de eficácia do Gale
    st.subheader("🎯 Análise da Estratégia Martingale (Gale)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Eficácia por Nível de Gale")
        
        gale_data = {
            'Nível': ['Entrada', 'Gale 1', 'Gale 2'],
            'WINs': [metrics['win_direto'], metrics['win_g1'], metrics['win_g2']],
            'Tentativas': [metrics['total_signals'], metrics['gale1_calls'], metrics['gale2_calls']]
        }
        
        gale_df = pd.DataFrame(gale_data)
        gale_df['Eficácia (%)'] = (gale_df['WINs'] / gale_df['Tentativas'] * 100).round(1)
        
        fig_gale_efic = px.bar(
            gale_df,
            x='Nível',
            y='Eficácia (%)',
            title="Eficácia por Nível de Gale",
            color='Eficácia (%)',
            color_continuous_scale='RdYlGn',
            text='Eficácia (%)'
        )
        fig_gale_efic.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_gale_efic.update_layout(showlegend=False)
        st.plotly_chart(fig_gale_efic, use_container_width=True)
    
    with col2:
        st.subheader("Fluxo de Operações")
        
        # Calcular o fluxo
        entrada_to_win = metrics['win_direto']
        entrada_to_gale1 = metrics['gale1_calls']
        gale1_to_win = metrics['win_g1']
        gale1_to_gale2 = metrics['gale2_calls']
        gale2_to_win = metrics['win_g2']
        gale2_to_stop = metrics['stop_loss']
        
        st.write("**Fluxo das Operações:**")
        st.write(f"🟢 **{metrics['total_signals']} Sinais** iniciais")
        st.write(f"├─ ✅ {entrada_to_win} WINs diretos ({entrada_to_win/metrics['total_signals']*100:.1f}%)")
        st.write(f"└─ ⚠️ {entrada_to_gale1} foram para Gale 1 ({entrada_to_gale1/metrics['total_signals']*100:.1f}%)")
        st.write(f"   ├─ ✅ {gale1_to_win} WINs no G1 ({gale1_to_win/entrada_to_gale1*100:.1f}%)")
        st.write(f"   └─ ⚠️ {gale1_to_gale2} foram para Gale 2 ({gale1_to_gale2/entrada_to_gale1*100:.1f}%)")
        st.write(f"      ├─ ✅ {gale2_to_win} WINs no G2 ({gale2_to_win/gale1_to_gale2*100:.1f}%)")
        st.write(f"      └─ ❌ {gale2_to_stop} STOPs ({gale2_to_stop/gale1_to_gale2*100:.1f}%)")
    
    with col3:
        st.subheader("Métricas de Gale")
        
        # Métricas calculadas
        taxa_entrada_direta = (metrics['win_direto'] / metrics['total_signals'] * 100) if metrics['total_signals'] > 0 else 0
        taxa_uso_gale = ((metrics['gale1_calls']) / metrics['total_signals'] * 100) if metrics['total_signals'] > 0 else 0
        taxa_recuperacao_g1 = (metrics['win_g1'] / metrics['gale1_calls'] * 100) if metrics['gale1_calls'] > 0 else 0
        taxa_recuperacao_g2 = (metrics['win_g2'] / metrics['gale2_calls'] * 100) if metrics['gale2_calls'] > 0 else 0
        
        st.metric("Taxa Win Entrada", f"{taxa_entrada_direta:.1f}%")
        st.metric("Taxa Uso Gale", f"{taxa_uso_gale:.1f}%")
        st.metric("Recuperação G1", f"{taxa_recuperacao_g1:.1f}%")
        st.metric("Recuperação G2", f"{taxa_recuperacao_g2:.1f}%")
        
        # ROI Estimado (assumindo entrada = 1, G1 = 2.31, G2 = 5.38)
        roi_entrada = entrada_to_win * 0.8  # WIN = 80% de lucro
        roi_gale1 = gale1_to_win * 0.8 - (entrada_to_gale1 * 1)  # WIN G1 = 80% - perda entrada
        roi_gale2 = gale2_to_win * 0.8 - (gale1_to_gale2 * 3.31)  # WIN G2 = 80% - perdas G1+entrada
        roi_stop = -(gale2_to_stop * 6.69)  # STOP = perda total
        
        roi_total = roi_entrada + roi_gale1 + roi_gale2 + roi_stop
        st.metric("ROI Estimado", f"{roi_total:.2f} unidades")
    
    # Tabela de operações recentes
    st.header("📋 Histórico de Operações")
    
    # Mostrar últimas operações
    recent_ops = df_classified[df_classified['msg_type'].isin(['SIGNAL', 'WIN', 'WIN_G1', 'WIN_G2', 'STOP'])].copy()
    recent_ops = recent_ops.sort_values('data', ascending=False).head(50)
    
    # Preparar dados para exibição
    display_ops = recent_ops[['data', 'msg_type', 'par', 'direction', 'result']].copy()
    display_ops['data'] = display_ops['data'].dt.strftime('%d/%m/%Y %H:%M')
    display_ops.columns = ['Data/Hora', 'Tipo', 'Par', 'Direção', 'Resultado']
    
    st.dataframe(display_ops, use_container_width=True)
    
    # Informações adicionais na sidebar
    st.sidebar.header("📈 Resumo Executivo")
    st.sidebar.write(f"**Assertividade Geral:** {metrics['assertividade']:.1f}%")
    st.sidebar.write(f"**Operações Analisadas:** {metrics['total_operations']:,}")
    st.sidebar.write(f"**Taxa de Uso de Gale:** {((metrics['gale1_calls']/metrics['total_signals'])*100):.1f}%")
    
    # Performance por par na sidebar
    if not par_analysis.empty:
        st.sidebar.header("🎯 Performance por Par")
        for _, row in par_analysis.iterrows():
            st.sidebar.write(f"**{row['par']}:** {row['assertividade']:.1f}% ({row['wins']}/{row['total']})")

else:
    st.error("❌ Não foi possível carregar os dados. Verifique se o arquivo 'mensagens_tratadas.csv' está no diretório correto.")
    st.info("📁 O arquivo deve estar na mesma pasta que este dashboard.")
