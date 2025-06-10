import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import unidecode
from shapely.geometry import shape
from shapely.ops import unary_union

st.set_page_config(layout="wide")
st.title("Mapa de Previsão Agrícola - Região Geográfica Intermediária de Santa Maria/RS")
st.markdown("<br><br>", unsafe_allow_html=True)

# Seu código para carregar os arquivos de média
arquivos = {
    'media_rendimento_medio_arroz_30anos.csv': ('rendimento_medio', 'arroz', '30 anos'),
    'media_rendimento_medio_soja_20anos.csv': ('rendimento_medio', 'soja', '20 anos'),
    'media_rendimento_medio_soja_30anos.csv': ('rendimento_medio', 'soja', '30 anos'),
    'media_quantidade_produzida_arroz_20anos.csv': ('quantidade_produzida', 'arroz', '20 anos'),
    'media_quantidade_produzida_arroz_30anos.csv': ('quantidade_produzida', 'arroz', '30 anos'),
    'media_quantidade_produzida_soja_20anos.csv': ('quantidade_produzida', 'soja', '20 anos'),
    'media_quantidade_produzida_soja_30anos.csv': ('quantidade_produzida', 'soja', '30 anos'),
}


nomes_variaveis_amigaveis = {
    "rendimento_medio": "Rendimento Médio (kg/ha)",
    "quantidade_produzida": "Quantidade Produzida (ton)",
    # adicione os outros conforme necessário
}

def padronizar_nome(nome):
    return unidecode.unidecode(nome.lower().strip())


# Criar uma coluna para o hover com formatação em HTML:
def formatar_diferenca(diff):
    if pd.isna(diff):
        return "Média indisponível"
    bolinha = "🟢" if diff >= 0 else "🔴"
    sinal = "+" if diff >= 0 else ""
    return f"{bolinha} {sinal}{diff:.2f}"


# 1. Corrige dicionário com as chaves padronizadas
nomes_cidades_amigaveis = {
    padronizar_nome(k): v for k, v in {
        "Agudo": "Agudo",
        "Cacapava do sul": "Caçapava do Sul",
        "Cacequi": "Cacequi",
        "Cachoeira do sul": "Cachoeira do Sul",
        "Capao do cipo": "Capão do Cipó",
        "Cerro branco": "Cerro Branco",
        "Dilermano de aguiar": "Dilermando de Aguiar",
        "Dona francisca": "Dona Francisca",
        "Faxinal do soturno": "Faxinal do Soturno",
        "Formigueiro": "Formigueiro",
        "Itaara": "Itaara",
        "Itacurubi": "Itacurubi",
        "Ivora": "Ivorá",
        "Jaguari": "Jaguari",
        "Jari": "Jari",
        "Julio de castilhos": "Júlio de Castilhos",
        "Lavras do sul": "Lavras do Sul",
        "Mata": "Mata",
        "Nova esperanca do sul": "Nova Esperança do Sul",
        "Nova palma": "Nova Palma",
        "Novo cabrais": "Novo Cabrais",
        "Paraiso do sul": "Paraíso do Sul",
        "Pinhal grande": "Pinhal Grande",
        "Quevedos": "Quevedos",
        "Restinga seca": "Restinga Seca",
        "Santa margarida do sul": "Santa Margarida do Sul",
        "Santa maria": "Santa Maria",
        "Santana da boa vista": "Santana da Boa Vista",
        "Santiago": "Santiago",
        "Sao francisco de assis": "São Francisco de Assis",
        "Sao gabriel": "São Gabriel",
        "Sao joao do polesine": "São João do Polêsine",
        "Sao martinho da serra": "São Martinho da Serra",
        "Sao pedro do sul": "São Pedro do Sul",
        "Sao sepe": "São Sepé",
        "Sao vicente do sul": "São Vicente do Sul",
        "Silveira martins": "Silveira Martins",
        "Toropi": "Toropi",
        "Unistalda": "Unistalda",
        "Vila nova do sul": "Vila Nova do Sul"
    }.items()
}

