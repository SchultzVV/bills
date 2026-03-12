#!/bin/bash

# Script para executar o app Streamlit estendido
echo "🚀 Iniciando App Streamlit - Sistema Estendido de Análise GFET"
echo "================================================"
echo ""
echo "📊 Funcionalidades:"
echo "  ✅ Comparação entre etapas"
echo "  ✅ Comparação entre corridas (sweeps)"
echo "  ✅ Visualização customizada"
echo "  ✅ Análise de reprodutibilidade"
echo ""
echo "🌐 O app será aberto em: http://localhost:8501"
echo ""

# Executar streamlit
streamlit run streamlit_app_extended.py
