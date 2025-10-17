# Dockerfile

# === 1. Builder Stage ===
# Use a slim image for better native dependency compatibility
FROM node:18-slim AS builder

WORKDIR /app

# Copy package.json and lock files
COPY package.json ./

# Install dependencies
RUN npm install

# Copy the rest of your application code
COPY . .

# Build the Next.js application
RUN npm run build


# === 2. Runner Stage ===
# Use the same slim image for the final container
FROM node:18-slim AS runner

WORKDIR /app

# Set the environment to production
ENV NODE_ENV=production

# Create a non-root user for security
RUN addgroup --system nextjs
RUN adduser --system --ingroup nextjs nextjs

# Copy the standalone output from the builder stage
COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./

# Copy public assets and static build assets
COPY --from=builder --chown=nextjs:nextjs /app/public ./public
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static

# Set the user
USER nextjs

# Expose the port Next.js runs on (default is 3000)
EXPOSE 3000

# The command to start the server
CMD ["node", "server.js"]