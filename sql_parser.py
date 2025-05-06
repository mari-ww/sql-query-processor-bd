import re

# ================================================
#   METADADOS
# ================================================
# Dicionário com os nomes de tabelas e seus campos válidos,
# utilizado para validar os campos referenciados na SQL.
metadados = {
    "Categoria": ["idCategoria", "Descricao"],
    "Produto": ["idProduto", "Nome", "Descricao", "Preco", "QuantEstoque", "Categoria_idCategoria"],
    "TipoCliente": ["idTipoCliente", "Descricao"],
    "Cliente": ["idCliente", "Nome", "Email", "Nascimento", "Senha", "TipoCliente_idTipoCliente", "DataRegistro"],
    "TipoEndereco": ["idTipoEndereco", "Descricao"],
    "Endereco": ["idEndereco", "EnderecoPadrao", "Logradouro", "Numero", "Complemento", "Bairro", "Cidade", "UF", "CEP", "TipoEndereco_idTipoEndereco", "Cliente_idCliente"],
    "Telefone": ["Numero", "Cliente_idCliente"],
    "Status": ["idStatus", "Descricao"],
    "Pedido": ["idPedido", "Status_idStatus", "DataPedido", "ValorTotalPedido", "Cliente_idCliente"],
    "Pedido_has_Produto": ["idPedidoProduto", "Pedido_idPedido", "Produto_idProduto", "PrecoUnitario"]
}

