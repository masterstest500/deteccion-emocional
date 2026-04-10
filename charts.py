import plotly.graph_objects as go

def crear_radar_poms(valores, riesgo):
    """
    Crea un gráfico de radar basado en las métricas emocionales.
    Recibe 'valores' (lista de floats) y 'riesgo' (string para definir el color).
    """
    # 1. Definir el color según el nivel de riesgo
    colores_map = {
        "Alto": "#ff4444",   # Rojo
        "Medio": "#ffaa44",  # Naranja
        "Bajo": "#44cc44"    # Verde
    }
    
    # Si el riesgo no coincide, usa un gris neutro
    color_linea = colores_map.get(riesgo, "#888888")
    
    # 2. Configurar las categorías del radar
    categorias = ['Estrés', 'Fatiga', 'Tensión', 'Activación', 'Estado Emocional']
    
    # Asegurar que el gráfico se "cierre" repitiendo el primer valor al final
    # (Opcional en Plotly, pero ayuda a la simetría)
    
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill='toself',
        name='Perfil',
        line=dict(color=color_linea, width=2),
        fillcolor=color_linea,
        opacity=0.4,
        marker=dict(size=8)
    ))

    # 3. Diseño estético del gráfico (Cyberpunk/Dark Mode)
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                gridcolor="#444444",
                tickfont=dict(color="#888888", size=10)
            ),
            angularaxis=dict(
                gridcolor="#444444",
                tickfont=dict(color="#cccccc", size=11)
            )
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=30, b=30),
        height=320,
        dragmode=False
    )

    return fig, color_linea