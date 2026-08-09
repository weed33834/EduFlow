FROM node:20-alpine

RUN npm install -g pnpm

WORKDIR /app

# Copy monorepo config files
COPY package.json pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/
COPY packages/shared/package.json ./packages/shared/
COPY packages/ui/package.json ./packages/ui/

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Build the web app
RUN pnpm --filter @eduflow/web build

EXPOSE 3000
CMD ["pnpm", "--filter", "@eduflow/web", "start"]
