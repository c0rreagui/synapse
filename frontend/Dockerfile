# Use imagem leve do Node
FROM node:20-alpine

# Define diretório
WORKDIR /app

# Copia arquivos de dependência
COPY package.json package-lock.json* ./

# Instala dependências
RUN npm install --legacy-peer-deps

# Copia o código fonte
COPY . .

# Expõe a porta 3000
EXPOSE 3000

# Inicia em modo desenvolvimento
CMD ["npm", "run", "dev"]
