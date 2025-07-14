import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# Ruta al archivo CSV
file_path = '/Users/macbookair/Desktop/caza2025/planilla-de-inscripción-de-establecimiento-particulares-2025-07-01.csv'

# Función para parsear las proporciones de machos y hembras
def parse_proportions(text):
    if pd.isna(text):
        return None, None

    text = text.lower().replace('%', '').replace(' ', '')
    
    # Try to find patterns like XmachosYhembras or X-Y or X Y
    match_m_h = re.search(r'(\d+)(?:machos|m)(\d+)(?:hembras|h)', text)
    match_h_m = re.search(r'(\d+)(?:hembras|h)(\d+)(?:machos|m)', text)
    match_dash = re.search(r'(\d+)-(\d+)', text)
    match_space = re.search(r'(\d+)\s*(\d+)', text) # Allow zero or more spaces

    males, females = None, None

    if match_m_h:
        males = int(match_m_h.group(1))
        females = int(match_m_h.group(2))
    elif match_h_m:
        females = int(match_h_m.group(1))
        males = int(match_h_m.group(2))
    elif match_dash:
        males = int(match_dash.group(1))
        females = int(match_dash.group(2))
    elif match_space:
        males = int(match_space.group(1))
        females = int(match_space.group(2))
    else:
        # Try to find single percentage and assume it's males
        match_single = re.search(r'^(\d+)$|^(\d+)(?:machos|m)$|^(\d+)(?:hembras|h)$|^(\d+)(?:ciervo|ciervos)$|^(\d+)(?:hembra|hembras)$|^(\d+)(?:macho|machos)$', text)
        if match_single:
            val = int(match_single.group(1) or match_single.group(2) or match_single.group(3) or match_single.group(4) or match_single.group(5) or match_single.group(6))
            if val <= 100: # Assume it's male percentage if it's a percentage
                males = val
                females = 100 - males
            # If it's a large number, it's probably not a percentage, so return None

    # Basic validation for percentages (allow some deviation from 100 for sum)
    if (males is not None and females is not None and
        0 <= males <= 100 and 0 <= females <= 100 and
        (males + females == 100 or abs(males + females - 100) < 5)):
        return males, females
    
    return None, None

# Categorize the proportions
def categorize_proportion(males, females):
    if males is None or females is None:
        return 'No especificado / Formato inválido'
    if males > females:
        return 'Más Machos'
    elif females > males:
        return 'Más Hembras'
    else:
        return 'Igual Proporción'

# Función para parsear la cantidad de ciervos furtivos
def parse_ciervos_furtivos(text):
    if pd.isna(text) or text.strip() == '':
        return 'No especificado'
    text = text.lower().strip()

    # Buscar números o rangos
    match_range = re.search(r'(\d+)\s*[-/]\s*(\d+)', text)
    match_number = re.search(r'^\s*(\d+)\s*$', text)

    if match_range:
        num1 = int(match_range.group(1))
        num2 = int(match_range.group(2))
        return (num1 + num2) / 2 # Promedio del rango
    elif match_number:
        return int(match_number.group(1))
    elif 'no se' in text or 'no lo se' in text or 'no sabria' in text or 'no se sabe' in text:
        return 'No se sabe'
    elif 'muy poco' in text or 'poco' in text:
        return 'Muy poco'
    elif 'varios' in text:
        return 'Varios'
    elif 'mas de' in text:
        num = re.search(r'mas de\s*(\d+)', text)
        if num: return f'> {num.group(1)}'
        return 'Más de'
    elif 'entre' in text:
        num1 = re.search(r'entre\s*(\d+)\s*y\s*(\d+)', text)
        if num1: return f'{num1.group(1)}-{num1.group(2)}'
        return 'Entre'
    elif 'aprox' in text:
        num = re.search(r'(\d+)\s*aprox', text)
        if num: return int(num.group(1))
        return 'Aproximado'
    elif 'erratico' in text:
        return 'Errático'
    elif 'no poseemos estimaciones' in text:
        return 'No poseemos estimaciones'
    elif 'no es permanente' in text:
        return 'No es permanente'
    elif 'no me afecta' in text:
        return 'No me afecta'
    elif 'no' == text:
        return 'No'
    
    return 'Otro' # Para cualquier otra entrada no reconocida