descricoes_cenarios = {
    "ssp126": (
        "Cenário otimista que pressupõe uma forte mitigação das emissões de gases de efeito estufa, "
        "com adoção ampla de tecnologias limpas, políticas ambientais rigorosas e transição para fontes "
        "renováveis de energia. Reflete um desenvolvimento sustentável com crescimento populacional baixo"
        "e econômico equilibrado, resultando em aumento da qualidade de vida e menores impactos climáticos."
    ),
    "ssp245": (
        "Cenário intermediário que assume um caminho de desenvolvimento equilibrado, onde as emissões de "
        "gases de efeito estufa crescem moderadamente. As políticas climáticas são implementadas de forma "
        "gradual, com algumas melhorias tecnológicas, mas ainda há dependência significativa de combustíveis fósseis. "
        "Esse cenário reflete um crescimento populacional e econômico moderado, com esforços parciais para a sustentabilidade."
    ),
    "ssp370": (
        "Cenário pessimista caracterizado por emissões elevadas e mitigação insuficiente dos impactos ambientais. "
        "Neste cenário, há uma dependência contínua de fontes de energia fósseis, políticas ambientais fracas e "
        "crescimento econômico e populacional acelerado, especialmente em países em desenvolvimento. Isso resulta "
        "em aumentos significativos da temperatura global e impactos severos nos ecossistemas e na sociedade."
    ),
    "ssp585": (
        "Cenário extremo que prevê um aumento acelerado das emissões de gases de efeito estufa devido à falta de "
        "controle sobre as atividades humanas e ausência de políticas climáticas efetivas. O crescimento econômico "
        "e populacional é rápido, mas baseado em modelos insustentáveis, com alta exploração dos recursos naturais. "
        "Esse cenário indica um futuro com impactos climáticos severos, eventos climáticos extremos mais frequentes e "
        "desafios críticos para a adaptação global."
    ),
}


dfs = []

for arquivo, (variavel_media, cultivo_media, periodo_media) in arquivos.items():
    df_temp = pd.read_csv(arquivo)
    
    # Extrai a coluna que começa com "media_"
    col_media = [col for col in df_temp.columns if col.startswith('media_')]
    if not col_media:
        raise ValueError(f"Nenhuma coluna começando com 'media_' encontrada em {arquivo}")
    
    # Cria a coluna valor padronizada
    df_temp['valor'] = df_temp[col_media[0]]
    
    df_temp['variavel'] = variavel_media
    df_temp['cultivo'] = cultivo_media
    df_temp['periodo'] = periodo_media
    df_temp["cidade"] = df_temp["cidade"].apply(padronizar_nome)  # importante padronizar nome da cidade!
    
    dfs.append(df_temp)

df_medias = pd.concat(dfs, ignore_index=True)


def texto_hover(valor_atual, media):
    if pd.isna(media):
        return "Média indisponível"
    diff = valor_atual - media
    cor = 'green' if diff >= 0 else 'red'
    sinal = '+' if diff >= 0 else ''
    return f"<span style='color:{cor}'>{sinal}{diff:.2f}</span>"

df = pd.read_csv("dados_transformados.csv")
df["cidade"] = df["cidade"].apply(padronizar_nome)

# 2. Inverter dicionário
nomes_cidades_invertido = {v: k for k, v in nomes_cidades_amigaveis.items()}

# 3. Padronize os nomes da coluna cidade do dataframe
df["cidade"] = df["cidade"].apply(padronizar_nome)

# 4. Converte os nomes padronizados para amigáveis
cidades_padronizadas = df["cidade"].unique()
cidades_amigaveis = [nomes_cidades_amigaveis.get(c, c.title()) for c in cidades_padronizadas]
cidades_amigaveis = sorted(cidades_amigaveis)

with open("geojs-43-mun.json", encoding='utf-8') as f:
    geojson = json.load(f)

for feature in geojson["features"]:
    nome_mun = feature["properties"]["name"]
    nome_mun_formatado = padronizar_nome(nome_mun)
    feature["id"] = nome_mun_formatado

with open("regiao-intermediaria-sm.txt", "r", encoding="utf-8") as f:
    cidades_santa_maria = [padronizar_nome(linha) for linha in f if linha.strip()]

df["regiao_santa_maria"] = df["cidade"].apply(lambda x: x in cidades_santa_maria)

