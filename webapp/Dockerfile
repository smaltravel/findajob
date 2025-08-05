# Use Node.js 18 Alpine for smaller image size
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies for build)
RUN npm install

# Copy source code
COPY . .

# Build the Vue application
RUN npm run build

# Remove dev dependencies to reduce image size
RUN npm prune --production

# Expose ports
EXPOSE 3000
EXPOSE 8080

# Start the server
CMD ["npm", "start"] 