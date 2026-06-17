FROM node:20

WORKDIR /app

ARG VITE_API_URL=https://psychology-consultation-service-1.onrender.com/
ENV VITE_API_URL=$VITE_API_URL

COPY package*.json ./

RUN npm ci

COPY . .

RUN npm run build

EXPOSE 5173

CMD ["npm", "run", "preview"]