geojson_sm = {
    "type": "FeatureCollection",
    "features": [f for f in geojson["features"] if f["id"] in cidades_santa_maria]
}

# --- Borda da RGI ---
poligonos_rgi = [shape(f["geometry"]) for f in geojson["features"] if f["id"] in cidades_santa_maria]
borda_rgi = unary_union(poligonos_rgi)

coords = []
if borda_rgi.geom_type == 'Polygon':
    coords = list(borda_rgi.exterior.coords)
elif borda_rgi.geom_type == 'MultiPolygon':
    for pol in borda_rgi.geoms:
        coords.extend(list(pol.exterior.coords))

lons, lats = zip(*coords)

cidades = sorted(df["cidade"].unique())
# --- Interface ---
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    safra = st.selectbox("Safra (Ano):", sorted(df["safra"].unique()))

# Criar dicionário: "Soja" → "soja"
cultivos_unicos = sorted(df["cultivo"].unique())
cultivos_formatados = {c.capitalize(): c for c in cultivos_unicos}

with col2:
    # Selectbox com rótulo amigável
    cultivo_formatado = st.selectbox("Cultivo:", list(cultivos_formatados.keys()))

    # Obter o valor original (minúsculo) a partir do selecionado
    cultivo = cultivos_formatados[cultivo_formatado]

with col3:
    # Lista de variáveis disponíveis no dataframe
    variaveis_disponiveis = sorted(df["variavel_alvo"].unique())

    # Criar lista de labels amigáveis, mantendo apenas os que existem no DataFrame
    opcoes_variaveis = [nomes_variaveis_amigaveis[v] for v in variaveis_disponiveis]

    # Mostrar label no selectbox
    variavel_label = st.selectbox("Variável:", opcoes_variaveis)

    # Obter o valor real (ex: "rendimento_medio") a partir do label
    variavel = {v: k for k, v in nomes_variaveis_amigaveis.items()}[variavel_label]

with col4:
    modelo = st.selectbox("Série Temporal (histórico):", sorted(df["modelo"].unique()))

with col5:
    cidade_amigavel = st.selectbox("Cidade:", ["Todas"] + cidades_amigaveis)

    if cidade_amigavel != "Todas":
        cidade_selecionada = nomes_cidades_invertido.get(cidade_amigavel)
        df_tabela = df[
            (df["safra"] == safra) &
            (df["cultivo"] == cultivo) &
            (df["variavel_alvo"] == variavel) &
            (df["modelo"] == modelo) &
            (df["cidade"] == cidade_selecionada)
        ]
    else:
        cidade_selecionada = "Todas"
      
        df_tabela = df[
            (df["safra"] == safra) &
            (df["cultivo"] == cultivo) &
            (df["variavel_alvo"] == variavel) &
            (df["modelo"] == modelo)
        ]




combinacao_invalida = (
    cultivo == "arroz" and variavel == "rendimento_medio" and modelo == "20anos"
)

cenarios = ["ssp126", "ssp245", "ssp370", "ssp585"]  # substitua pelos nomes exatos dos cenários no seu CSV


# Calcular zmin e zmax globais para os 4 cenários
valores_globais = []

for cenario in cenarios:
    df_filtrado = df[
        (df["safra"] == safra) &
        (df["cultivo"] == cultivo) &
        (df["cenario"] == cenario) &
        (df["variavel_alvo"] == variavel) &
        (df["modelo"] == modelo)
    ]

    if cidade_selecionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado["cidade"] == cidade_selecionada]

    df_validos = df_filtrado[df_filtrado["cidade"].isin(cidades_santa_maria)]
    valores = df_validos["valor"].dropna().tolist()
    valores_globais.extend(valores)

if valores_globais:
    zmin_global = min(valores_globais)
    zmax_global = max(valores_globais)
else:
    zmin_global, zmax_global = None, None

df_filtrado_todos = pd.DataFrame()

if combinacao_invalida:
    st.warning("Essa combinação (arroz + rendimento_medio + 20 anos) não está disponível.")
