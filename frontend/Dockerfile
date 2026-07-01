FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm install

COPY . .

# Expose Vite's default port
EXPOSE 5173

# Run dev server accessible from outside container
CMD ["npm", "run", "dev", "--", "--host"]