# Función para parsear la cantidad de jabalí europeo
def parse_jabali_europeo(text):
    if pd.isna(text) or text.strip() == '':
        return 'No especificado'
    text = text.lower().strip()

    # Buscar números o rangos
    match_range = re.search(r'(\d+)\s*[-/]\s*(\d+)', text)
    match_number = re.search(r'^\s*(\d+)\s*$', text)

    if match_range:
        num1 = int(match_range.group(1))
        num2 = int(match_range.group(2))
        return (num1 + num2) / 2 # Promedio del rango
    elif match_number:
        return int(match_number.group(1))
    elif 'no se' in text or 'no lo se' in text or 'no sabria' in text or 'no se sabe' in text:
        return 'No se sabe'
    elif 'muchos' in text:
        return 'Muchos'
    elif 'aprox' in text:
        num = re.search(r'(\d+)\s*aprox', text)
        if num: return int(num.group(1))
        return 'Aproximado'
    elif 'muy poco' in text:
        return 'Muy poco'
    elif 'no' == text:
        return 'No'
    
    return 'Otro' # Para cualquier otra entrada no reconocida

# Función para parsear la población de jabalí en 3 años
def parse_jabali_poblacion_3_anos(text):
    if pd.isna(text) or text.strip() == '':
        return 'No especificado'
    text = text.lower().strip()

    if 'aumento' in text or 'aumentó' in text:
        return 'Aumentó'
    elif 'disminuyo' in text or 'disminuyó' in text:
        return 'Disminuyó'
    elif 'se mantuvo estable' in text:
        return 'Se mantuvo estable'
    else:
        return 'Otro'


