FROM node:24-alpine
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8100
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
EXPOSE 3001
CMD ["npm","run","dev"]
