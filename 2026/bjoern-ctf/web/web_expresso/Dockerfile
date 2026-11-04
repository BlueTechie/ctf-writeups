FROM node:alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --omit=dev

COPY a.js ./

USER node
EXPOSE 3000

CMD ["node", "a.js"]
