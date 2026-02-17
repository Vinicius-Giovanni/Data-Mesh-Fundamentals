"""
Usando duckdb como engine para jogar os dados gerados do script generate_raw.py para o banco
S3 da AWS. O duckdb tem uma integração nativa com o S3, o que facilita a transferência de dados para a nuvem.
"""

import duckdb
import os
from dotenv import load_dotenv
from tqdm import tqdm
import glob
import time

start_time = time.time()

# Remover variáveis previameto carregadas (se houver)
os.environ.pop('AWS_ACCESS_KEY_ID', None)
os.environ.pop('AWS_SECRET_ACCESS_KEY', None)
os.environ.pop('AWS_BUCKET_NAME', None)
os.environ.pop('AWS_REGION', None)

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv(override=True)

# Obter as variáveis de ambiente para o S3
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
AWS_REGION = os.getenv('AWS_REGION')

# Conectar o Duckdb (em memória ou em arquivo se necessário)
con = duckdb.connect()

# Instalar e carregar a extensão httpfs para acesso ao S3
con.execute("INSTALL httpfs;")
con.execute("LOAD httpfs;")

# Configurar as credenciais do S3 para o Duckdb
con.execute(f"""
        set s3_region='{AWS_REGION}';
        set s3_access_key_id='{AWS_ACCESS_KEY_ID}';    
        set s3_secret_access_key='{AWS_SECRET_ACCESS_KEY}';        
""")

def load_parquet_to_s3(parquet_dir, s3_prefix):
    # Carregando arquivs Parquet e transferindo para o S3 via Engine Duckdb
    parquet_files = glob.glob(os.path.join(parquet_dir, '*.parquet'))

    # Mostrar a barra de progresso
    for parquet_file in tqdm(parquet_files, desc=f"Carregando {s3_prefix} para S3", unit="arquivo"):
        # Definir o caminho (key) no S3 onde o arquivo será salvo
        s3_path = f"s3://{AWS_BUCKET_NAME}/{s3_prefix}/{os.path.basename(parquet_file)}"

        # Carregar o arquivo parquet no duckdb e enviar diretamente para o S3
        con.execute(f"""
            COPY (SELECT * FROM read_parquet('{parquet_file}))
            TO '{s3_path}'
            (FORMAT 'parquet')
        """)

        print(f'Arquivo {parquet_file} carregado para {s3_path}')
    
    print(f"Todos os arquivos de {s3_prefix} foram carregados para o S3.")

# Caminho para as pastas de arquivos Parquet
parquet_dir_cadastros = r'./datasets/raw_data/cadastros'
parquet_dir_pedidos = r'./datasets/raw_data/pedidos'

# Carregar os arquivos de cadatros e pedidos para o S3
load_parquet_to_s3(parquet_dir_cadastros, 'datasets_duckdb/bronze/cadastros')
load_parquet_to_s3(parquet_dir_pedidos, 'datasets_duckdb/bronze/pedidos')

# Fechar a conexão com o Duckdb
con.close()

elapsed_time = time.time() - start_time
print(f'Tempo decorrido: {elapsed_time:.2f} segundos')