# Leer el archivo CSV en un DataFrame de pandas
try:
    df = pd.read_csv(file_path)

    # --- Procesamiento y Gráfico de Establecimientos por Departamento (Plotly) ---
    columna_departamento = 'Departamento donde se ubica el establecimiento'

    # Unificar las entradas de departamentos
    df[columna_departamento] = df[columna_departamento].replace({
        'ALUMINE': 'Alumine',
        'Departamento Aluminé': 'Alumine',
        'COLLON CURA': 'Collon cura',
        'Collón Curá': 'Collon cura',
        'Lácar': 'Lacar',
        'lacar': 'Lacar',
        'Lacar - Huiliches': 'Lacar',
        'huiliches': 'Huiliches',
        'HUILICHES': 'Huiliches',
        'Catán Lil': 'Catan Lil',
        'catan lil': 'Catan Lil',
        'Lacar - los lagos': 'Lacar'
    })

    # Contar la cantidad de establecimientos por departamento
    conteo_por_departamento = df[columna_departamento].value_counts().reset_index()
    conteo_por_departamento.columns = ['Departamento', 'Cantidad']

    # Imprimir los resultados en la consola
    print("Cantidad de establecimientos por departamento:")
    print(conteo_por_departamento)

    # Generar un gráfico de barras interactivo con Plotly
    fig_departamentos = px.bar(conteo_por_departamento, x='Departamento', y='Cantidad',
                               title='Cantidad de Establecimientos por Departamento',
                               labels={'Departamento': 'Departamento', 'Cantidad': 'Número de Establecimientos'},
                               text='Cantidad') # Mostrar el valor en la barra
    fig_departamentos.update_traces(textposition='outside')
    fig_departamentos.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    fig_departamentos.update_xaxes(tickangle=45)

    # Guardar el gráfico de departamentos como HTML
    grafico_departamentos_path = '/Users/macbookair/Downloads/establecimientos_por_departamento.html'
    fig_departamentos.write_html(grafico_departamentos_path)
    print(f"\nGráfico de departamentos guardado en: {grafico_departamentos_path}")

    # --- Procesamiento y Gráfico de Torta de Especies de Caza (Plotly) ---
    columna_especies = 'Marque el casillero de la especies para las que solicita la práctica de caza. mayor.  Estas especies son exclusivamente para caza en establecimientos debidamente inscriptos como Criaderos de Fauna Silvestre y habilitados como Áreas de Caza Mayor.'

    # Limpiar y dividir las especies
    especies_list = df[columna_especies].fillna('').str.split(',').explode()
    especies_list = especies_list.str.strip() # Eliminar espacios en blanco
    especies_list = especies_list[especies_list != ''] # Eliminar entradas vacías

    # Contar la frecuencia de cada especie
    conteo_especies = especies_list.value_counts().reset_index()
    conteo_especies.columns = ['Especie', 'Cantidad']

    # Generar el gráfico de torta interactivo con Plotly
    fig_especies = px.pie(conteo_especies, values='Cantidad', names='Especie',
                          title='Distribución de Especies de Caza Solicitadas')
    fig_especies.update_traces(textposition='inside', textinfo='percent+label')

    # Guardar el gráfico de torta como HTML
    grafico_especies_path = '/Users/macbookair/Downloads/especies_caza_torta.html'
    fig_especies.write_html(grafico_especies_path)
    print(f"Gráfico de especies de caza guardado en: {grafico_especies_path}")

    # --- Procesamiento y Gráfico de Torta de Ciervos en los Últimos Cinco Años (Plotly) ---
    columna_ciervos_5_anos = 'En los últimos cinco años, el número de ciervos en su campo'

    # Contar la frecuencia de cada respuesta
    conteo_ciervos_5_anos = df[columna_ciervos_5_anos].value_counts().reset_index()
    conteo_ciervos_5_anos.columns = ['Respuesta', 'Cantidad']

    # Generar el gráfico de torta interactivo con Plotly
    fig_ciervos_5_anos = px.pie(conteo_ciervos_5_anos, values='Cantidad', names='Respuesta',
                                title='Cambio en el Número de Ciervos en los Últimos Cinco Años')
    fig_ciervos_5_anos.update_traces(textposition='inside', textinfo='percent+label')

    # Guardar el gráfico de torta como HTML
    grafico_ciervos_5_anos_path = '/Users/macbookair/Downloads/ciervos_ultimos_cinco_anos_torta.html'
    fig_ciervos_5_anos.write_html(grafico_ciervos_5_anos_path)
    print(f"Gráfico de ciervos en los últimos cinco años guardado en: {grafico_ciervos_5_anos_path}")

    # --- Procesamiento y Gráfico de Torta de Proporción Machos/Hembras (Plotly) ---
    columna_proporcion = 'Con respecto a la proporción existente entre machos y hembras, podría indicar los porcentajes que observa de Machos y Hembras. '

    # Aplicar la función de parseo
    df[['Parsed_Males', 'Parsed_Females']] = df[columna_proporcion].apply(lambda x: pd.Series(parse_proportions(x)))

    # Categorizar las proporciones
    df['Proportion_Category'] = df.apply(lambda row: categorize_proportion(row['Parsed_Males'], row['Parsed_Females']), axis=1)

    # Contar las categorías
    conteo_proporcion = df['Proportion_Category'].value_counts().reset_index()
    conteo_proporcion.columns = ['Categoría', 'Cantidad']

    # Generar el gráfico de torta interactivo con Plotly
    fig_proporcion = px.pie(conteo_proporcion, values='Cantidad', names='Categoría',
                            title='Proporción de Machos y Hembras Observada de Ciervos')
    fig_proporcion.update_traces(textposition='inside', textinfo='percent+label')

    # Guardar el gráfico de torta como HTML
    grafico_proporcion_path = '/Users/macbookair/Downloads/proporcion_machos_hembras.html'
    fig_proporcion.write_html(grafico_proporcion_path)
    print(f"Gráfico de proporción machos/hembras guardado en: {grafico_proporcion_path}")

    # --- Procesamiento y Gráfico de Barras de Ambientes Preferenciales (Plotly) ---
    columna_ambientes = 'En cuanto a los ambientes que ocupan de manera preferencial los ciervos, seleccione los ambientes donde se encuentran presentes.'

    # Limpiar y dividir los ambientes
    ambientes_list = df[columna_ambientes].fillna('').str.split(',').explode()
    ambientes_list = ambientes_list.str.strip() # Eliminar espacios en blanco
    ambientes_list = ambientes_list[ambientes_list != ''] # Eliminar entradas vacías

    # Contar la frecuencia de cada ambiente
    conteo_ambientes = ambientes_list.value_counts().reset_index()
    conteo_ambientes.columns = ['Ambiente', 'Cantidad']

    # Generar el gráfico de barras interactivo con Plotly
    fig_ambientes = px.bar(conteo_ambientes, x='Ambiente', y='Cantidad',
                           title='Ambientes Preferenciales de Ciervos',
                           labels={'Ambiente': 'Ambiente', 'Cantidad': 'Número de Menciones'},
                           text='Cantidad') # Mostrar el valor en la barra
    fig_ambientes.update_traces(textposition='outside')
    fig_ambientes.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    fig_ambientes.update_xaxes(tickangle=45)

    # Guardar el gráfico de barras como HTML
    grafico_ambientes_path = '/Users/macbookair/Downloads/ambientes_preferenciales_ciervos.html'
    fig_ambientes.write_html(grafico_ambientes_path)
    print(f"Gráfico de ambientes preferenciales guardado en: {grafico_ambientes_path}")

    # --- Procesamiento y Gráfico de Barras de Ciervos Furtivos (Plotly) ---
    columna_furtivos = 'Podría estimar el número de ciervos que son extraídos de su establecimiento todos los años, por los cazadores furtivos?'

    # Aplicar la función de parseo
    df['Ciervos_Furtivos_Parsed'] = df[columna_furtivos].apply(parse_ciervos_furtivos)

    # Contar las categorías o valores numéricos
    conteo_furtivos = df['Ciervos_Furtivos_Parsed'].value_counts().reset_index()
    conteo_furtivos.columns = ['Estimación', 'Cantidad']

    # Ordenar por Cantidad si es un gráfico de barras de categorías
    conteo_furtivos = conteo_furtivos.sort_values(by='Cantidad', ascending=False)

    fig_furtivos = px.bar(conteo_furtivos, x='Estimación', y='Cantidad',
                          title='Estimación de Ciervos Extraídos por Cazadores Furtivos',
                          labels={'Estimación': 'Estimación de Ciervos', 'Cantidad': 'Número de Menciones'},
                          text='Cantidad')
    fig_furtivos.update_traces(textposition='outside')
    fig_furtivos.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    fig_furtivos.update_xaxes(tickangle=45)

    # Guardar el gráfico de barras como HTML
    grafico_furtivos_path = '/Users/macbookair/Downloads/ciervos_furtivos_bar.html'
    fig_furtivos.write_html(grafico_furtivos_path)
    print(f"Gráfico de ciervos furtivos guardado en: {grafico_furtivos_path}")

    # --- Procesamiento y Gráfico de Torta de Jabalí Europeo (Plotly) ---
    columna_jabali = 'Indique en forma aproximada, la cantidad de ejemplares de jabalí europeo que alberga su establecimiento.'

    # Aplicar la función de parseo
    df['Jabali_Europeo_Parsed'] = df[columna_jabali].apply(parse_jabali_europeo)

    # Contar las categorías o valores numéricos
    conteo_jabali = df['Jabali_Europeo_Parsed'].value_counts().reset_index()
    conteo_jabali.columns = ['Cantidad de Jabalí', 'Frecuencia']

    # Generar el gráfico de torta interactivo con Plotly
    fig_jabali = px.pie(conteo_jabali, values='Frecuencia', names='Cantidad de Jabalí',
                        title='Cantidad de Ejemplares de Jabalí Europeo')
    fig_jabali.update_traces(textposition='inside', textinfo='percent+label')

    # Guardar el gráfico de torta como HTML
    grafico_jabali_path = '/Users/macbookair/Downloads/jabali_europeo_torta.html'
    fig_jabali.write_html(grafico_jabali_path)
    print(f"Gráfico de jabalí europeo guardado en: {grafico_jabali_path}")

    # --- Procesamiento y Gráfico de Torta de Población de Jabalí en 3 Años (Plotly) ---
    columna_jabali_3_anos = 'En los últimos tres años, la población de jabalí europeo:'

    # Aplicar la función de parseo
    df['Jabali_Poblacion_3_Anos_Parsed'] = df[columna_jabali_3_anos].apply(parse_jabali_poblacion_3_anos)

    # Contar las categorías
    conteo_jabali_3_anos = df['Jabali_Poblacion_3_Anos_Parsed'].value_counts().reset_index()
    conteo_jabali_3_anos.columns = ['Cambio en Población', 'Frecuencia']

    # Generar el gráfico de torta interactivo con Plotly
    fig_jabali_3_anos = px.pie(conteo_jabali_3_anos, values='Frecuencia', names='Cambio en Población',
                               title='Cambio en la Población de Jabalí Europeo en los Últimos 3 Años')
    fig_jabali_3_anos.update_traces(textposition='inside', textinfo='percent+label')

    # Guardar el gráfico de torta como HTML
    grafico_jabali_3_anos_path = '/Users/macbookair/Downloads/jabali_poblacion_3_anos_torta.html'
    fig_jabali_3_anos.write_html(grafico_jabali_3_anos_path)
    print(f"Gráfico de población de jabalí en 3 años guardado en: {grafico_jabali_3_anos_path}")

