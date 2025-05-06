import tkinter as tk
from tkinter import messagebox
import networkx as nx
import matplotlib.pyplot as plt
from sql_parser import SQLParser, GrafoDeOperadores

# para criar a interface gráfica, foi utilizado o Tkinter
# e para a exibição visual do grafo, foi utilizado networkx e matplotlib.pyplot
# para testar, usar o comando:
# python interface.py

# primeiro, o usuário insere uma consulta SQL na área de texto "campo_input_sql"
# ao clicar no botão Executar Consulta, a função processar_consulta() é chamada processando a consulta SQL
# a consulta inserida é exibida na interface gráfica
# após o processamento, o código gera e exibe a álgebra relacional
# o grafo de operadores que foi criado a partir da consulta SQL é exibido
# o plano de execução é exibido na interface gráfica

# Função para processar a consulta e exibir os resultados
def processar_consulta():
    sql = campo_input_sql.get("1.0", tk.END).strip()
    if not sql:
        messagebox.showerror("Erro", "Por favor, insira uma consulta SQL.")
        return
    
    try:
        # Cria o parser com a consulta
        parser = SQLParser(sql)
        parser.parse()
        parser.validate_fields()

        # Gerar álgebra relacional
        algebra_relacional = parser.gerar_algebra_relacional()

        # Criar grafo de operadores
        grafo = GrafoDeOperadores(parser)

        # Exibir o resultado na interface gráfica
        campo_consulta_original.delete("1.0", tk.END)
        campo_consulta_original.insert(tk.END, sql)

        campo_algebra_relacional.delete("1.0", tk.END)
        campo_algebra_relacional.insert(tk.END, algebra_relacional)

        grafo_exibido = "\n".join(str(op) for op in grafo.nos)
        campo_grafo_operadores.delete("1.0", tk.END)
        campo_grafo_operadores.insert(tk.END, grafo_exibido)

        plano_execucao = "\n".join(str(op) for op in grafo.nos[::-1])  # Plano de execução é a ordem inversa
        campo_plano_execucao.delete("1.0", tk.END)
        campo_plano_execucao.insert(tk.END, plano_execucao)

        # Visualizar grafo e otimizações
        visualizar_grafo(grafo)
        # essa função usa o NetworkX para criar um grafo direcionado e o Matplotlib para desenhar ele

    except ValueError as e:
        messagebox.showerror("Erro", str(e))

def visualizar_grafo(grafo):
    # Criar um grafo de NetworkX
    G = nx.DiGraph()

    # Adicionar nós ao grafo
    for i, op in enumerate(grafo.nos):
        G.add_node(i, label=str(op))

    # Adicionar arestas (relações entre as operações)
    for i, op in enumerate(grafo.nos):
        for j, filho in enumerate(op.filhos):
            # Encontrar o índice do filho no grafo
            filho_index = grafo.nos.index(filho)
            G.add_edge(i, filho_index)

    # Definir o layout do grafo
    pos = nx.spring_layout(G, seed=42)  # Define a posição dos nós de forma automática

    # Desenhar o grafo
    plt.figure(figsize=(10, 6))
    nx.draw(G, pos, with_labels=True, node_size=2000, node_color='skyblue', font_size=10, font_weight='bold', arrows=True)

    # Adicionar rótulos aos nós
    labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(G, pos, labels, font_size=8)

    # Destacar otimizações
    otimizado = [0, 1]  # Exemplo: vamos destacar as duas primeiras operações como "otimizadas"
    nx.draw_networkx_nodes(G, pos, nodelist=otimizado, node_color='lightgreen', node_size=3000)

    # Exibir o gráfico
    plt.title("Grafo de Operadores e Otimizações")
    plt.show()

# Configuração da interface gráfica
root = tk.Tk()
root.title("SQL Query Processor")

# Campo de entrada para a consulta SQL
campo_input_sql = tk.Text(root, height=6, width=50)
campo_input_sql.pack(pady=10)

# Botão para processar a consulta
botao_processar = tk.Button(root, text="Executar Consulta", command=processar_consulta)
botao_processar.pack(pady=10)

# Área para exibir a consulta original
label_consulta_original = tk.Label(root, text="Consulta Original:")
label_consulta_original.pack()

campo_consulta_original = tk.Text(root, height=4, width=50)
campo_consulta_original.pack(pady=5)

# Área para exibir a álgebra relacional
label_algebra_relacional = tk.Label(root, text="Álgebra Relacional:")
label_algebra_relacional.pack()

campo_algebra_relacional = tk.Text(root, height=4, width=50)
campo_algebra_relacional.pack(pady=5)

# Área para exibir o grafo de operadores
label_grafo_operadores = tk.Label(root, text="Grafo de Operadores:")
label_grafo_operadores.pack()

campo_grafo_operadores = tk.Text(root, height=6, width=50)
campo_grafo_operadores.pack(pady=5)

# Área para exibir o plano de execução
label_plano_execucao = tk.Label(root, text="Plano de Execução:")
label_plano_execucao.pack()

campo_plano_execucao = tk.Text(root, height=6, width=50)
campo_plano_execucao.pack(pady=5)

# Rodar a interface gráfica
root.mainloop()
