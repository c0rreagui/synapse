# Use imagem leve do Node
FROM node:20-alpine

# Define diretório
WORKDIR /app

# Copia arquivos de dependência
COPY package.json package-lock.json* ./

# Instala dependências
# Debug and Install
RUN echo "Running custom build with legacy-peer-deps"
RUN rm -f package-lock.json
RUN npm install --legacy-peer-deps

# Copia o código fonte
COPY . .

# Expõe a porta 3000
EXPOSE 3000

# Inicia em modo desenvolvimento
CMD ["npm", "run", "dev"]