except FileNotFoundError:
    print(f"Error: No se encontró el archivo en la ruta: {file_path}")
except KeyError:
    print(f"Error: Una de las columnas especificadas no se encontró en el archivo CSV.")
# Función para parsear la cantidad de pumas
def parse_cantidad_pumas(text):
    if pd.isna(text) or text.strip() == '':
        return 'No especificado'
    text = text.lower().strip()

    match_number = re.search(r'(\d+)', text)
    if match_number:
        return int(match_number.group(1))
    elif 'no se' in text or 'no lo se' in text or 'no sabria' in text or 'no se sabe' in text:
        return 'No se sabe'
    elif 'muchos' in text:
        return 'Muchos'
    elif 'pocos' in text:
        return 'Pocos'
    elif 'aprox' in text:
        num = re.search(r'(\d+)\s*aprox', text)
        if num: return int(num.group(1))
        return 'Aproximado'
    elif 'no' == text:
        return 'No'
    return 'Otro'

# Función para parsear la población de pumas en 3 años
def parse_poblacion_pumas_3_anos(text):
    if pd.isna(text) or text.strip() == '':
        return 'No especificado'
    text = text.lower().strip()

    if 'aumento' in text or 'aumentó' in text:
        return 'Aumentó'
    elif 'disminuyo' in text or 'disminuyó' in text:
        return 'Disminuyó'
    elif 'se mantuvo estable' in text:
        return 'Se mantuvo estable'
    else:
        return 'Otro'