# ================================================
#   CLASSE PRINCIPAL DO PARSER
# ================================================
# Responsabilidades dessa parte (feito):
# - Implementar o parser da consulta SQL com regex ✅
# - Separar cláusulas SELECT, FROM, JOIN, WHERE ✅
# - Validar existência de tabelas/campos ✅
# - Gerar álgebra relacional ✅
# - Mensagens de erro claras ✅
# - Código limpo e fácil de manter ✅
class SQLParser:
    def __init__(self, sql):
        self.sql = sql.strip()
        self.parsed = {}

    def parse(self):
        self.extract_select()
        self.extract_from()
        self.extract_joins()
        self.extract_where()
        return self.parsed

    # ================================================
    # SELECT
    # ================================================
    # Extrai os campos que estão após SELECT e antes do FROM.
    def extract_select(self):
        select_match = re.search(r"SELECT\s+(.*?)\s+FROM", self.sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            fields = [f.strip() for f in select_match.group(1).split(",")]
            self.parsed["SELECT"] = fields
        else:
            raise ValueError("Cláusula SELECT inválida ou ausente.")

    # ================================================
    # FROM
    # ================================================
    # Extrai a tabela base e seu alias, se houver.
    def extract_from(self):
        from_match = re.search(r"FROM\s+([a-zA-Z0-9_]+)(?:\s+([a-zA-Z0-9_]+))?", self.sql, re.IGNORECASE)
        if from_match:
            table, alias = from_match.groups()
            self.parsed["FROM"] = {"table": table, "alias": alias or table}
        else:
            raise ValueError("Cláusula FROM inválida ou ausente.")

    # ================================================
    # JOINs
    # ================================================
    # Extrai todas as cláusulas JOIN e suas condições ON.
    def extract_joins(self):
        join_matches = re.findall(
            r"JOIN\s+([a-zA-Z0-9_]+)\s+([a-zA-Z0-9_]+)?\s*ON\s+(.+?)(?=\s+(?:JOIN|WHERE|GROUP|ORDER|$))",
            self.sql, re.IGNORECASE | re.DOTALL
        )
        joins = []
        for table, alias, condition in join_matches:
            joins.append({
                "table": table,
                "alias": alias or table,
                "condition": condition.strip()
            })
        self.parsed["JOINS"] = joins

    # ================================================
    # WHERE
    # ================================================
    # Extrai a condição de filtragem (se houver).
    def extract_where(self):
        where_match = re.search(r"WHERE\s+(.+)", self.sql, re.IGNORECASE | re.DOTALL)
        if where_match:
            condition = where_match.group(1).strip()
            self.parsed["WHERE"] = condition

    # ================================================
    # VALIDAÇÃO DE CAMPOS
    # ================================================
    # Confere se todos os campos referenciados existem nas tabelas
    # e que os aliases estão corretamente utilizados.
    def validate_fields(self):
        aliases = {self.parsed['FROM']['alias']: self.parsed['FROM']['table']}
        for join in self.parsed.get("JOINS", []):
            aliases[join['alias']] = join['table']

        for field in self.parsed["SELECT"]:
            alias, col = field.split(".")
            if alias not in aliases or col not in metadados[aliases[alias]]:
                raise ValueError(f"Campo inválido: {field}")

        if "WHERE" in self.parsed:
            # Validação simples: verifica se os campos estão no formato alias.campo
            conditions = re.findall(r"([a-zA-Z_]+\.[a-zA-Z_]+)", self.parsed["WHERE"])
            for cond in conditions:
                alias, col = cond.split(".")
                if alias not in aliases or col not in metadados[aliases[alias]]:
                    raise ValueError(f"Campo inválido na cláusula WHERE: {cond}")

    # ================================================
    # GERAÇÃO DA ÁLGEBRA RELACIONAL
    # ================================================
    # Constrói a representação da consulta em álgebra relacional,
    # considerando projeção, seleção e junções.
    def gerar_algebra_relacional(self):
        from_clause = self.parsed['FROM']
        joins = self.parsed.get("JOINS", [])
        where = self.parsed.get("WHERE")
        select = self.parsed["SELECT"]

        base = from_clause['alias']
        for join in joins:
            base = f"({base} ⨝ {join['alias']})"

        if where:
            base = f"σ {where} ({base})"

        algebra = f"π {', '.join(select)} ({base})"
        return algebra

# ================================================
#   GRAFO DE OPERADORES
# ================================================

class Operador:
    def __init__(self, tipo, descricao, custo=1):
        self.tipo = tipo           
        self.descricao = descricao    
        self.filhos = []            
        self.custo = custo          

    def __repr__(self):
        return f"{self.tipo}: {self.descricao}"


class GrafoDeOperadores:
    def __init__(self, parser):
        self.parser = parser
        self.raiz = None
        self.nos = []
        self.alias_to_tabela = {}
        self.criar_grafo()

    def criar_grafo(self):
        dados = self.parser.parsed
        self.alias_to_tabela = {
            dados['FROM']['alias']: dados['FROM']['table']
        }

        for join in dados.get("JOINS", []):
            self.alias_to_tabela[join['alias']] = join['table']

        tabelas = {alias: Operador("Tabela", f"{alias} ({tabela})") for alias, tabela in self.alias_to_tabela.items()}

        atual = tabelas[dados['FROM']['alias']]
        self.nos.append(atual)

        for join in dados.get("JOINS", []):
            tabela_join = tabelas[join['alias']]
            self.nos.append(tabela_join)

            join_op = Operador("Junção", f"⨝ {join['condition']}", custo=self.estimar_custo(join['condition']))
            join_op.filhos = [atual, tabela_join]
            atual = join_op
            self.nos.append(join_op)

        if "WHERE" in dados:
            selecao = Operador("Seleção", f"σ {dados['WHERE']}", custo=self.estimar_custo(dados['WHERE']))
            selecao.filhos = [atual]
            atual = selecao
            self.nos.append(selecao)

        projecao = Operador("Projeção", f"π {', '.join(dados['SELECT'])}")
        projecao.filhos = [atual]
        atual = projecao
        self.nos.append(projecao)

        self.raiz = atual

    def estimar_custo(self, condicao):
        return condicao.count("AND") + condicao.count("OR") + 1

    def exibir_grafo(self):
        print("\nGrafo de Operadores:")
        self._exibir_recursivo(self.raiz, nivel=0)

    def _exibir_recursivo(self, operador, nivel):
        print("  " * nivel + str(operador))
        for filho in operador.filhos:
            self._exibir_recursivo(filho, nivel + 1)

    def gerar_plano_execucao(self):
        print("\nPlano de Execução (Ordem):")
        visitado = set()
        self._executar_em_ordem(self.raiz, visitado)

    def _executar_em_ordem(self, op, visitado):
        for filho in op.filhos:
            self._executar_em_ordem(filho, visitado)
        if op not in visitado:
            print(f"-> {op}")
            visitado.add(op)

# ================================================
#   EXEMPLO DE USO
# ================================================
# Este é um exemplo de como usar o parser dentro do sistema.

# 1. Obtenha a SQL da interface:
#    sql = campo_input_sql.text()

# 2. Use o parser:
sql = """
SELECT p.Nome, c.Descricao
FROM Produto p
JOIN Categoria c ON p.Categoria_idCategoria = c.idCategoria
WHERE p.Preco > 100 AND c.Descricao = 'Eletrônicos'
"""
parser = SQLParser(sql)
parser.parse()
parser.validate_fields()

# 3. Gere a álgebra relacional:
algebra = parser.gerar_algebra_relacional()
print("Álgebra Relacional:", algebra)

# 4. Se quiser mostrar as partes da consulta separadas:
#    print(parser.parsed)

# 5. Cria grafo de operadores e plano de execução:
grafo = GrafoDeOperadores(parser)
grafo.exibir_grafo()
grafo.gerar_plano_execucao()
