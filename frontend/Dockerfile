FROM node:24-alpine AS builder

WORKDIR /app
# COPY package.json package-lock.json ./
COPY package.json ./
RUN npm install --frozen-lockfile

COPY . .
RUN npm run build

# ──────────────────────────────────────────────
# 2. Production stage
# ──────────────────────────────────────────────
FROM node:24-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["npm", "start"]