# Función para parsear daños provocados por puma
def parse_danos_puma(text):
    if pd.isna(text) or text.strip() == '':
        return 'No especificado'
    text = text.lower().strip()

    if 'nada' in text or 'no' in text or 'ninguno' in text:
        return 'Ninguno'
    elif 'ovejas' in text or 'corderos' in text or 'lanares' in text:
        return 'Ovejas/Lanares'
    elif 'vacunos' in text or 'terneros' in text or 'vacas' in text:
        return 'Vacunos'
    elif 'potrillos' in text or 'caballos' in text:
        return 'Potrillos/Caballos'
    elif 'choiques' in text:
        return 'Choiques'
    elif 'ciervos' in text:
        return 'Ciervos'
    elif 'varios' in text or 'diversos' in text:
        return 'Varios tipos'
    return 'Otro'


# Leer el archivo CSV en un DataFrame de pandas
try:
    df = pd.read_csv(file_path)

    # --- Procesamiento y Gráfico de Establecimientos por Departamento (Plotly) ---
    columna_departamento = 'Departamento donde se ubica el establecimiento'

    # Unificar las entradas de departamentos
    df[columna_departamento] = df[columna_departamento].replace({
        'ALUMINE': 'Alumine',
        'Departamento Aluminé': 'Alumine',
        'COLLON CURA': 'Collon cura',
        'Collón Curá': 'Collon cura',
        'Lácar': 'Lacar',
        'lacar': 'Lacar',
        'Lacar - Huiliches': 'Lacar',
        'huiliches': 'Huiliches',
        'HUILICHES': 'Huiliches',
        'Catán Lil': 'Catan Lil',
        'catan lil': 'Catan Lil',
        'Lacar - los lagos': 'Lacar'
    })

    # Contar la cantidad de establecimientos por departamento
    conteo_por_departamento = df[columna_departamento].value_counts().reset_index()
    conteo_por_departamento.columns = ['Departamento', 'Cantidad']

    # Imprimir los resultados en la consola
    print("Cantidad de establecimientos por departamento:")
    print(conteo_por_departamento)

    # Generar un gráfico de barras interactivo con Plotly
    fig_departamentos = px.bar(conteo_por_departamento, x='Departamento', y='Cantidad',
                               title='Cantidad de Establecimientos por Departamento',
                               labels={'Departamento': 'Departamento', 'Cantidad': 'Número de Establecimientos'},
                               text='Cantidad') # Mostrar el valor en la barra
    fig_departamentos.update_traces(textposition='outside')
    fig_departamentos.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    fig_departamentos.update_xaxes(tickangle=45)

    # Guardar el gráfico de departamentos como HTML
    grafico_departamentos_path = '/Users/macbookair/Desktop/caza2025/establecimientos_por_departamento.html'
    fig_departamentos.write_html(grafico_departamentos_path)
    print(f"\nGráfico de departamentos guardado en: {grafico_departamentos_path}")

    # --- Procesamiento y Gráfico de Torta de Especies de Caza (Plotly) ---
    columna_especies = 'Marque el casillero de la especies para las que solicita la práctica de caza. mayor.  Estas especies son exclusivamente para caza en establecimientos debidamente inscriptos como Criaderos de Fauna Silvestre y habilitados como Áreas de Caza Mayor.'

    # Limpiar y dividir las especies
    especies_list = df[columna_especies].fillna('').str.split(',').explode()
    especies_list = especies_list.str.strip() # Eliminar espacios en blanco
    especies_list = especies_list[especies_list != ''] # Eliminar entradas vacías

    # Contar la frecuencia de cada especie
    conteo_especies = especies_list.value_counts().reset_index()
    conteo_especies.columns = ['Especie', 'Cantidad']

    # Generar el gráfico de torta interactivo con Plotly
    fig_especies = px.pie(conteo_especies, values='Cantidad', names='Especie',
                          title='Distribución de Especies de Caza Solicitadas')
    fig_especies.update_traces(textposition='inside', textinfo='percent+label')

    # Guardar el gráfico de torta como HTML
    grafico_especies_path = '/Users/macbookair/Desktop/caza2025/especies_caza_torta.html'
    fig_especies.write_html(grafico_especies_path)
    print(f"Gráfico de especies de caza guardado en: {grafico_especies_path}")

    # --- Procesamiento y Gráfico de Torta de Ciervos en los Últimos Cinco Años (Plotly) ---
    columna_ciervos_5_anos = 'En los últimos cinco años, el número de ciervos en su campo'

    # Contar la frecuencia de cada respuesta
    conteo_ciervos_5_anos = df[columna_ciervos_5_anos].value_counts().reset_index()
    conteo_ciervos_5_anos.columns = ['Respuesta', 'Cantidad']

    # Generar el gráfico de torta interactivo con Plotly
    fig_ciervos_5_anos = px.pie(conteo_ciervos_5_anos, values='Cantidad', names='Respuesta',
                                title='Cambio en el Número de Ciervos en los Últimos Cinco Años')
    fig_ciervos_5_anos.update_traces(textposition='inside', textinfo='percent+label')

    # Guardar el gráfico de torta como HTML
    grafico_ciervos_5_anos_path = '/Users/macbookair/Desktop/caza2025/ciervos_ultimos_cinco_anos_torta.html'
    fig_ciervos_5_anos.write_html(grafico_ciervos_5_anos_path)
    print(f"Gráfico de ciervos en los últimos cinco años guardado en: {grafico_ciervos_5_anos_path}")

    # --- Procesamiento y Gráfico de Torta de Proporción Machos/Hembras (Plotly) ---
    columna_proporcion = 'Con respecto a la proporción existente entre machos y hembras, podría indicar los porcentajes que observa de Machos y Hembras. '

    # Aplicar la función de parseo
    df[['Parsed_Males', 'Parsed_Females']] = df[columna_proporcion].apply(lambda x: pd.Series(parse_proportions(x)))

    # Categorizar las proporciones
    df['Proportion_Category'] = df.apply(lambda row: categorize_proportion(row['Parsed_Males'], row['Parsed_Females']), axis=1)

    # Contar las categorías
    conteo_proporcion = df['Proportion_Category'].value_counts().reset_index()
    conteo_proporcion.columns = ['Categoría', 'Cantidad']

    # Generar el gráfico de torta interactivo con Plotly
    fig_proporcion = px.pie(conteo_proporcion, values='Cantidad', names='Categoría',
                            title='Proporción de Machos y Hembras Observada de Ciervos')
    fig_proporcion.update_traces(textposition='inside', textinfo='percent+label')

    # Guardar el gráfico de torta como HTML
    grafico_proporcion_path = '/Users/macbookair/Desktop/caza2025/proporcion_machos_hembras.html'
    fig_proporcion.write_html(grafico_proporcion_path)
    print(f"Gráfico de proporción machos/hembras guardado en: {grafico_proporcion_path}")

    # --- Procesamiento y Gráfico de Barras de Ambientes Preferenciales (Plotly) ---
    columna_ambientes = 'En cuanto a los ambientes que ocupan de manera preferencial los ciervos, seleccione los ambientes donde se encuentran presentes.'

    # Limpiar y dividir los ambientes
    ambientes_list = df[columna_ambientes].fillna('').str.split(',').explode()
    ambientes_list = ambientes_list.str.strip() # Eliminar espacios en blanco
    ambientes_list = ambientes_list[ambientes_list != ''] # Eliminar entradas vacías

    # Contar la frecuencia de cada ambiente
    conteo_ambientes = ambientes_list.value_counts().reset_index()
    conteo_ambientes.columns = ['Ambiente', 'Cantidad']

    # Generar el gráfico de barras interactivo con Plotly
    fig_ambientes = px.bar(conteo_ambientes, x='Ambiente', y='Cantidad',
                           title='Ambientes Preferenciales de Ciervos',
                           labels={'Ambiente': 'Ambiente', 'Cantidad': 'Número de Menciones'},
                           text='Cantidad') # Mostrar el valor en la barra
    fig_ambientes.update_traces(textposition='outside')
    fig_ambientes.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    fig_ambientes.update_xaxes(tickangle=45)

    # Guardar el gráfico de barras como HTML
    grafico_ambientes_path = '/Users/macbookair/Desktop/caza2025/ambientes_preferenciales_ciervos.html'
    fig_ambientes.write_html(grafico_ambientes_path)
    print(f"Gráfico de ambientes preferenciales guardado en: {grafico_ambientes_path}")

    # --- Procesamiento y Gráfico de Barras de Ciervos Furtivos (Plotly) ---
    columna_furtivos = 'Podría estimar el número de ciervos que son extraídos de su establecimiento todos los años, por los cazadores furtivos?'

    # Aplicar la función de parseo
    df['Ciervos_Furtivos_Parsed'] = df[columna_furtivos].apply(parse_ciervos_furtivos)

    # Contar las categorías o valores numéricos
    conteo_furtivos = df['Ciervos_Furtivos_Parsed'].value_counts().reset_index()
    conteo_furtivos.columns = ['Estimación', 'Cantidad']

    # Ordenar por Cantidad si es un gráfico de barras de categorías
    conteo_furtivos = conteo_furtivos.sort_values(by='Cantidad', ascending=False)

    fig_furtivos = px.bar(conteo_furtivos, x='Estimación', y='Cantidad',
                          title='Estimación de Ciervos Extraídos por Cazadores Furtivos',
                          labels={'Estimación': 'Estimación de Ciervos', 'Cantidad': 'Número de Menciones'},
                          text='Cantidad')
    fig_furtivos.update_traces(textposition='outside')
    fig_furtivos.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    fig_furtivos.update_xaxes(tickangle=45)

    # Guardar el gráfico de barras como HTML
    grafico_furtivos_path = '/Users/macbookair/Desktop/caza2025/ciervos_furtivos_bar.html'
    fig_furtivos.write_html(grafico_furtivos_path)
    print(f"Gráfico de ciervos furtivos guardado en: {grafico_furtivos_path}")

    # --- Procesamiento y Gráfico de Torta de Jabalí Europeo (Plotly) ---
    columna_jabali = 'Indique en forma aproximada, la cantidad de ejemplares de jabalí europeo que alberga su establecimiento.'

    # Aplicar la función de parseo
    df['Jabali_Europeo_Parsed'] = df[columna_jabali].apply(parse_jabali_europeo)

    # Contar las categorías o valores numéricos
    conteo_jabali = df['Jabali_Europeo_Parsed'].value_counts().reset_index()
    conteo_jabali.columns = ['Cantidad de Jabalí', 'Frecuencia']

    # Generar el gráfico de torta interactivo con Plotly
    fig_jabali = px.pie(conteo_jabali, values='Frecuencia', names='Cantidad de Jabalí',
                        title='Cantidad de Ejemplares de Jabalí Europeo')
    fig_jabali.update_traces(textposition='inside', textinfo='percent+label')

    # Guardar el gráfico de torta como HTML
    grafico_jabali_path = '/Users/macbookair/Desktop/caza2025/jabali_europeo_torta.html'
    fig_jabali.write_html(grafico_jabali_path)
    print(f"Gráfico de jabalí europeo guardado en: {grafico_jabali_path}")

    # --- Procesamiento y Gráfico de Torta de Población de Jabalí en 3 Años (Plotly) ---
    columna_jabali_3_anos = 'En los últimos tres años, la población de jabalí europeo:'

    # Aplicar la función de parseo
    df['Jabali_Poblacion_3_Anos_Parsed'] = df[columna_jabali_3_anos].apply(parse_jabali_poblacion_3_anos)

    # Contar las categorías
    conteo_jabali_3_anos = df['Jabali_Poblacion_3_Anos_Parsed'].value_counts().reset_index()
    conteo_jabali_3_anos.columns = ['Cambio en Población', 'Frecuencia']

    # Generar el gráfico de torta interactivo con Plotly
    fig_jabali_3_anos = px.pie(conteo_jabali_3_anos, values='Frecuencia', names='Cambio en Población',
                               title='Cambio en la Población de Jabalí Europeo en los Últimos 3 Años')
    fig_jabali_3_anos.update_traces(textposition='inside', textinfo='percent+label')

    # Guardar el gráfico de torta como HTML
    grafico_jabali_3_anos_path = '/Users/macbookair/Desktop/caza2025/jabali_poblacion_3_anos_torta.html'
    fig_jabali_3_anos.write_html(grafico_jabali_3_anos_path)
    print(f"Gráfico de población de jabalí en 3 años guardado en: {grafico_jabali_3_anos_path}")

    # --- Procesamiento y Gráfico de Torta de Cantidad de Pumas (Plotly) ---
    columna_cantidad_pumas = 'Si es posible, indique en forma aproximada, la cantidad de pumas que alberga su establecimiento.'

    df['Cantidad_Pumas_Parsed'] = df[columna_cantidad_pumas].apply(parse_cantidad_pumas)
    conteo_cantidad_pumas = df['Cantidad_Pumas_Parsed'].value_counts().reset_index()
    conteo_cantidad_pumas.columns = ['Cantidad de Pumas', 'Frecuencia']

    fig_cantidad_pumas = px.pie(conteo_cantidad_pumas, values='Frecuencia', names='Cantidad de Pumas',
                                title='Cantidad de Pumas que Alberga el Establecimiento')
    fig_cantidad_pumas.update_traces(textposition='inside', textinfo='percent+label')

    grafico_cantidad_pumas_path = '/Users/macbookair/Desktop/caza2025/pumas_cantidad_torta.html'
    fig_cantidad_pumas.write_html(grafico_cantidad_pumas_path)
    print(f"Gráfico de cantidad de pumas guardado en: {grafico_cantidad_pumas_path}")

    # --- Procesamiento y Gráfico de Barras de Población de Pumas en 3 Años (Plotly) ---
    columna_poblacion_pumas_3_anos = 'En los últimos tres años, la población de pumas'

    df['Poblacion_Pumas_3_Anos_Parsed'] = df[columna_poblacion_pumas_3_anos].apply(parse_poblacion_pumas_3_anos)
    conteo_poblacion_pumas_3_anos = df['Poblacion_Pumas_3_Anos_Parsed'].value_counts().reset_index()
    conteo_poblacion_pumas_3_anos.columns = ['Cambio en Población', 'Frecuencia']

    fig_poblacion_pumas_3_anos = px.bar(conteo_poblacion_pumas_3_anos, x='Cambio en Población', y='Frecuencia',
                                        title='Cambio en la Población de Pumas en los Últimos 3 Años',
                                        labels={'Cambio en Población': 'Cambio', 'Frecuencia': 'Número de Menciones'},
                                        text='Frecuencia')
    fig_poblacion_pumas_3_anos.update_traces(textposition='outside', width=0.3) # Ajustar el ancho de las barras aquí
    fig_poblacion_pumas_3_anos.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    fig_poblacion_pumas_3_anos.update_xaxes(tickangle=45)

    grafico_poblacion_pumas_3_anos_path = '/Users/macbookair/Desktop/caza2025/pumas_poblacion_bar.html'
    fig_poblacion_pumas_3_anos.write_html(grafico_poblacion_pumas_3_anos_path)
    print(f"Gráfico de población de pumas en 3 años guardado en: {grafico_poblacion_pumas_3_anos_path}")

    # --- Procesamiento y Gráfico de Barras de Daños Provocados por Puma (Plotly) ---
    columna_danos_puma = 'Si detectó daños provocados por puma durante el último año, cuantifique los mismos (tipo y cantidad de hacienda afectada): '

    df['Danos_Puma_Parsed'] = df[columna_danos_puma].apply(parse_danos_puma)
    conteo_danos_puma = df['Danos_Puma_Parsed'].value_counts().reset_index()
    conteo_danos_puma.columns = ['Tipo de Daño', 'Frecuencia']

    fig_danos_puma = px.bar(conteo_danos_puma, x='Tipo de Daño', y='Frecuencia',
                            title='Daños Provocados por Puma (Último Año)',
                            labels={'Tipo de Daño': 'Tipo de Hacienda Afectada', 'Frecuencia': 'Número de Menciones'},
                            text='Frecuencia')
    fig_danos_puma.update_traces(textposition='outside')
    fig_danos_puma.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    fig_danos_puma.update_xaxes(tickangle=45)

    grafico_danos_puma_path = '/Users/macbookair/Desktop/caza2025/pumas_danos_bar.html'
    fig_danos_puma.write_html(grafico_danos_puma_path)
    print(f"Gráfico de daños por puma guardado en: {grafico_danos_puma_path}")


except FileNotFoundError:
    print(f"Error: No se encontró el archivo en la ruta: {file_path}")
except KeyError as e:
    print(f"Error: Una de las columnas especificadas no se encontró en el archivo CSV: {e}")
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")
