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