else:
    # ao invés de cols = st.columns(4)

    # Vamos fazer em duas linhas, cada uma com 2 colunas:
    for linha in range(2):
        cols = st.columns(2)
        for i in range(2):
            idx = linha * 2 + i
            cenario = cenarios[idx]
            
            df_filtrado = df[
                (df["safra"] == safra) &
                (df["cultivo"] == cultivo) &
                (df["cenario"] == cenario) &
                (df["variavel_alvo"] == variavel) &
                (df["modelo"] == modelo)
            ]

            df_medias["periodo"] = df_medias["periodo"].astype(str).str.strip()

            df_filtrado = df_filtrado.merge(
                df_medias[(df_medias["cultivo"] == cultivo) & (df_medias["variavel"] == variavel) & (df_medias["periodo"] == modelo)],
                on="cidade", how="left", suffixes=("", "_media")
            )
            df_filtrado["diferenca"] = df_filtrado["valor"] - df_filtrado["valor_media"]

            
            df_filtrado["diferenca_colorida"] = df_filtrado["diferenca"].apply(formatar_diferenca)
            if cidade_selecionada != "Todas":
                df_filtrado = df_filtrado[df_filtrado["cidade"] == cidade_selecionada]

            with cols[i]:
                              # Pega o texto conforme o cenário (em minúsculas para garantir correspondência)
                texto_tooltip = descricoes_cenarios.get(cenario.lower(), "Descrição não disponível para este cenário.")

                st.markdown(f"""
                    <style>
                    .tooltip {{
                        position: relative;
                        display: inline-block;
                        cursor: pointer;
                        color: blue;
                        font-weight: bold;
                    }}

                    .tooltip .tooltiptext {{
                        visibility: hidden;
                        width: 220px;
                        background-color: #555;
                        color: #fff;
                        text-align: center;
                        border-radius: 6px;
                        padding: 5px;
                        position: absolute;
                        z-index: 1;
                        top: 125%;
                        left: 50%;
                        margin-left: -110px;
                        opacity: 0;
                        transition: opacity 0.3s;
                        font-weight: normal;   /* texto normal */
                        font-size: 12px;       /* tamanho menor */
                    }}

                    .tooltip:hover .tooltiptext {{
                        visibility: visible;
                        opacity: 1;
                    }}

                    .inline {{
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        font-weight: bold;
                        font-size: 18px;
                    }}
                    </style>

                    <div class="inline">
                        <div>Cenário: {cenario.upper()}</div>
                        <span class="tooltip">ℹ️
                            <span class="tooltiptext">{texto_tooltip}</span>
                        </span>
                    </div>
                """, unsafe_allow_html=True)


                if not df_filtrado.empty:
                    cidades_geojson = [f["id"] for f in geojson["features"]]
                    df_mapa = pd.DataFrame({"cidade": cidades_geojson})
                    df_merge = df_mapa.merge(df_filtrado[["cidade", "valor", "diferenca_colorida"]], on="cidade", how="left")
                    df_merge["regiao_santa_maria"] = df_merge["cidade"].apply(lambda x: x in cidades_santa_maria)

                    df_merge["z"] = df_merge.apply(
                        lambda row: row["valor"] if row["regiao_santa_maria"] and pd.notna(row["valor"])
                        else (-9999 if not row["regiao_santa_maria"] else None),
                        axis=1
                    )

                    z_validos = df_merge["z"][(df_merge["z"] != -9999) & (pd.notna(df_merge["z"]))]
                    zmin = zmin_global
                    zmax = zmax_global

                    # [trecho acima permanece o mesmo até a criação do fig]

                    # Adiciona nome amigável da cidade
                    df_merge["cidade_amigavel"] = df_merge["cidade"].apply(
                        lambda x: nomes_cidades_amigaveis.get(x, x.title())
                    )

                    # Arredonda os valores
                    df_merge["valor_formatado"] = df_merge["valor"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "Sem dado")

                    # Define customdata para hover
                    df_merge["customdata"] = list(zip(df_merge["cidade_amigavel"], df_merge["valor_formatado"], df_merge["diferenca_colorida"]))

                    fig = go.Figure()

                    fig.add_trace(go.Choropleth(
                        geojson=geojson_sm,
                        locations=df_merge["cidade"],
                        z=df_merge["z"],
                        featureidkey="id",
                        colorscale=[
                            [0.0, "#B4B4B4"],
                            [0.2, "#d61515"],
                            [0.4, "#fa992a"],
                            [0.6, "#ffe605"],
                            [0.8, "#125ED1"],
                            [1.0, "#021835"]
                        ],
                        colorbar=dict(
                            title=nomes_variaveis_amigaveis.get(variavel, variavel.replace("_", " ").capitalize()),
                            thickness=10,
                            len=0.9,
                            x=0.90
                        ),
                        zmin=zmin,
                        zmax=zmax,
                        marker_line_color="white",
                        marker_line_width=0.5,
                        name="Produção",
                        customdata=df_merge["customdata"],
                        hovertemplate="<b>%{customdata[0]}</b>" + f"<br>{nomes_variaveis_amigaveis.get(variavel)}:</br>" + "%{customdata[1]:.2f}</br>" + "Desvio em relação a média histórica:<br> %{customdata[2]}</br>" + "<extra></extra>",
                    ))

                    fig.add_trace(go.Scattergeo(
                        lon=list(lons),
                        lat=list(lats),
                        mode='lines',
                        line=dict(width=1, color='white'),
                        name='Borda Região Santa Maria',
                        hoverinfo='skip'
                    ))

                    fig.update_geos(fitbounds="locations", visible=False)
                    fig.update_layout(
                        geo=dict(
                            bgcolor="rgba(0,0,0,0)",
                            lakecolor="rgba(0,0,0,0)",
                            showland=True,
                            landcolor="rgba(0,0,0,0)",
                            showlakes=False,
                            showrivers=False,
                            showcoastlines=False,
                            showcountries=False,
                            showsubunits=False,
                            showframe=False,
                            fitbounds="locations"
                        ),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin={"r":0,"t":30,"l":0,"b":0},
                        height=400,
                    )

                    st.plotly_chart(fig, use_container_width=True, key=f"mapa_{cenario}_{cidade_selecionada}_{safra}_{modelo}",config={"scrollZoom": False})
    st.markdown("---")

    # Permite selecionar múltiplos cenários
    cenarios_escolhidos = st.multiselect(
        "Selecione um ou mais cenários",
        ["ssp126", "ssp245", "ssp370", "ssp585"],
        default=["ssp126", "ssp245", "ssp370", "ssp585"]  # já mostrar todos por padrão
    )

    # Filtra o dataframe para os cenários escolhidos
    df_tabela = df_tabela[df_tabela["cenario"].isin(cenarios_escolhidos)].copy()

    # Formata a coluna 'valor' para mostrar 2 casas decimais (como string)
    df_tabela["valor"] = df_tabela["valor"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "")

    # Mostra os cenários escolhidos na legenda
    cenarios_texto = ", ".join(cenarios_escolhidos) if cenarios_escolhidos else "Nenhum cenário selecionado"
    st.markdown(f"### Tabela de Dados Filtrados - Cenários: {cenarios_texto}")

    # Mostra a tabela filtrada sempre
    st.dataframe(df_tabela.reset_index(drop=True))

    footer = """
    <div style='
        text-align: center;
        font-size: 14px;
        color: #ccc;
        padding: 20px 10px 10px 10px;
        border-top: 1px solid #444;
    '>
        Desenvolvido por <strong>Luiz Felipe Cavalheiro dos Santos</strong> <br>
        <a href="mailto:lfsantos@inf.ufsm.br" style="color: #ccc;">lfsantos@inf.ufsm.br</a> <br>
        Trabalho de Conclusão de Curso – Ciência da Computação <br>
        Universidade Federal de Santa Maria – UFSM <br>
        Orientador: <strong><a href="https://www-usr.inf.ufsm.br/~joaquim" target="_blank" style="color: #ccc;">Joaquim Vinicius Carvalho Assunção</a></strong><br>
        Ano: 2025 <br>
        <a href="https://github.com/luizfelipecavalheiro/previsao-agricola-regiao-geografica-intermediaria-sm" target="_blank" style="color: #ccc;">Repositório no GitHub</a>
    </div>
    """

    # Renderizar o footer
    st.markdown(footer, unsafe_allow_html=True)

    # Eliminar qualquer espaço extra abaixo do footer
    st.markdown("<style>body { margin-bottom: 0 !important; }</style>", unsafe_allow_html=True)







