FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
COPY backend/package.json backend/package.json
COPY frontend/package.json frontend/package.json
RUN npm install --include=dev
FROM deps AS build
COPY backend backend
RUN npm run build -w backend
FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json* ./
COPY backend/package.json backend/package.json
RUN npm install --omit=dev -w backend
COPY --from=build /app/backend/dist backend/dist
EXPOSE 4000
CMD ["npm", "run", "start", "-w", "backend"]
